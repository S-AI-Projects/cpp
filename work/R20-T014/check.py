#!/usr/bin/env python3
"""Compare the affine-cipher reference before and after the gcd refactor."""

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
EXERCISE_REL = Path("exercises/practice/affine-cipher")
EXERCISE = ROOT / EXERCISE_REL
EVIDENCE = Path(__file__).resolve().parent
SELECTED_CASES = [
    {
        "name": "encode_yes",
        "id": "2ee1d9af-1c43-416c-b41b-cefd7d4d2b2a",
        "input": "yes",
        "a": 5,
        "b": 7,
        "expected": "xbt",
    },
    {
        "name": "encode_no",
        "id": "785bade9-e98b-4d4f-a5b0-087ba3d7de4b",
        "input": "no",
        "a": 15,
        "b": 18,
        "expected": "fu",
    },
    {
        "name": "encode_OMG",
        "id": "2854851c-48fb-40d8-9bf6-8f192ed25054",
        "input": "OMG",
        "a": 21,
        "b": 3,
        "expected": "lvz",
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


def tool_version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.stdout.splitlines()[0] if result.stdout else f"exit {result.returncode}"


def replace_solution_with_reference(
    exercise_copy: Path,
    config: dict,
    original_example: str,
    *,
    before: bool,
) -> None:
    solution_files = config["files"]["solution"]
    example_files = config["files"]["example"]
    if len(solution_files) != len(example_files):
        raise RuntimeError("Solution and example file lists do not have matching lengths")
    for solution_rel, example_rel in zip(solution_files, example_files):
        destination = exercise_copy / solution_rel
        if not destination.is_file():
            raise RuntimeError(f"Missing configured solution path: {solution_rel}")
        if before and example_rel == ".meta/example.cpp":
            destination.write_text(original_example)
        else:
            reference = exercise_copy / example_rel
            if not reference.is_file():
                raise RuntimeError(f"Missing configured reference path: {example_rel}")
            shutil.copy2(reference, destination)


def build_and_run_suite(
    temporary_root: Path,
    config: dict,
    *,
    label: str,
    original_example: str,
) -> dict:
    variant_dir = temporary_root / label
    variant_dir.mkdir()
    exercise_copy = variant_dir / EXERCISE_REL.name
    shutil.copytree(EXERCISE, exercise_copy)
    replace_solution_with_reference(
        exercise_copy,
        config,
        original_example,
        before=label == "before",
    )

    configure = run(
        ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"],
        exercise_copy,
    )
    build = run(["cmake", "--build", "build"], exercise_copy)
    executable = exercise_copy / "build" / EXERCISE_REL.name
    if not executable.is_file():
        raise RuntimeError(f"CMake did not produce the expected test executable: {executable}")
    test_run = run([str(executable), "--reporter", "junit"], exercise_copy)
    parsed = parse_junit(test_run["stdout"])
    if parsed["test_case_count"] <= 0:
        raise RuntimeError(f"{label} run executed zero test cases")
    if test_run["returncode"] != 0 or parsed["failed_case_count"] or parsed["error_case_count"]:
        raise RuntimeError(f"{label} reference failed the full enabled test suite")

    source = safe_exercise_path(config["files"]["test"][0]).read_text()
    for case in SELECTED_CASES:
        if case["id"] not in source or f'TEST_CASE("{case["name"]}"' not in source:
            raise RuntimeError(f"Named case not present in C++ test source: {case['name']}")

    probe_source = variant_dir / "affine_probe.cpp"
    probe_source.write_text(
        '#include <iostream>\n'
        '#include "affine_cipher.h"\n'
        'int main() {\n'
        '    std::cout << affine_cipher::encode("yes", 5, 7) << "\\n";\n'
        '    std::cout << affine_cipher::encode("no", 15, 18) << "\\n";\n'
        '    std::cout << affine_cipher::encode("OMG", 21, 3) << "\\n";\n'
        '}\n'
    )
    probe_binary = variant_dir / "affine_probe"
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
            str(exercise_copy / config["files"]["solution"][0]),
            str(probe_source),
            "-o",
            str(probe_binary),
        ],
        variant_dir,
    )
    probe_run = run([str(probe_binary)], variant_dir)
    outputs = probe_run["stdout"].splitlines()
    expected = [case["expected"] for case in SELECTED_CASES]
    if outputs != expected:
        raise RuntimeError(f"{label} selected outputs were {outputs!r}, expected {expected!r}")

    return {
        "configure": configure,
        "build": build,
        "test_run": test_run,
        "test_summary": parsed,
        "probe_build": probe_build,
        "probe_run": probe_run,
        "selected_outputs": outputs,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    config = json.loads(safe_exercise_path(".meta/config.json").read_text())
    learner_hashes_before = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    current_example_path = safe_exercise_path(".meta/example.cpp")
    current_example = current_example_path.read_text()
    merge_base = run(["git", "merge-base", "HEAD", "upstream/main"], ROOT)["stdout"].strip()
    original_result = subprocess.run(
        ["git", "show", f"{merge_base}:{EXERCISE_REL}/.meta/example.cpp"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if original_result.returncode != 0:
        raise RuntimeError(f"Could not read base reference source: {original_result.stderr}")
    original_example = original_result.stdout

    test_source = safe_exercise_path(config["files"]["test"][0]).read_text()
    metadata_text = safe_exercise_path(".meta/tests.toml").read_text()
    source_case_count = len(re.findall(r"^\s*TEST_CASE\(", test_source, re.MULTILINE))
    metadata_case_count = len(re.findall(r"^\[[0-9a-f-]{36}\]$", metadata_text, re.MULTILINE))

    report = {
        "task_id": "R20-T014",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/18",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "exercise": str(EXERCISE_REL),
        "base_commit": merge_base,
        "reference_sha256": {
            "before": hashlib.sha256(original_example.encode()).hexdigest(),
            "after": sha256(current_example_path),
        },
        "selected_cases": SELECTED_CASES,
        "case_counts": {
            "metadata_entries": metadata_case_count,
            "C++_source_cases": source_case_count,
        },
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before": learner_hashes_before,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t014-") as temporary:
        temporary_root = Path(temporary)
        before = build_and_run_suite(
            temporary_root,
            config,
            label="before",
            original_example=original_example,
        )
        after = build_and_run_suite(
            temporary_root,
            config,
            label="after",
            original_example=original_example,
        )

    before_summary = before["test_summary"]
    after_summary = after["test_summary"]
    if before_summary["test_case_count"] != source_case_count or after_summary["test_case_count"] != source_case_count:
        raise RuntimeError("Executed test count does not match the enabled C++ test source")
    if metadata_case_count != source_case_count:
        raise RuntimeError("Metadata entry count does not match enabled C++ test source case count")
    if before_summary["case_names"] != after_summary["case_names"]:
        raise RuntimeError("Before/after enabled test cases differ")
    if before["selected_outputs"] != after["selected_outputs"]:
        raise RuntimeError("Named encode outputs differ before and after the refactor")

    case_evidence = []
    for index, case in enumerate(SELECTED_CASES):
        case_evidence.append(
            {
                **case,
                "before_actual": before["selected_outputs"][index],
                "after_actual": after["selected_outputs"][index],
            }
        )
    report["before"] = before
    report["after"] = after
    report["all_enabled_cases_match"] = before_summary["case_names"] == after_summary["case_names"]
    report["selected_outputs_match"] = before["selected_outputs"] == after["selected_outputs"]
    report["learner_solution_sha256_after"] = {
        relative: sha256(safe_exercise_path(relative)) for relative in config["files"]["solution"]
    }
    report["learner_files_unchanged"] = (
        report["learner_solution_sha256_before"] == report["learner_solution_sha256_after"]
    )
    if not report["learner_files_unchanged"]:
        raise RuntimeError("Learner solution files changed during the isolated check")

    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    cases_path = EVIDENCE / "cases.json"
    cases_path.write_text(json.dumps(case_evidence, indent=2) + "\n")
    print(f"Before: {before_summary['test_case_count']} test cases passed")
    print(f"After: {after_summary['test_case_count']} test cases passed")
    print(f"Before/after case lists match: {report['all_enabled_cases_match']}")
    print(f"Named outputs: {before['selected_outputs']} (identical after refactor)")
    print("Learner solution files unchanged")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
