#!/usr/bin/env python3
"""Verify the run-length-encoding reference and its single-count mutant."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def find_repository_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / ".git").exists():
            return candidate
        nested_clone = candidate / "work" / "cpp"
        if (nested_clone / ".git").exists():
            return nested_clone
    raise RuntimeError("Could not locate the cpp repository checkout")


ROOT = find_repository_root()
EXERCISE_REL = Path("exercises/practice/run-length-encoding")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
TARGET_CASE = "encode single characters only are encoded without count"
TARGET_ID = "52012823-b7e6-4277-893c-5b96d42f82de"
MUTATION_FROM = "counter > 1"
MUTATION_TO = "counter >= 1"
PROBE_CASES = [
    {"name": "encode empty string", "input": "", "expected": "", "mutant_actual": ""},
    {"name": TARGET_CASE, "id": TARGET_ID, "input": "XYZ", "expected": "XYZ", "mutant_actual": "1X1Y1Z"},
    {
        "name": "encode string with no single characters",
        "input": "AABBBCCCC",
        "expected": "2A3B4C",
        "mutant_actual": "2A3B4C",
    },
    {
        "name": "shortest non-empty distinguishing input",
        "input": "A",
        "expected": "A",
        "mutant_actual": "1A",
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, *, expected: int | None = 0) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    result = {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
    }
    if expected is not None and completed.returncode != expected:
        raise RuntimeError(
            f"Command returned {completed.returncode}, expected {expected}: "
            f"{' '.join(command)}\n{completed.stdout}"
        )
    return result


def parse_junit(result: dict) -> dict:
    try:
        root = ET.fromstring(result["stdout"])
    except ET.ParseError as exc:
        raise RuntimeError(f"Could not parse Catch2 JUnit output: {exc}\n{result['stdout']}")
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    cases = [case for suite in suites for case in suite.findall("testcase")]
    failures = [failure for case in cases for failure in case.findall("failure")]
    errors = [error for case in cases for error in case.findall("error")]
    return {
        "test_case_count": len(cases),
        "failed_case_count": len(failures),
        "error_case_count": len(errors),
        "case_names": [case.attrib.get("name", "") for case in cases],
        "failure_messages": [failure.attrib.get("message", "") for failure in failures],
    }


def safe_exercise_path(relative: str) -> Path:
    candidate = (EXERCISE / relative).resolve()
    if not candidate.is_relative_to(EXERCISE.resolve()):
        raise RuntimeError(f"Metadata path escapes exercise directory: {relative}")
    return candidate


def configure_copy(variant_dir: Path, config: dict, *, mutant: bool) -> tuple[Path, dict]:
    exercise_copy = variant_dir / EXERCISE_REL.name
    shutil.copytree(EXERCISE, exercise_copy)

    solution_files = config["files"]["solution"]
    example_files = config["files"]["example"]
    if len(solution_files) != len(example_files):
        raise RuntimeError("Solution and example file lists do not have matching lengths")

    # The learner files are replaced only in this temporary copy, using config.json's mapping.
    for solution_rel, example_rel in zip(solution_files, example_files, strict=True):
        solution = exercise_copy / solution_rel
        example = exercise_copy / example_rel
        if not solution.is_file() or not example.is_file():
            raise RuntimeError(f"Missing configured solution/reference pair: {solution_rel}, {example_rel}")
        shutil.copy2(example, solution)

    solution_cpp = exercise_copy / solution_files[0]
    if mutant:
        original = solution_cpp.read_text()
        occurrences = original.count(MUTATION_FROM)
        if occurrences != 2:
            raise RuntimeError(f"Expected two count conditions to mutate, found {occurrences}")
        solution_cpp.write_text(original.replace(MUTATION_FROM, MUTATION_TO))

    return exercise_copy, {"solution_cpp": str(solution_cpp), "mutant": mutant}


def compile_probe(exercise_copy: Path, variant_dir: Path) -> Path:
    probe_source = variant_dir / "encode_probe.cpp"
    probe_source.write_text(
        '#include <iostream>\n'
        '#include "run_length_encoding.h"\n'
        'int main(int argc, char** argv) {\n'
        '    if (argc != 2) return 2;\n'
        '    std::cout << run_length_encoding::encode(argv[1]);\n'
        '}\n'
    )
    probe_binary = variant_dir / "encode_probe"
    compile_result = run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(exercise_copy),
            str(exercise_copy / "run_length_encoding.cpp"),
            str(probe_source),
            "-o",
            str(probe_binary),
        ],
        variant_dir,
    )
    RESULTS["probe_compiles"].append(compile_result)
    return probe_binary


def run_probe(binary: Path, cwd: Path, input_text: str, expected_output: str) -> dict:
    result = run([str(binary), input_text], cwd)
    actual = result["stdout"]
    if actual != expected_output:
        raise RuntimeError(f"Probe {input_text!r}: expected {expected_output!r}, got {actual!r}")
    return {"input": input_text, "expected": expected_output, "actual": actual, "returncode": result["returncode"]}


def run_variant(temp_root: Path, config: dict, *, mutant: bool) -> dict:
    label = "mutant" if mutant else "original"
    variant_dir = temp_root / label
    variant_dir.mkdir()
    exercise_copy, replacement = configure_copy(variant_dir, config, mutant=mutant)
    build_dir = exercise_copy / "build"
    configure = run(
        ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"],
        exercise_copy,
    )
    RESULTS["variants"][label] = {
        "reference_replacement": replacement,
        "configure": configure,
    }

    # The exercise's ALL target runs the complete suite during the build. The original
    # must therefore build cleanly; the mutant build is expected to return non-zero because
    # the ALL target executes the suite and encounters the deliberate assertion failures.
    executable_name = EXERCISE_REL.name
    build = run(
        ["cmake", "--build", "build"],
        exercise_copy,
        expected=None if mutant else 0,
    )
    RESULTS["variants"][label]["build"] = build

    if mutant and (build["returncode"] == 0 or TARGET_CASE not in build["stdout"] or "failed" not in build["stdout"].lower()):
        raise RuntimeError("Mutant's default build did not report the expected test assertion failure")

    executable = build_dir / executable_name
    if not executable.is_file():
        raise RuntimeError(f"CMake did not produce expected test executable: {executable}")

    all_tests_result = run(
        [str(executable), "--reporter", "junit"],
        exercise_copy,
        expected=None if mutant else 0,
    )
    all_tests = parse_junit(all_tests_result)
    RESULTS["variants"][label]["all_tests"] = {
        "process": all_tests_result,
        **all_tests,
    }
    if all_tests["test_case_count"] <= 0:
        raise RuntimeError(f"{label} run executed zero test cases")

    target_result = run(
        [str(executable), "--reporter", "junit", TARGET_CASE],
        exercise_copy,
        expected=None,
    )
    target_tests = parse_junit(target_result)
    RESULTS["variants"][label]["target_case"] = {
        "process": target_result,
        **target_tests,
    }
    if target_tests["test_case_count"] != 1 or TARGET_CASE not in target_tests["case_names"]:
        raise RuntimeError(f"Named case filter did not run exactly {TARGET_CASE!r}")

    probe_binary = compile_probe(exercise_copy, variant_dir)
    probes = []
    for case in PROBE_CASES:
        probe_expected = case["mutant_actual"] if mutant else case["expected"]
        probes.append(run_probe(probe_binary, variant_dir, case["input"], probe_expected))
    RESULTS["variants"][label]["probes"] = probes

    if not mutant:
        if all_tests_result["returncode"] != 0 or all_tests["failed_case_count"] or all_tests["error_case_count"]:
            raise RuntimeError("Original reference did not pass all enabled test cases")
        if target_result["returncode"] != 0 or target_tests["failed_case_count"]:
            raise RuntimeError("Original reference failed the named single-character case")
        if target_tests["test_case_count"] != 1:
            raise RuntimeError("Original named-case run count was not one")
    else:
        failures = target_tests["failed_case_count"] + target_tests["error_case_count"]
        if target_result["returncode"] == 0 or failures == 0:
            raise RuntimeError("Mutant did not fail the named assertion as required")
        if all_tests_result["returncode"] == 0 or all_tests["failed_case_count"] + all_tests["error_case_count"] == 0:
            raise RuntimeError("Mutant unexpectedly passed the complete enabled suite")

    return RESULTS["variants"][label]


def tool_version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.stdout.splitlines()[0] if result.stdout else f"exit {result.returncode}"


RESULTS: dict = {"variants": {}, "probe_compiles": []}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    config_path = safe_exercise_path(".meta/config.json")
    config = json.loads(config_path.read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    test_source = safe_exercise_path(config["files"]["test"][0]).read_text()
    if TARGET_ID not in metadata_text or f'TEST_CASE("{TARGET_CASE}"' not in test_source:
        raise RuntimeError(f"Expected test metadata entry not found for {TARGET_ID}")

    RESULTS.update(
        {
            "task_id": "R20-T013",
            "issue": "https://github.com/S-AI-Projects/cpp/issues/17",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "exercise": str(EXERCISE_REL),
            "target_case": {"id": TARGET_ID, "name": TARGET_CASE},
            "mutation": {"from": MUTATION_FROM, "to": MUTATION_TO},
            "selected_inputs_and_expected_results": PROBE_CASES,
            "learner_solution_sha256_before": learner_hashes_before,
            "tool_versions": {
                "python": tool_version(["python3", "--version"]),
                "cmake": tool_version(["cmake", "--version"]),
                "cxx": tool_version(["c++", "--version"]),
            },
            "variants": {},
        }
    )

    with tempfile.TemporaryDirectory(prefix="r20-t013-") as temporary:
        temp_root = Path(temporary)
        run_variant(temp_root, config, mutant=False)
        run_variant(temp_root, config, mutant=True)

    learner_hashes_after = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    RESULTS["learner_solution_sha256_after"] = learner_hashes_after
    RESULTS["learner_files_unchanged"] = learner_hashes_before == learner_hashes_after
    if not RESULTS["learner_files_unchanged"]:
        raise RuntimeError("Learner solution files changed during the isolated check")

    RESULT_PATH = EVIDENCE / "report.json"
    CASE_PATH = EVIDENCE / "cases.json"
    case_evidence = []
    for index, case in enumerate(RESULTS["selected_inputs_and_expected_results"]):
        case_evidence.append(
            {
                **case,
                "original_actual": RESULTS["variants"]["original"]["probes"][index]["actual"],
                "mutant_actual": RESULTS["variants"]["mutant"]["probes"][index]["actual"],
            }
        )
    RESULTS["case_evidence"] = case_evidence
    RESULT_PATH.write_text(json.dumps(RESULTS, indent=2) + "\n")
    CASE_PATH.write_text(json.dumps(case_evidence, indent=2) + "\n")
    print(f"Reference: {RESULTS['variants']['original']['all_tests']['test_case_count']} test cases passed")
    print(f"Mutant: {RESULTS['variants']['mutant']['all_tests']['test_case_count']} cases run; "
          f"{RESULTS['variants']['mutant']['all_tests']['failed_case_count']} failed")
    print(f"Named case: {TARGET_CASE}; ID {TARGET_ID}; mutant rejected")
    print("Minimal distinguishing input: 'A' -> expected 'A', mutant '1A'")
    print("Learner solution files unchanged")
    print(f"Evidence: {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
