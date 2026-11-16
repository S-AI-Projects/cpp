#!/usr/bin/env python3
"""Run food-chain reference tests and count fixed-domain song_verse work."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def find_repository_root() -> Path:
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / ".git").exists():
            return candidate
        nested_clone = candidate / "work" / "cpp"
        if (nested_clone / ".git").exists():
            return nested_clone
    raise RuntimeError("Could not locate the cpp repository checkout")


ROOT = find_repository_root()
EXERCISE_REL = Path("exercises/practice/food-chain")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
SELECTED_NAMES = ("fly", "spider", "bird")
TABLE_SIZE = 8


def safe_exercise_path(relative: str) -> Path:
    candidate = (EXERCISE / relative).resolve()
    if not candidate.is_relative_to(EXERCISE.resolve()):
        raise RuntimeError(f"Metadata path escapes exercise directory: {relative}")
    return candidate


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool_version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.stdout.splitlines()[0] if result.stdout else f"exit {result.returncode}"


def parse_junit(output: str) -> dict:
    root = ET.fromstring(output)
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    cases = [case for suite in suites for case in suite.findall("testcase")]
    failures = [node for case in cases for node in case.findall("failure")]
    errors = [node for case in cases for node in case.findall("error")]
    return {
        "test_case_count": len(cases),
        "failed_case_count": len(failures),
        "error_case_count": len(errors),
        "case_names": [case.attrib.get("name", "") for case in cases],
        "failures": [node.attrib.get("message", "") for node in failures + errors],
    }


def extract_expected_case(test_source: str, name: str) -> dict:
    match = re.search(rf'TEST_CASE\("{re.escape(name)}"\)\s*\{{', test_source)
    if not match:
        raise RuntimeError(f"Could not find canonical test case {name!r}")
    remainder = test_source[match.end():]
    next_case = re.search(r"^\s*TEST_CASE\(", remainder, re.MULTILINE)
    body = remainder[: next_case.start()] if next_case else remainder
    literals = re.findall(r'"(?:\\.|[^"\\])*"', body)
    expected = "".join(ast.literal_eval(literal) for literal in literals)
    verse_number = re.search(r"food_chain::verse\((\d+)\)", body)
    if not verse_number:
        raise RuntimeError(f"Could not find verse input in canonical case {name!r}")
    return {"name": name, "verse_number": int(verse_number.group(1)), "expected": expected}


def instrument_reference(source: str) -> str:
    replacements = [
        (
            "namespace {\n",
            "namespace {\n\nunsigned metric_sing_calls = 0;\n"
            "unsigned metric_verse_calls = 0;\n"
            "unsigned metric_appends = 0;\n"
            "unsigned metric_loop_checks = 0;\n",
        ),
        (
            "    string sing() const {\n",
            "    string sing() const {\n        ++metric_sing_calls;\n",
        ),
        (
            "    string verse() const { return verse_; }",
            "    string verse() const {\n        ++metric_verse_calls;\n        return verse_;\n    }",
        ),
        (
            "const unsigned num_verses = sizeof(song_verses) / sizeof(song_verses[0]);\n\n}  // namespace\n\nstring verse(unsigned num) {",
            "const unsigned num_verses = sizeof(song_verses) / sizeof(song_verses[0]);\n\n"
            "}  // namespace\n\n"
            "void reset_song_verse_metrics() {\n"
            "    metric_sing_calls = metric_verse_calls = metric_appends = metric_loop_checks = 0;\n"
            "}\n"
            "unsigned song_verse_sing_calls() { return metric_sing_calls; }\n"
            "unsigned song_verse_verse_calls() { return metric_verse_calls; }\n"
            "unsigned song_verse_appends() { return metric_appends; }\n"
            "unsigned song_verse_loop_checks() { return metric_loop_checks; }\n\n"
            "string verse(unsigned num) {",
        ),
        (
            "            while (num--) {\n                text += song_verses[num].verse();",
            "            while ((++metric_loop_checks, num--)) {\n"
            "                text += song_verses[num].verse();\n"
            "                ++metric_appends;",
        ),
    ]
    for old, new in replacements:
        count = source.count(old)
        if count != 1:
            raise RuntimeError(f"Expected one instrumentation target, found {count}: {old[:60]!r}")
        source = source.replace(old, new)
    return source


def compile_and_measure(
    temporary_root: Path,
    exercise_copy: Path,
    reference_source: str,
    selected: list[dict],
) -> dict:
    instrumented_source = temporary_root / "instrumented_food_chain.cpp"
    instrumented_source.write_text(instrument_reference(reference_source))
    harness = temporary_root / "operation_probe.cpp"
    harness.write_text(
        '#include <iostream>\n'
        '#include <string>\n'
        '#include "food_chain.h"\n'
        'namespace food_chain {\n'
        'void reset_song_verse_metrics();\n'
        'unsigned song_verse_sing_calls();\n'
        'unsigned song_verse_verse_calls();\n'
        'unsigned song_verse_appends();\n'
        'unsigned song_verse_loop_checks();\n'
        '}\n'
        'int main() {\n'
        '    for (unsigned n = 1; n <= 8; ++n) {\n'
        '        food_chain::reset_song_verse_metrics();\n'
        '        const std::string output = food_chain::verse(n);\n'
        '        std::cout << "METRIC " << n << " "\n'
        '                  << food_chain::song_verse_sing_calls() << " "\n'
        '                  << food_chain::song_verse_verse_calls() << " "\n'
        '                  << food_chain::song_verse_appends() << " "\n'
        '                  << food_chain::song_verse_loop_checks() << " "\n'
        '                  << output.size() << "\\n";\n'
        '        if (n <= 3) {\n'
        '            std::cout << "OUTPUT_" << n << "_BEGIN\\n" << output\n'
        '                      << "OUTPUT_" << n << "_END\\n";\n'
        '        }\n'
        '    }\n'
        '}\n'
    )
    binary = temporary_root / "operation_probe"
    build = run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(exercise_copy),
            str(instrumented_source),
            str(harness),
            "-o",
            str(binary),
        ],
        temporary_root,
    )
    execution = run([str(binary)], temporary_root)

    metrics = []
    for line in execution["stdout"].splitlines():
        if line.startswith("METRIC "):
            _, verse_number, sing_calls, verse_calls, appends, loop_checks, output_chars = line.split()
            metrics.append(
                {
                    "verse_number": int(verse_number),
                    "song_verse_sing_calls": int(sing_calls),
                    "song_verse_verse_calls": int(verse_calls),
                    "prior_fragment_appends": int(appends),
                    "loop_condition_checks": int(loop_checks),
                    "verse_output_characters": int(output_chars),
                }
            )
    if [item["verse_number"] for item in metrics] != list(range(1, TABLE_SIZE + 1)):
        raise RuntimeError("Operation probe did not measure every valid verse number")

    actual_outputs = {}
    for case in selected:
        marker = f"OUTPUT_{case['verse_number']}_BEGIN\n"
        end_marker = f"OUTPUT_{case['verse_number']}_END\n"
        start = execution["stdout"].find(marker)
        end = execution["stdout"].find(end_marker, start + len(marker))
        if start < 0 or end < 0:
            raise RuntimeError(f"Missing direct output for {case['name']}")
        actual_outputs[case["name"]] = execution["stdout"][start + len(marker):end]
        if actual_outputs[case["name"]] != case["expected"]:
            raise RuntimeError(
                f"{case['name']} output differs from canonical expected text: "
                f"{actual_outputs[case['name']]!r} != {case['expected']!r}"
            )

    return {"build": build, "execution": execution, "metrics": metrics, "selected_outputs": actual_outputs}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    config = json.loads(safe_exercise_path(".meta/config.json").read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    test_source_path = safe_exercise_path(config["files"]["test"][0])
    test_source = test_source_path.read_text()
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    selected = [extract_expected_case(test_source, name) for name in SELECTED_NAMES]
    source_test_count = len(re.findall(r"^\s*TEST_CASE\(", test_source, re.MULTILINE))
    metadata_count = len(re.findall(r"^\[[0-9a-f-]{36}\]$", metadata_text, re.MULTILINE))

    report = {
        "task_id": "R20-T015",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/19",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exercise": str(EXERCISE_REL),
        "fixed_domain": {"first_verse": 1, "last_verse": TABLE_SIZE},
        "selected_cases": selected,
        "case_counts": {"metadata_entries": metadata_count, "C++_source_cases": source_test_count},
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before": learner_hashes_before,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t015-") as temporary:
        temporary_root = Path(temporary)
        exercise_copy = temporary_root / EXERCISE_REL.name
        shutil.copytree(EXERCISE, exercise_copy)

        solution_files = config["files"]["solution"]
        example_files = config["files"]["example"]
        if len(solution_files) != len(example_files):
            raise RuntimeError("Solution and example file lists do not have matching lengths")
        for solution_rel, example_rel in zip(solution_files, example_files):
            solution = exercise_copy / solution_rel
            example = exercise_copy / example_rel
            if not solution.is_file() or not example.is_file():
                raise RuntimeError(f"Missing configured solution/reference pair: {solution_rel}, {example_rel}")
            shutil.copy2(example, solution)

        configure = run(
            ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"],
            exercise_copy,
        )
        build = run(["cmake", "--build", "build"], exercise_copy)
        executable = exercise_copy / "build" / EXERCISE_REL.name
        if not executable.is_file():
            raise RuntimeError(f"CMake did not produce the expected test executable: {executable}")
        test_run = run([str(executable), "--reporter", "junit"], exercise_copy)
        tests = parse_junit(test_run["stdout"])
        if tests["test_case_count"] <= 0:
            raise RuntimeError("Reference test run executed zero test cases")
        if tests["test_case_count"] != source_test_count or tests["test_case_count"] != metadata_count:
            raise RuntimeError("Executed cases, C++ source cases, and metadata entries do not match")
        if test_run["returncode"] != 0 or tests["failed_case_count"] or tests["error_case_count"]:
            raise RuntimeError("Reference failed one or more enabled tests")

        operation_probe = compile_and_measure(
            temporary_root,
            exercise_copy,
            safe_exercise_path(".meta/example.cpp").read_text(),
            selected,
        )

    metrics = operation_probe["metrics"]
    for item in metrics:
        n = item["verse_number"]
        expected_prior_calls = n - 1 if n < TABLE_SIZE else 0
        expected_loop_checks = n if n < TABLE_SIZE else 0
        if (
            item["song_verse_sing_calls"] != 1
            or item["song_verse_verse_calls"] != expected_prior_calls
            or item["prior_fragment_appends"] != expected_prior_calls
            or item["loop_condition_checks"] != expected_loop_checks
        ):
            raise RuntimeError(f"Unexpected operation count for verse({n}): {item}")

    report["configure"] = configure
    report["build"] = build
    report["test_run"] = test_run
    report["test_summary"] = tests
    report["operation_probe"] = operation_probe
    report["timing_benchmark"] = "Not run: the exercise domain is fixed at verses 1 through 8."
    report["learner_solution_sha256_after"] = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    report["learner_files_unchanged"] = (
        report["learner_solution_sha256_before"] == report["learner_solution_sha256_after"]
    )
    if not report["learner_files_unchanged"]:
        raise RuntimeError("Learner solution files changed during isolated validation")

    case_evidence = []
    for case in selected:
        case_evidence.append(
            {
                **case,
                "actual": operation_probe["selected_outputs"][case["name"]],
            }
        )
    (EVIDENCE / "cases.json").write_text(json.dumps(case_evidence, indent=2) + "\n")
    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Reference tests: {tests['test_case_count']} passed")
    print(f"Selected lyric outputs match: {', '.join(SELECTED_NAMES)}")
    print("Instrumented operation counts captured for all 8 valid verse numbers; no timing benchmark run")
    print("Learner solution files unchanged")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
