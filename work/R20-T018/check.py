#!/usr/bin/env python3
"""Check binary-search path metadata, invalid fixtures, and reference behavior."""

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
EXERCISE_REL = Path("exercises/practice/binary-search")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
CHECKER = ROOT / "tools/course_checks/r20-t018.py"
SELECTED_CASES = [
    {
        "name": "finds_a_value_in_an_array_with_one_element",
        "id": "b55c24a9-a98d-4379-a08c-2adcf8ebeee8",
        "data": [6],
        "value": 6,
        "expected": 0,
    },
    {
        "name": "finds_a_value_in_the_middle_of_an_array",
        "id": "73469346-b0a0-4011-89bf-989e443d503d",
        "data": [1, 3, 4, 6, 8, 9, 11],
        "value": 6,
        "expected": 3,
    },
    {
        "name": "finds_a_value_at_the_beginning_of_an_array",
        "id": "327bc482-ab85-424e-a724-fb4658e66ddb",
        "data": [1, 3, 4, 6, 8, 9, 11],
        "value": 1,
        "expected": 0,
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


def write_fixture(root: Path, files: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for relative in (
        "solution.cpp",
        "solution.h",
        "tests/test.cpp",
        ".meta/example.cpp",
        ".meta/example.h",
        "editor.json",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n")
    config_path = root / ".meta/config.json"
    config_path.write_text(json.dumps({"files": files}, indent=2) + "\n")
    return config_path


def run_fixture(checker: Path, root: Path, config: Path, cwd: Path) -> dict:
    result = run(
        ["python3", str(checker), "--exercise-dir", str(root), "--config", str(config)],
        cwd,
        expected=None,
    )
    try:
        result["json"] = json.loads(result["stdout"])
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Path checker did not return JSON: {result['stdout']}") from error
    return result


def compile_probe(exercise_copy: Path, temporary_root: Path) -> dict:
    source = temporary_root / "binary_search_probe.cpp"
    source.write_text(
        '#include <iostream>\n'
        '#include <vector>\n'
        '#include "binary_search.h"\n'
        'int main() {\n'
        '    std::cout << binary_search::find(std::vector<int>{6}, 6) << "\\n";\n'
        '    std::cout << binary_search::find(std::vector<int>{1, 3, 4, 6, 8, 9, 11}, 6) << "\\n";\n'
        '    std::cout << binary_search::find(std::vector<int>{1, 3, 4, 6, 8, 9, 11}, 1) << "\\n";\n'
        '}\n'
    )
    binary = temporary_root / "binary_search_probe"
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
            str(exercise_copy / "binary_search.cpp"),
            str(source),
            "-o",
            str(binary),
        ],
        temporary_root,
    )
    execution = run([str(binary)], temporary_root)
    actual = [int(value) for value in execution["stdout"].splitlines()]
    expected = [case["expected"] for case in SELECTED_CASES]
    if actual != expected:
        raise RuntimeError(f"Named case outputs {actual!r} do not match expected {expected!r}")
    return {"build": build, "execution": execution, "actual": actual, "expected": expected}


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    config_path = safe_exercise_path(".meta/config.json")
    config = json.loads(config_path.read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    test_source = safe_exercise_path(config["files"]["test"][0]).read_text()
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    metadata_count = len(re.findall(r"^\[[0-9a-f-]{36}\]$", metadata_text, re.MULTILINE))
    source_test_count = len(re.findall(r"^\s*TEST_CASE\(", test_source, re.MULTILINE))
    for case in SELECTED_CASES:
        if case["id"] not in metadata_text or case["name"] not in test_source:
            raise RuntimeError(f"Named canonical test is not present: {case['name']}")

    real_config_check = run_fixture(CHECKER, EXERCISE, config_path, ROOT)
    if real_config_check["returncode"] != 0 or not real_config_check["json"].get("valid"):
        raise RuntimeError(f"Real config did not pass path checker: {real_config_check['stdout']}")

    fixture_results: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="r20-t018-fixtures-") as fixture_tmp:
        fixture_root = Path(fixture_tmp)
        valid_roles = {
            "solution": ["solution.cpp", "solution.h"],
            "test": ["tests/test.cpp"],
            "example": [".meta/example.cpp", ".meta/example.h"],
            "editor": ["editor.json"],
        }
        valid_root = fixture_root / "valid"
        valid_config = write_fixture(valid_root, valid_roles)
        valid_result = run_fixture(CHECKER, valid_root, valid_config, ROOT)
        if valid_result["returncode"] != 0 or not valid_result["json"].get("valid"):
            raise RuntimeError("Fixture baseline with all file roles did not validate")

        invalids = [
            (
                "missing_reference",
                {
                    **valid_roles,
                    "example": [".meta/missing_reference.cpp", ".meta/example.h"],
                },
                "example",
                "configured file does not exist",
            ),
            (
                "missing_test",
                {**valid_roles, "test": ["tests/missing_test.cpp"]},
                "test",
                "configured file does not exist",
            ),
            (
                "outside_exercise",
                {**valid_roles, "solution": ["../outside.cpp"]},
                "solution",
                "parent traversal or absolute path is not allowed",
            ),
        ]
        outside_file = fixture_root / "outside.cpp"
        outside_file.write_text("present but outside the exercise\n")
        for name, roles, expected_role, expected_reason in invalids:
            fixture_dir = fixture_root / name
            fixture_config = write_fixture(fixture_dir, roles)
            result = run_fixture(CHECKER, fixture_dir, fixture_config, ROOT)
            errors = result["json"].get("errors", [])
            if result["returncode"] == 0 or result["json"].get("valid"):
                raise RuntimeError(f"Invalid fixture unexpectedly passed: {name}")
            if not any(error["role"] == expected_role and error["reason"] == expected_reason for error in errors):
                raise RuntimeError(f"Fixture {name} failed for the wrong reason: {errors}")
            fixture_results[name] = {"returncode": result["returncode"], "errors": errors}

    with tempfile.TemporaryDirectory(prefix="r20-t018-") as temporary:
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
            raise RuntimeError("Binary-search reference run executed zero test cases")
        if tests["test_case_count"] != source_test_count or tests["test_case_count"] != metadata_count:
            raise RuntimeError("Executed tests, source cases, and metadata entries do not match")
        if test_run["returncode"] != 0 or tests["failed_case_count"] or tests["error_case_count"]:
            raise RuntimeError("Binary-search reference failed one or more enabled tests")
        for case in SELECTED_CASES:
            if case["name"] not in tests["case_names"]:
                raise RuntimeError(f"Named test did not execute: {case['name']}")
        probe = compile_probe(exercise_copy, temporary_root)

    learner_hashes_after = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    if learner_hashes_before != learner_hashes_after:
        raise RuntimeError("Learner solution files changed during isolated validation")

    report = {
        "task_id": "R20-T018",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/22",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exercise": str(EXERCISE_REL),
        "real_path_check": real_config_check["json"],
        "invalid_fixture_results": fixture_results,
        "selected_cases": SELECTED_CASES,
        "case_counts": {
            "metadata_entries": metadata_count,
            "C++_source_cases": source_test_count,
            "executed_cases": tests["test_case_count"],
        },
        "configure": configure,
        "build": build,
        "test_run": test_run,
        "test_summary": tests,
        "selected_output_probe": probe,
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before": learner_hashes_before,
        "learner_solution_sha256_after": learner_hashes_after,
        "learner_files_unchanged": True,
    }
    case_evidence = []
    for index, case in enumerate(SELECTED_CASES):
        case_evidence.append({**case, "actual": probe["actual"][index]})
    (EVIDENCE / "cases.json").write_text(json.dumps(case_evidence, indent=2) + "\n")
    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Real file map: valid; {len(config['files'])} roles checked")
    print("Invalid fixtures rejected for missing reference, missing test, and parent traversal")
    print(f"Reference: {tests['test_case_count']} enabled cases passed; named indices {probe['actual']}")
    print("Learner solution files unchanged")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
