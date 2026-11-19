#!/usr/bin/env python3
"""Validate two-fer rationale and run its maintained reference in an isolated temporary directory."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/two-fer")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T021"
SELECTED = {
    "1cf3e15a-a3d7-4a87-aeb3-ba1b43bc8dce": "One for you, one for me.",
    "b4c6dbb8-b4fb-42c2-bafd-10785abe7709": "One for Alice, one for me.",
    "3549048d-1a6e-4653-9a79-b0bda163e8d5": "One for Bob, one for me.",
}
REQUIRED_TESTS = {
    "no_name_given",
    "a_name_given",
    "another_name_given",
}


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "cmake": run(["cmake", "--version"], ROOT).stdout.splitlines()[0],
        "cxx": run(["c++", "--version"], ROOT).stdout.splitlines()[0],
    }


def main() -> int:
    config = json.loads((EXERCISE / ".meta/config.json").read_text())
    metadata_text = (EXERCISE / ".meta/tests.toml").read_text()
    metadata = tomllib.loads(metadata_text)
    test_path = EXERCISE / config["files"]["test"][0]
    test_source = test_path.read_text()
    test_names = re.findall(r'TEST_CASE\("([^"]+)"\)', test_source)
    doc_path = ROOT / "docs/maintenance/two-fer.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/two-fer.md")
    doc = doc_path.read_text()

    # Verify learner stubs remain unsolved
    for solution_file in config["files"]["solution"]:
        stub_text = (EXERCISE / solution_file).read_text()
        if "TODO: add your solution here" not in stub_text:
            raise AssertionError(f"Learner stub in {solution_file} was modified!")

    if len(metadata) != 3:
        raise AssertionError(f"Expected 3 canonical UUID entries; found {len(metadata)}")
    excluded = sum(item.get("include") is False for item in metadata.values())
    if excluded != 0:
        raise AssertionError(f"Expected 0 explicit exclusions; found {excluded}")
    if len(test_names) != 3:
        raise AssertionError(f"Expected 3 C++ cases; found {len(test_names)}")
    if not REQUIRED_TESTS.issubset(test_names):
        raise AssertionError(f"Missing required C++ tests: {sorted(REQUIRED_TESTS - set(test_names))}")
    for uuid in SELECTED:
        rationale = metadata.get(uuid, {}).get("comment", "")
        if not rationale:
            raise AssertionError(f"Missing durable TOML comment for {uuid}")
        if uuid not in doc:
            raise AssertionError(f"Missing maintenance mapping for {uuid}")

    report: dict[str, object] = {
        "task": "R20-T021",
        "versions": versions(),
        "counts_before_after": {
            "metadata_entries": {"before": 3, "after": len(metadata)},
            "explicit_exclusions": {"before": 0, "after": excluded},
            "cpp_test_cases": {"before": 3, "after": len(test_names)},
        },
        "enabled_test_cases": test_names,
        "canonical_results": [],
    }

    with tempfile.TemporaryDirectory(prefix="r20-t021-") as temp_name:
        temp_root = Path(temp_name) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)

        # Substitute reference solution in temp copy only
        # example is .meta/example.h; replace solution two_fer.h
        example_path = temp_root / ".meta/example.h"
        target_h = temp_root / "two_fer.h"
        shutil.copy2(example_path, target_h)

        # 1. Canonical Probe
        probe_source = Path(temp_name) / "canonical_probe.cpp"
        probe_source.write_text(
            '#include "two_fer.h"\n'
            '#include <iostream>\n'
            'int main() {\n'
            '  std::cout << two_fer::two_fer() << "\\n";\n'
            '  std::cout << two_fer::two_fer("Alice") << "\\n";\n'
            '  std::cout << two_fer::two_fer("Bob") << "\\n";\n'
            '}\n'
        )
        probe_binary = Path(temp_name) / "canonical_probe"
        # Compile probe with C++17
        run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-I", str(temp_root), str(probe_source), "-o", str(probe_binary)], ROOT)
        probe_output = run([str(probe_binary)], ROOT).stdout.strip().splitlines()
        expected = list(SELECTED.values())
        if probe_output != expected:
            raise AssertionError(f"Canonical outputs differ: expected {expected}, got {probe_output}")

        report["canonical_results"] = [
            {"uuid": uuid, "expected": exp, "actual": act}
            for uuid, exp, act in zip(SELECTED.keys(), expected, probe_output)
        ]

        # 2. CMake configure and build
        configure = run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        build = run(["cmake", "--build", "build"], temp_root)
        binary = temp_root / "build" / EXERCISE_REL.name

        listing_result = subprocess.run(
            [str(binary), "--list-test-names-only"],
            cwd=temp_root,
            text=True,
            capture_output=True,
        )
        listed_names = [line.strip() for line in listing_result.stdout.splitlines() if line.strip()]
        if listing_result.returncode not in (0, len(listed_names)):
            raise RuntimeError(
                f"Test listing failed ({listing_result.returncode}): {listing_result.stderr}"
            )
        if len(listed_names) != len(test_names):
            raise AssertionError(f"Test executable lists {len(listed_names)} cases; source has {len(test_names)}")

        test_run = run([str(binary)], temp_root)
        summary = re.search(r"(\d+) test cases?", test_run.stdout + test_run.stderr)
        if not summary:
            raise AssertionError("Could not verify executed case count from Catch output")
        executed = int(summary.group(1))
        if executed != len(test_names):
            raise AssertionError(f"Expected {len(test_names)} executed cases; Catch reported {executed}")

        report["test_run"] = {
            "configure_exit": configure.returncode,
            "build_exit": build.returncode,
            "list_exit": listing_result.returncode,
            "executable_exit": test_run.returncode,
            "listed_cases": len(listed_names),
            "executed_cases": executed,
            "summary": test_run.stdout.strip().splitlines()[-1] if test_run.stdout.strip() else "",
        }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"R20-T021 checks passed: 3 metadata entries, 0 explicit exclusions, 3 executed cases.")
    print(f"Canonical probe results: {probe_output}")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"R20-T021 check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
