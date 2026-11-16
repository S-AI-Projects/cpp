#!/usr/bin/env python3
"""Validate sum-of-multiples rationale and run its maintained reference."""

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
EXERCISE_REL = Path("exercises/practice/sum-of-multiples")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T011"
SELECTED = {
    "54aaab5a-ce86-4edc-8b40-d3ab2400a279": 0,
    "361e4e50-c89b-4f60-95ef-5bc5c595490a": 3,
    "e644e070-040e-4ae0-9910-93c69fc3f7ce": 9,
}
REQUIRED_TESTS = {
    "sum_to_1_yields_0",
    "sum_to_4_yields_3",
    "sum_to_10_yields_23",
}


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
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
    doc_path = ROOT / "docs/maintenance/sum-of-multiples.md"
    doc = doc_path.read_text()

    if len(metadata) != 16:
        raise AssertionError(f"Expected 16 canonical UUID entries; found {len(metadata)}")
    excluded = sum(item.get("include") is False for item in metadata.values())
    if excluded != 0:
        raise AssertionError(f"Expected 0 explicit exclusions; found {excluded}")
    if len(test_names) != 12:
        raise AssertionError(f"Expected 12 C++ cases; found {len(test_names)}")
    if not REQUIRED_TESTS.issubset(test_names):
        raise AssertionError(f"Missing required C++ tests: {sorted(REQUIRED_TESTS - set(test_names))}")
    for uuid in SELECTED:
        rationale = metadata.get(uuid, {}).get("comment", "")
        if not rationale:
            raise AssertionError(f"Missing durable TOML comment for {uuid}")
        if uuid not in doc:
            raise AssertionError(f"Missing maintenance mapping for {uuid}")

    # The canonical values are independently exercised against the temporary
    # reference copy, including the one-factor case absent from the enabled suite.
    canonical_inputs = [([3, 5], 1), ([3, 5], 4), ([3], 7)]
    expected = [0, 3, 9]
    report: dict[str, object] = {
        "task": "R20-T011",
        "versions": versions(),
        "counts_before_after": {
            "metadata_entries": {"before": 16, "after": len(metadata)},
            "explicit_exclusions": {"before": 0, "after": excluded},
            "cpp_test_cases": {"before": 12, "after": len(test_names)},
        },
        "enabled_test_cases": test_names,
        "canonical_results": [],
    }

    with tempfile.TemporaryDirectory(prefix="r20-t011-") as temp_name:
        temp_root = Path(temp_name) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)
        solutions = [Path(item) for item in config["files"]["solution"]]
        examples = [Path(item) for item in config["files"]["example"]]
        for example in examples:
            destinations = [path for path in solutions if path.suffix == example.suffix]
            if len(destinations) != 1:
                raise AssertionError(f"Cannot uniquely map reference {example} to solution: {destinations}")
            destination = temp_root / destinations[0]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_root / example, destination)

        probe_source = Path(temp_name) / "canonical_probe.cpp"
        probe_source.write_text(
            '#include "sum_of_multiples.h"\n'
            '#include <iostream>\n'
            'int main() {\n'
            '  std::cout << sum_of_multiples::to({3, 5}, 1) << "\\n";\n'
            '  std::cout << sum_of_multiples::to({3, 5}, 4) << "\\n";\n'
            '  std::cout << sum_of_multiples::to({3}, 7) << "\\n";\n'
            '}\n'
        )
        source_cpp = next((temp_root / path for path in solutions if path.suffix == ".cpp"), None)
        if source_cpp is None:
            raise AssertionError("No C++ solution path was declared in config.json")
        probe_binary = Path(temp_name) / "canonical_probe"
        run(["c++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-I", str(temp_root), str(probe_source), str(source_cpp), "-o", str(probe_binary)], ROOT)
        probe_output = run([str(probe_binary)], ROOT).stdout.strip().splitlines()
        actual = [int(value) for value in probe_output]
        if actual != expected:
            raise AssertionError(f"Canonical outputs differ: expected {expected}, got {actual}")
        report["canonical_results"] = [
            {"factors": factors, "limit": limit, "expected": want, "actual": got}
            for (factors, limit), want, got in zip(canonical_inputs, expected, actual)
        ]

        configure = run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        build = run(["cmake", "--build", "build"], temp_root)
        binary = temp_root / "build" / EXERCISE_REL.name
        listing_result = subprocess.run(
            [str(binary), "--list-test-names-only"],
            cwd=temp_root,
            text=True,
            capture_output=True,
        )
        listing = listing_result.stdout
        listed_names = [line.strip() for line in listing.splitlines() if line.strip()]
        # Catch2 v2 returns the number of listed tests as its status for this
        # listing-only command; the actual test execution below must return 0.
        if listing_result.returncode not in (0, len(listed_names)):
            raise RuntimeError(
                f"Test listing failed ({listing_result.returncode}): {listing_result.stderr}"
            )
        if len(listed_names) != len(test_names):
            raise AssertionError(f"Test executable lists {len(listed_names)} cases; source has {len(test_names)}")
        test_run = run([str(binary)], temp_root)
        summary = re.search(r"(\d+) test cases?", test_run.stdout + test_run.stderr)
        if not summary:
            raise AssertionError("Could not verify the executed case count from Catch output")
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
    print(f"R20-T011 checks passed: 16 metadata entries, 0 explicit exclusions, 12 executed cases.")
    print(f"Canonical selected outputs: {actual} (expected {expected}).")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"R20-T011 check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
