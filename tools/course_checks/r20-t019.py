#!/usr/bin/env python3
"""Run simple-linked-list reference tests in a temporary exercise copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def load_config(config_path: Path) -> dict:
    config = json.loads(config_path.read_text())
    if not isinstance(config.get("files"), dict):
        raise ValueError("config.json must contain a files object")
    return config


def resolve_file(root: Path, configured: str) -> Path:
    relative = Path(configured)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Configured path is absolute or traverses parents: {configured}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError(f"Configured path escapes the exercise: {configured}") from error
    if not resolved.is_file():
        raise FileNotFoundError(f"Configured file does not exist: {configured}")
    return resolved


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def execute(command: list[str], cwd: Path, timeout: float | None) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout,
        }
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return {
            "command": command,
            "returncode": 124,
            "timed_out": True,
            "stdout": output,
        }


def parse_junit(output: str) -> dict:
    try:
        root = ET.fromstring(output)
    except ET.ParseError as error:
        return {
            "test_case_count": 0,
            "failed_case_count": 0,
            "error_case_count": 0,
            "case_names": [],
            "failures": [],
            "parse_error": str(error),
        }
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


def run_isolated(args: argparse.Namespace, report: dict) -> int:
    exercise_dir = args.exercise_dir.resolve()
    config_path = args.config.resolve() if args.config else exercise_dir / ".meta/config.json"
    config = load_config(config_path)
    solution_rel = config["files"].get("solution")
    test_rel = config["files"].get("test")
    example_rel = config["files"].get("example")
    if not all(isinstance(value, list) and value for value in (solution_rel, test_rel, example_rel)):
        raise ValueError("config.json must declare non-empty solution, test, and example path lists")
    if len(solution_rel) != len(example_rel):
        raise ValueError("solution and example path lists must have matching lengths")

    learner_paths = [resolve_file(exercise_dir, relative) for relative in solution_rel]
    test_paths = [resolve_file(exercise_dir, relative) for relative in test_rel]
    example_paths = [resolve_file(exercise_dir, relative) for relative in example_rel]
    reference_source = Path(args.reference_source).resolve() if args.reference_source else None
    if reference_source and not reference_source.is_file():
        raise FileNotFoundError(f"Reference override does not exist: {reference_source}")

    report.update(
        {
            "exercise_dir": str(exercise_dir),
            "config_path": str(config_path),
            "selection": args.selection,
            "learner_solution_sha256_before": file_hashes(learner_paths),
            "configured_test_files": [str(path) for path in test_paths],
            "configured_example_files": [str(path) for path in example_paths],
        }
    )

    temp_parent = args.temp_parent.resolve() if args.temp_parent else None
    if temp_parent:
        temp_parent.mkdir(parents=True, exist_ok=True)

    temporary_path: Path | None = None
    return_code = 1
    try:
        with tempfile.TemporaryDirectory(
            prefix="course-r20-t019-",
            dir=str(temp_parent) if temp_parent else None,
        ) as temporary:
            temporary_path = Path(temporary)
            exercise_copy = temporary_path / exercise_dir.name
            shutil.copytree(exercise_dir, exercise_copy)
            copied_config = load_config(exercise_copy / ".meta/config.json")

            copied_solution = copied_config["files"]["solution"]
            copied_examples = copied_config["files"]["example"]
            for index, (solution_file, example_file) in enumerate(zip(copied_solution, copied_examples)):
                destination = resolve_file(exercise_copy, solution_file)
                source = resolve_file(exercise_copy, example_file)
                if index == 0 and reference_source:
                    shutil.copy2(reference_source, destination)
                else:
                    shutil.copy2(source, destination)

            configure = execute(
                ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"],
                exercise_copy,
                args.timeout_seconds,
            )
            report["configure"] = configure
            if configure["timed_out"]:
                report["status"] = "timed_out"
                return_code = 124
            elif configure["returncode"] != 0:
                report["status"] = "configure_failed"
                return_code = 1
            else:
                build = execute(["cmake", "--build", "build"], exercise_copy, args.timeout_seconds)
                report["build"] = build
                if build["timed_out"]:
                    report["status"] = "timed_out"
                    return_code = 124
                else:
                    executable = exercise_copy / "build" / exercise_dir.name
                    if not executable.is_file():
                        report["status"] = "build_failed"
                        return_code = 1
                    else:
                        command = [str(executable), "--reporter", "junit"]
                        if args.selection == "none":
                            command.append("__r20_t019_no_test_selection__")
                        tests_run = execute(command, exercise_copy, args.timeout_seconds)
                        report["test_run"] = tests_run
                        if tests_run["timed_out"]:
                            report["status"] = "timed_out"
                            return_code = 124
                        else:
                            test_summary = parse_junit(tests_run["stdout"])
                            report["test_summary"] = test_summary
                            if test_summary["test_case_count"] == 0:
                                report["status"] = "zero_tests"
                                return_code = 2
                            elif (
                                tests_run["returncode"] != 0
                                or test_summary["failed_case_count"]
                                or test_summary["error_case_count"]
                                or build["returncode"] != 0
                            ):
                                report["status"] = "test_failure"
                                return_code = 1
                            else:
                                report["status"] = "passed"
                                return_code = 0
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        report["interrupted"] = True
        return_code = 130
    finally:
        report["temporary_directory"] = str(temporary_path) if temporary_path else None
        report["temporary_files_removed"] = temporary_path is None or not temporary_path.exists()
        report["learner_solution_sha256_after"] = file_hashes(learner_paths)
        report["learner_files_unchanged"] = (
            report["learner_solution_sha256_before"] == report["learner_solution_sha256_after"]
        )
        if not report["learner_files_unchanged"]:
            report["status"] = "learner_files_changed"
            return_code = 1
        if not report["temporary_files_removed"]:
            report["status"] = "temporary_files_not_removed"
            return_code = 1

    return return_code


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exercise-dir",
        type=Path,
        default=repository_root / "exercises/practice/simple-linked-list",
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--reference-source", type=Path, help="optional reference source override for validation")
    parser.add_argument("--selection", choices=("all", "none"), default="all")
    parser.add_argument("--temp-parent", type=Path, help="parent directory for the disposable exercise copy")
    parser.add_argument("--timeout-seconds", type=float, help="optional timeout for each child process")
    args = parser.parse_args()

    report: dict = {
        "task": "R20-T019",
        "status": "not_started",
        "selection": args.selection,
    }
    try:
        return_code = run_isolated(args, report)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        report["interrupted"] = True
        return_code = 130
    except Exception as error:
        report["status"] = "runner_error"
        report["error"] = f"{type(error).__name__}: {error}"
        return_code = 1

    report["exit_code"] = return_code
    print(json.dumps(report, indent=2))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
