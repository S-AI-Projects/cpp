#!/usr/bin/env python3
"""Validate word-count two-approach comparison and test execution."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/word-count")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T026"
ALT_CPP = TASK_DIR / "alternative.cpp"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "cmake": run(["cmake", "--version"], ROOT).stdout.splitlines()[0],
        "cxx": run(["c++", "--version"], ROOT).stdout.splitlines()[0],
    }


def main() -> int:
    config_path = EXERCISE / ".meta/config.json"
    if not config_path.exists():
        raise AssertionError("Missing word-count config.json")
    config = json.loads(config_path.read_text())

    hints_path = EXERCISE / ".docs/hints.md"
    if not hints_path.exists():
        raise AssertionError("Missing exercises/practice/word-count/.docs/hints.md")
    hints_text = hints_path.read_text()
    if "Approach Selection" not in hints_text or "large" not in hints_text:
        raise AssertionError("hints.md does not contain approach selection or worked example")

    doc_path = ROOT / "docs/maintenance/word-count.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/word-count.md")

    if not ALT_CPP.exists():
        raise AssertionError("Missing work/R20-T026/alternative.cpp")

    # Verify starter stubs before run
    stubs_before = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_before[sol] = sha256(sol_path)
        content = sol_path.read_text()
        if "TODO: add your solution here" not in content:
            raise AssertionError(f"Learner starter stub in {sol} was modified!")

    # 1. Build and test reference implementation
    with tempfile.TemporaryDirectory(prefix="r20-t026-ref-") as ref_dir:
        temp_root = Path(ref_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)
        shutil.copy2(temp_root / ".meta/example.cpp", temp_root / "word_count.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "word_count.h")

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build"], temp_root)
        ref_binary = temp_root / "build/word-count"

        ref_run = run([str(ref_binary)], temp_root)
        summary_ref = re.search(r"(\d+) test cases?", ref_run.stdout)
        if not summary_ref:
            raise AssertionError("Could not verify reference test count from Catch output")
        ref_count = int(summary_ref.group(1))
        if ref_count != 14:
            raise AssertionError(f"Expected 14 test cases in reference run, got {ref_count}")

    # 2. Build and test alternative implementation
    with tempfile.TemporaryDirectory(prefix="r20-t026-alt-") as alt_dir:
        temp_root = Path(alt_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)
        shutil.copy2(ALT_CPP, temp_root / "word_count.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "word_count.h")

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build"], temp_root)
        alt_binary = temp_root / "build/word-count"

        alt_run = run([str(alt_binary)], temp_root)
        summary_alt = re.search(r"(\d+) test cases?", alt_run.stdout)
        if not summary_alt:
            raise AssertionError("Could not verify alternative test count from Catch output")
        alt_count = int(summary_alt.group(1))
        if alt_count != 14:
            raise AssertionError(f"Expected 14 test cases in alternative run, got {alt_count}")

    # Verify starter stubs after run
    stubs_after = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_after[sol] = sha256(sol_path)
        if stubs_after[sol] != stubs_before[sol]:
            raise AssertionError(f"Learner starter file {sol} was altered during the check!")

    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "task": "R20-T026",
        "versions": versions(),
        "exercise": "word-count",
        "reference_run": {
            "executed_cases": ref_count,
            "summary": ref_run.stdout.strip().splitlines()[-1],
        },
        "alternative_run": {
            "executed_cases": alt_count,
            "summary": alt_run.stdout.strip().splitlines()[-1],
        },
        "worked_example_input": "Joe can't tell between 'large' and large.",
        "worked_example_expected": {"and": 1, "between": 1, "can't": 1, "joe": 1, "large": 2, "tell": 1},
        "stubs_hash_before": stubs_before,
        "stubs_hash_after": stubs_after,
        "both_approaches_passed": True,
    }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("R20-T026 check passed: both reference and alternative passed all 14 test cases.")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"R20-T026 check failed: {err}", file=sys.stderr)
        raise SystemExit(1)
