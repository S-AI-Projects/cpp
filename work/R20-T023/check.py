#!/usr/bin/env python3
"""Validate twelve-days mutation-driven regression check."""

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
EXERCISE_REL = Path("exercises/practice/twelve-days")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T023"
REJECTING_TEST = "second day two turtle doves"
REJECTING_UUID = "1c64508a-df3d-420a-b8e1-fe408847854a"


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
        raise AssertionError("Missing twelve-days config.json")
    config = json.loads(config_path.read_text())

    # Check documentation and hints
    hints_path = EXERCISE / ".docs/hints.md"
    if not hints_path.exists():
        raise AssertionError("Missing exercises/practice/twelve-days/.docs/hints.md")
    hints_text = hints_path.read_text()
    if "recite(2, 2)" not in hints_text and "verse 2" not in hints_text:
        raise AssertionError("hints.md does not provide diagnostic input guidance")

    doc_path = ROOT / "docs/maintenance/twelve-days.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/twelve-days.md")
    doc_text = doc_path.read_text()
    if REJECTING_TEST not in doc_text or REJECTING_UUID not in doc_text:
        raise AssertionError("docs/maintenance/twelve-days.md does not identify rejecting test case")

    # Verify starter stubs before run
    stubs_before = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_before[sol] = sha256(sol_path)
        content = sol_path.read_text()
        if "TODO: add your solution here" not in content:
            raise AssertionError(f"Learner starter stub in {sol} was modified!")

    # 1. Test Original Reference
    with tempfile.TemporaryDirectory(prefix="r20-t023-orig-") as orig_dir:
        temp_root = Path(orig_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)

        # Substitute reference solution
        shutil.copy2(temp_root / ".meta/example.cpp", temp_root / "twelve_days.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "twelve_days.h")

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build", "--target", "twelve-days"], temp_root)
        orig_binary = temp_root / "build/twelve-days"

        orig_run = subprocess.run([str(orig_binary)], cwd=temp_root, text=True, capture_output=True)
        if orig_run.returncode != 0:
            raise AssertionError(f"Original reference test run failed ({orig_run.returncode}):\n{orig_run.stdout}\n{orig_run.stderr}")
        summary_match = re.search(r"(\d+) test cases?", orig_run.stdout)
        if not summary_match:
            raise AssertionError("Could not verify original test count from Catch output")
        orig_executed = int(summary_match.group(1))
        if orig_executed != 15:
            raise AssertionError(f"Expected 15 executed test cases, got {orig_executed}")
        orig_summary = orig_run.stdout.strip().splitlines()[-1]

    # 2. Test Mutated Reference
    with tempfile.TemporaryDirectory(prefix="r20-t023-mutant-") as mut_dir:
        temp_root = Path(mut_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)

        # Substitute reference solution
        shutil.copy2(temp_root / ".meta/example.cpp", temp_root / "twelve_days.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "twelve_days.h")

        # Apply mutation: replace ', and ' with ', '
        source = (temp_root / "twelve_days.cpp").read_text()
        mutant_source = source.replace('result += std::string{", and "};', 'result += std::string{", "};')
        if mutant_source == source:
            raise AssertionError("Failed to apply deliberate mutant to example.cpp")
        (temp_root / "twelve_days.cpp").write_text(mutant_source)

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build", "--target", "twelve-days"], temp_root)
        mut_binary = temp_root / "build/twelve-days"

        # Run specifically against the target test case
        mut_run = subprocess.run([str(mut_binary), REJECTING_TEST], cwd=temp_root, text=True, capture_output=True)
        if mut_run.returncode == 0:
            raise AssertionError(f"Mutant unexpectedly passed test '{REJECTING_TEST}'!")
        if "FAILED" not in mut_run.stdout or "1 failed" not in mut_run.stdout:
            raise AssertionError(f"Mutant output did not indicate expected assertion failure:\n{mut_run.stdout}")

        mut_summary = "1 test case failed as expected"

    # Verify starter stubs after run
    stubs_after = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_after[sol] = sha256(sol_path)
        if stubs_after[sol] != stubs_before[sol]:
            raise AssertionError(f"Learner starter file {sol} was altered during the check!")

    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "task": "R20-T023",
        "versions": versions(),
        "exercise": "twelve-days",
        "original_run": {
            "exit_code": orig_run.returncode,
            "executed_cases": orig_executed,
            "summary": orig_summary,
        },
        "mutant_run": {
            "rejecting_test": REJECTING_TEST,
            "rejecting_uuid": REJECTING_UUID,
            "exit_code": mut_run.returncode,
            "summary": mut_summary,
            "minimal_input": "recite(2, 2)",
        },
        "stubs_hash_before": stubs_before,
        "stubs_hash_after": stubs_after,
        "regression_verified": True,
    }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("R20-T023 check passed: original passed 15 cases; mutant correctly rejected by 'second day two turtle doves'.")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"R20-T023 check failed: {err}", file=sys.stderr)
        raise SystemExit(1)
