#!/usr/bin/env python3
"""Verify Luhn reference tests and the C++ const-reference hint example."""

from __future__ import annotations

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
EXERCISE_REL = Path("exercises/practice/luhn")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
NAMED_CASES = [
    {
        "id": "792a7082-feb7-48c7-b88b-bbfec160865e",
        "name": "single digit strings can not be valid",
        "input": "1",
        "expected": False,
    },
    {
        "id": "698a7924-64d4-4d89-8daa-32e1aadc271e",
        "name": "a single zero is invalid",
        "input": "0",
        "expected": False,
    },
    {
        "id": "73c2f62b-9b10-4c9f-9a04-83cee7367965",
        "name": "a simple valid SIN that remains valid if reversed",
        "input": "059",
        "expected": True,
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


def compile_hint_example(hints: str, temporary_root: Path) -> dict:
    code_match = re.search(r"### C\+\+ micro-example.*?```cpp\n(.*?)\n```", hints, re.DOTALL)
    output_match = re.search(r"Output:\s*```text\n(.*?)\n```", hints, re.DOTALL)
    if not code_match or not output_match:
        raise RuntimeError("Could not find the fenced micro-example and its published output")
    source = code_match.group(1) + "\n"
    expected = output_match.group(1).splitlines()
    source_path = temporary_root / "hint_micro_example.cpp"
    binary_path = temporary_root / "hint_micro_example"
    source_path.write_text(source)
    build = run(
        [
            "c++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-Werror",
            str(source_path),
            "-o",
            str(binary_path),
        ],
        temporary_root,
    )
    execution = run([str(binary_path)], temporary_root)
    actual = execution["stdout"].splitlines()
    if actual != expected or len(actual) != 2:
        raise RuntimeError(f"Micro-example output {actual!r} does not match published output {expected!r}")
    return {
        "source": source,
        "build": build,
        "execution": execution,
        "expected_output_lines": expected,
        "actual_output_lines": actual,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    config = json.loads(safe_exercise_path(".meta/config.json").read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    test_source = safe_exercise_path(config["files"]["test"][0]).read_text()
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    metadata_ids = re.findall(r"^\[([0-9a-f-]{36})\]$", metadata_text, re.MULTILINE)
    source_test_count = len(re.findall(r"^\s*TEST_CASE\(", test_source, re.MULTILINE))
    for case in NAMED_CASES:
        if case["id"] not in metadata_ids or case["name"] not in test_source:
            raise RuntimeError(f"Named canonical case missing: {case['name']}")

    hints_path = safe_exercise_path(".docs/hints.md")
    hints = hints_path.read_text()
    if "std::string const& input_str" not in hints or "https://en.cppreference.com/w/cpp/language/reference" not in hints:
        raise RuntimeError("Hint must name the reference construct and link its language reference")

    report = {
        "task_id": "R20-T017",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/21",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exercise": str(EXERCISE_REL),
        "named_cases": NAMED_CASES,
        "metadata_entry_count": len(metadata_ids),
        "C++_source_case_count": source_test_count,
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before": learner_hashes_before,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t017-") as temporary:
        temporary_root = Path(temporary)
        exercise_copy = temporary_root / EXERCISE_REL.name
        shutil.copytree(EXERCISE, exercise_copy)
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
            raise RuntimeError("Luhn reference run executed zero test cases")
        if tests["test_case_count"] != source_test_count or tests["test_case_count"] != len(metadata_ids):
            raise RuntimeError("Executed tests, source tests, and metadata entries do not match")
        if test_run["returncode"] != 0 or tests["failed_case_count"] or tests["error_case_count"]:
            raise RuntimeError("Luhn reference failed one or more enabled tests")
        for case in NAMED_CASES:
            if not any(case["name"] in name for name in tests["case_names"]):
                raise RuntimeError(f"Named canonical test did not execute: {case['name']}")

        micro_example = compile_hint_example(hints, temporary_root)

    report["configure"] = configure
    report["build"] = build
    report["test_run"] = test_run
    report["test_summary"] = tests
    report["micro_example"] = micro_example
    report["learner_solution_sha256_after"] = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    report["learner_files_unchanged"] = (
        report["learner_solution_sha256_before"] == report["learner_solution_sha256_after"]
    )
    if not report["learner_files_unchanged"]:
        raise RuntimeError("Learner solution files changed during isolated validation")

    case_evidence = {
        "canonical_cases": NAMED_CASES,
        "reference_test_case_count": tests["test_case_count"],
        "micro_example": {
            "input": "0 59",
            "raw_character_count_expected": 4,
            "digit_count_expected": 3,
            "published_output_lines": micro_example["expected_output_lines"],
            "actual_output_lines": micro_example["actual_output_lines"],
        },
    }
    (EVIDENCE / "cases.json").write_text(json.dumps(case_evidence, indent=2) + "\n")
    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Reference: {tests['test_case_count']} enabled cases passed")
    print(f"Micro-example: expected {micro_example['expected_output_lines']}, got {micro_example['actual_output_lines']}")
    print("Learner solution files unchanged")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
