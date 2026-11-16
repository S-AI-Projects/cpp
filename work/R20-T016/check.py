#!/usr/bin/env python3
"""Run zebra-puzzle tests against the reference and a position-array alternative."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
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
EXERCISE_REL = Path("exercises/practice/zebra-puzzle")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
ALTERNATIVE_SOURCE = EVIDENCE / "alternative.cpp"
CASES = [
    {
        "name": "drinks_water",
        "id": "16efb4e4-8ad7-4d5e-ba96-e5537b66fd42",
        "field": "drinksWater",
    },
    {
        "name": "owns_zebra",
        "id": "084d5b8b-24e2-40e6-b008-c800da8cd257",
        "field": "ownsZebra",
    },
]


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


def parse_expected_cases(test_source: str, metadata: dict) -> list[dict]:
    result = []
    for case in CASES:
        match = re.search(
            rf'TEST_CASE\("{re.escape(case["name"])}",\s*"\[{re.escape(case["id"])}\]"\)\s*\{{(.*?)\n\}}',
            test_source,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError(f"Could not find canonical test {case['name']!r}")
        expected_match = re.search(rf'solution\.{case["field"]}\s*==\s*"([^"]+)"', match.group(1))
        if not expected_match:
            raise RuntimeError(f"Could not extract expected result for {case['name']!r}")
        entry = metadata.get(case["id"])
        if not entry or "description" not in entry:
            raise RuntimeError(f"Canonical metadata entry missing description for {case['id']}")
        result.append(
            {
                **case,
                "description": entry["description"],
                "expected": expected_match.group(1),
            }
        )
    return result


def build_variant(
    temporary_root: Path,
    config: dict,
    *,
    label: str,
    metadata_data: dict,
    alternative_source: str | None,
    source_test_count: int,
) -> dict:
    variant_dir = temporary_root / label
    variant_dir.mkdir()
    exercise_copy = variant_dir / EXERCISE_REL.name
    shutil.copytree(EXERCISE, exercise_copy)
    if (exercise_copy / ".meta/config.json").read_text() != json.dumps(config, indent=2) + "\n":
        # Formatting differences are harmless; semantic metadata equality is checked below.
        copied_config = json.loads((exercise_copy / ".meta/config.json").read_text())
        if copied_config != config:
            raise RuntimeError(f"{label} exercise copy has different configuration metadata")

    solution_files = config["files"]["solution"]
    example_files = config["files"]["example"]
    if len(solution_files) != len(example_files):
        raise RuntimeError("Solution and example file lists do not have matching lengths")
    for solution_rel, example_rel in zip(solution_files, example_files):
        destination = exercise_copy / solution_rel
        reference = exercise_copy / example_rel
        if not destination.is_file() or not reference.is_file():
            raise RuntimeError(f"Missing configured solution/reference pair: {solution_rel}, {example_rel}")
        shutil.copy2(reference, destination)
    if alternative_source is not None:
        (exercise_copy / solution_files[0]).write_text(alternative_source)

    copied_metadata = tomllib.loads((exercise_copy / ".meta/tests.toml").read_text())
    if copied_metadata != metadata_data:
        raise RuntimeError(f"{label} copy did not preserve all metadata values")

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
        raise RuntimeError(f"{label} run executed zero test cases")
    if tests["test_case_count"] != source_test_count:
        raise RuntimeError(f"{label} test count differs from the enabled C++ source")
    if test_run["returncode"] != 0 or tests["failed_case_count"] or tests["error_case_count"]:
        raise RuntimeError(f"{label} implementation failed one or more enabled tests")

    probe_source = variant_dir / "answer_probe.cpp"
    probe_source.write_text(
        '#include <iostream>\n'
        '#include "zebra_puzzle.h"\n'
        'int main() {\n'
        '    const auto answer = zebra_puzzle::solve();\n'
        '    std::cout << answer.drinksWater << "\\n" << answer.ownsZebra << "\\n";\n'
        '}\n'
    )
    probe_binary = variant_dir / "answer_probe"
    probe_build = run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            "-I",
            str(exercise_copy),
            str(exercise_copy / solution_files[0]),
            str(probe_source),
            "-o",
            str(probe_binary),
        ],
        variant_dir,
    )
    probe_run = run([str(probe_binary)], variant_dir)
    outputs = probe_run["stdout"].splitlines()
    return {
        "configure": configure,
        "build": build,
        "test_run": test_run,
        "test_summary": tests,
        "probe_build": probe_build,
        "probe_run": probe_run,
        "outputs": outputs,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if not ALTERNATIVE_SOURCE.is_file():
        raise RuntimeError(f"Independent alternative source is missing: {ALTERNATIVE_SOURCE}")
    config = json.loads(safe_exercise_path(".meta/config.json").read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    test_source = safe_exercise_path(config["files"]["test"][0]).read_text()
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    metadata = tomllib.loads(metadata_text)
    selected = parse_expected_cases(test_source, metadata)
    source_test_count = len(re.findall(r"^\s*TEST_CASE\(", test_source, re.MULTILINE))
    if len(metadata) != source_test_count:
        raise RuntimeError("Metadata entry count does not match enabled C++ test case count")

    merge_base = run(["git", "merge-base", "HEAD", "upstream/main"], ROOT)["stdout"].strip()
    base_metadata = run(["git", "show", f"{merge_base}:{EXERCISE_REL}/.meta/tests.toml"], ROOT)["stdout"]
    base_config = json.loads(run(["git", "show", f"{merge_base}:{EXERCISE_REL}/.meta/config.json"], ROOT)["stdout"])
    if tomllib.loads(base_metadata) != metadata or base_config != config:
        raise RuntimeError("Exercise metadata/configuration changed from the branch base")

    report = {
        "task_id": "R20-T016",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/20",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exercise": str(EXERCISE_REL),
        "base_commit": merge_base,
        "representation": "Each category maps its values to house indices 0 through 4; each array is a permutation.",
        "selected_cases": selected,
        "test_case_count_expected": source_test_count,
        "metadata_entries": len(metadata),
        "metadata_contract_preserved_from_base": True,
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before": learner_hashes_before,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t016-") as temporary:
        temporary_root = Path(temporary)
        reference = build_variant(
            temporary_root,
            config,
            label="reference",
            metadata_data=metadata,
            alternative_source=None,
            source_test_count=source_test_count,
        )
        alternative = build_variant(
            temporary_root,
            config,
            label="alternative",
            metadata_data=metadata,
            alternative_source=ALTERNATIVE_SOURCE.read_text(),
            source_test_count=source_test_count,
        )

    expected_outputs = [case["expected"] for case in selected]
    if reference["outputs"] != expected_outputs:
        raise RuntimeError(f"Reference answers {reference['outputs']!r}, expected {expected_outputs!r}")
    if alternative["outputs"] != expected_outputs:
        raise RuntimeError(f"Alternative answers {alternative['outputs']!r}, expected {expected_outputs!r}")
    if reference["test_summary"]["case_names"] != alternative["test_summary"]["case_names"]:
        raise RuntimeError("Reference and alternative executed different enabled test cases")

    report["reference"] = reference
    report["alternative"] = alternative
    report["both_test_lists_match"] = (
        reference["test_summary"]["case_names"] == alternative["test_summary"]["case_names"]
    )
    report["reference_alternative_outputs_match"] = reference["outputs"] == alternative["outputs"]
    report["alternative_source_sha256"] = sha256(ALTERNATIVE_SOURCE)
    report["learner_solution_sha256_after"] = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    report["learner_files_unchanged"] = (
        report["learner_solution_sha256_before"] == report["learner_solution_sha256_after"]
    )
    if not report["learner_files_unchanged"]:
        raise RuntimeError("Learner solution files changed during isolated validation")

    case_evidence = []
    for index, case in enumerate(selected):
        case_evidence.append(
            {
                **case,
                "reference_actual": reference["outputs"][index],
                "alternative_actual": alternative["outputs"][index],
            }
        )
    (EVIDENCE / "cases.json").write_text(json.dumps(case_evidence, indent=2) + "\n")
    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Reference: {reference['test_summary']['test_case_count']} enabled cases passed")
    print(f"Alternative: {alternative['test_summary']['test_case_count']} enabled cases passed")
    print(f"Answers: {reference['outputs']} (identical for alternative)")
    print("Metadata and learner stub preserved")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
