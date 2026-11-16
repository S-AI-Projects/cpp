#!/usr/bin/env python3
"""Exercise simple-linked-list runner success, failure, zero-case and timeout paths."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
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
EXERCISE = ROOT / "exercises/practice/simple-linked-list"
RUNNER = ROOT / "tools/course_checks/r20-t019.py"
EVIDENCE = Path(__file__).resolve().parent
NAMED_CASES = [
    {
        "name": "EmptyListHasSizeZero",
        "input": "new empty List",
        "expected": "size() == 0",
    },
    {
        "name": "SingletonListHasSizeOne",
        "input": "push(44)",
        "expected": "size() == 1",
    },
    {
        "name": "NonEmptyListHasCorrectSize",
        "input": "push(44), push(42), push(47), push(-11)",
        "expected": "size() == 4",
    },
]


def file_hashes() -> dict[str, str]:
    config = json.loads((EXERCISE / ".meta/config.json").read_text())
    return {
        str(EXERCISE / relative): hashlib.sha256((EXERCISE / relative).read_bytes()).hexdigest()
        for relative in config["files"]["solution"]
    }


def run_runner(label: str, options: list[str], temporary_root: Path, expected_exit: int) -> dict:
    temp_parent = temporary_root / f"{label}-temps"
    temp_parent.mkdir()
    command = ["python3", str(RUNNER), "--temp-parent", str(temp_parent), *options]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=30,
        env={**os.environ, "LC_ALL": "C"},
    )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Runner did not emit JSON for {label}: {completed.stdout}") from error
    if completed.returncode != expected_exit:
        raise RuntimeError(
            f"{label} runner exit was {completed.returncode}, expected {expected_exit}: {completed.stdout}"
        )
    leftovers = [str(path) for path in temp_parent.iterdir()]
    if leftovers:
        raise RuntimeError(f"Runner left temporary files for {label}: {leftovers}")
    result["outer_exit_code"] = completed.returncode
    result["temporary_parent_empty"] = not leftovers
    return result


def tool_version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.stdout.splitlines()[0] if result.stdout else f"exit {result.returncode}"


def direct_case_probe(temporary_root: Path) -> dict:
    config = json.loads((EXERCISE / ".meta/config.json").read_text())
    exercise_copy = temporary_root / "direct-probe-exercise"
    shutil.copytree(EXERCISE, exercise_copy)
    for solution_rel, example_rel in zip(config["files"]["solution"], config["files"]["example"]):
        shutil.copy2(exercise_copy / example_rel, exercise_copy / solution_rel)

    source = temporary_root / "direct_case_probe.cpp"
    source.write_text(
        '#include <iostream>\n'
        '#include "simple_linked_list.h"\n'
        'int main() {\n'
        '    simple_linked_list::List empty;\n'
        '    std::cout << empty.size() << "\\n";\n'
        '    simple_linked_list::List singleton;\n'
        '    singleton.push(44);\n'
        '    std::cout << singleton.size() << "\\n";\n'
        '    simple_linked_list::List multiple;\n'
        '    multiple.push(44); multiple.push(42); multiple.push(47); multiple.push(-11);\n'
        '    std::cout << multiple.size() << "\\n";\n'
        '}\n'
    )
    binary = temporary_root / "direct_case_probe"
    build = subprocess.run(
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
            str(source),
            "-o",
            str(binary),
        ],
        cwd=temporary_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if build.returncode != 0:
        raise RuntimeError(f"Direct case probe failed to compile: {build.stdout}")
    execution = subprocess.run(
        [str(binary)],
        cwd=temporary_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if execution.returncode != 0:
        raise RuntimeError(f"Direct case probe failed: {execution.stdout}")
    actual = [int(value) for value in execution.stdout.splitlines()]
    expected = [0, 1, 4]
    if actual != expected:
        raise RuntimeError(f"Direct named-case outputs were {actual!r}, expected {expected!r}")
    return {
        "compile_returncode": build.returncode,
        "compile_output": build.stdout,
        "run_returncode": execution.returncode,
        "stdout": execution.stdout,
        "expected": expected,
        "actual": actual,
    }


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    hashes_before_all = file_hashes()
    source_text = (EXERCISE / "simple_linked_list_test.cpp").read_text()
    for case in NAMED_CASES:
        if case["name"] not in source_text:
            raise RuntimeError(f"Named test missing from source: {case['name']}")

    reference = (EXERCISE / ".meta/example.cpp").read_text()
    original_size_definition = "std::size_t List::size() const { return current_size; }"
    if reference.count(original_size_definition) != 1:
        raise RuntimeError("Could not create the deliberate size() mutant from the maintained reference")
    failing_reference = reference.replace(
        original_size_definition,
        "std::size_t List::size() const { return current_size == 0 ? 1 : current_size; }",
    )

    report: dict = {
        "task_id": "R20-T019",
        "issue": "https://github.com/S-AI-Projects/cpp/issues/23",
        "named_cases": NAMED_CASES,
        "tests_metadata": ".meta/tests.toml is not present; use the executable JUnit case count.",
        "tool_versions": {
            "python": tool_version(["python3", "--version"]),
            "cmake": tool_version(["cmake", "--version"]),
            "cxx": tool_version(["c++", "--version"]),
        },
        "learner_solution_sha256_before_all_runs": hashes_before_all,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t019-check-") as temporary:
        temporary_root = Path(temporary)
        mutant_path = temporary_root / "failing_reference.cpp"
        mutant_path.write_text(failing_reference)

        success = run_runner("success", [], temporary_root, expected_exit=0)
        if success.get("status") != "passed" or success["test_summary"]["test_case_count"] <= 0:
            raise RuntimeError("Real reference did not produce a successful non-zero test run")
        for case in NAMED_CASES:
            if case["name"] not in success["test_summary"]["case_names"]:
                raise RuntimeError(f"Named test did not pass in the real-reference run: {case['name']}")

        failing = run_runner(
            "failure",
            ["--reference-source", str(mutant_path)],
            temporary_root,
            expected_exit=1,
        )
        if (
            failing.get("status") != "test_failure"
            or failing.get("test_summary", {}).get("failed_case_count", 0) <= 0
            or "EmptyListHasSizeZero" not in failing.get("test_summary", {}).get("case_names", [])
        ):
            raise RuntimeError("Deliberately failing reference was not caught by its assertion")

        empty = run_runner("empty", ["--selection", "none"], temporary_root, expected_exit=2)
        if empty.get("status") != "zero_tests" or empty["test_summary"]["test_case_count"] != 0:
            raise RuntimeError("Empty test selection did not produce the expected zero-test failure")

        interrupted = run_runner(
            "interrupted",
            ["--timeout-seconds", "0.001"],
            temporary_root,
            expected_exit=124,
        )
        if interrupted.get("status") != "timed_out" or not interrupted.get("temporary_files_removed"):
            raise RuntimeError("Timed-out child did not report interruption and clean its temporary copy")
        direct_probe = direct_case_probe(temporary_root)

    hashes_after_all = file_hashes()
    for name, result in (("success", success), ("failure", failing), ("empty", empty), ("interrupted", interrupted)):
        if not result.get("learner_files_unchanged"):
            raise RuntimeError(f"Runner changed learner files in {name} mode")
        if not result.get("temporary_files_removed") or not result.get("temporary_parent_empty"):
            raise RuntimeError(f"Runner did not clean temporary files in {name} mode")
    if hashes_before_all != hashes_after_all:
        raise RuntimeError("Learner file hashes changed across runner modes")

    report.update(
        {
            "success_run": success,
            "failing_reference_run": failing,
            "zero_selection_run": empty,
            "timeout_interruption_run": interrupted,
            "direct_named_case_probe": direct_probe,
            "learner_solution_sha256_after_all_runs": hashes_after_all,
            "learner_files_unchanged_across_runs": hashes_before_all == hashes_after_all,
        }
    )
    report_path = EVIDENCE / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    cases_path = EVIDENCE / "cases.json"
    case_evidence = []
    for index, case in enumerate(NAMED_CASES):
        case_evidence.append({**case, "actual": direct_probe["actual"][index], "test_status": "passed"})
    cases_path.write_text(json.dumps(case_evidence, indent=2) + "\n")
    print(f"Real reference: {success['test_summary']['test_case_count']} cases passed")
    print(f"Deliberate mutant: {failing['test_summary']['failed_case_count']} failed cases; non-zero status caught")
    print(f"Empty selection: {empty['status']} with 0 cases and exit {empty['exit_code']}")
    print(f"Timeout: {interrupted['status']}; temp copy removed")
    print("Learner hashes identical across all four runs")
    print(f"Evidence: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        raise
