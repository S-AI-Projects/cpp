#!/usr/bin/env python3
"""Validate sublist reference refactor and verify behavioral equivalence."""

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
EXERCISE_REL = Path("exercises/practice/sublist")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T024"
ANCHOR_CASES = [
    "empty lists",
    "empty list within non empty list",
    "non empty list contains empty list",
]


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


ORIGINAL_EXAMPLE_CPP = """#include <algorithm>
#include <iterator>

#include "sublist.h"

namespace sublist {
bool is_sublist(const std::vector<int>& sublist,
                const std::vector<int>& superlist) {
    auto superlist_end = std::prev(
        superlist.end(), std::max<std::size_t>(1, sublist.size()) - 1);
    for (auto it{superlist.begin()}; it != superlist_end; std::advance(it, 1)) {
        if (std::equal(sublist.begin(), sublist.end(), it)) return true;
    }
    return false;
}

List_comparison sublist(const std::vector<int>& list_one,
                        const std::vector<int>& list_two) {
    if (list_one == list_two) {
        return List_comparison::equal;
    }
    if (list_one.size() < list_two.size() && is_sublist(list_one, list_two)) {
        return List_comparison::sublist;
    }
    if (list_one.size() > list_two.size() && is_sublist(list_two, list_one)) {
        return List_comparison::superlist;
    }
    return List_comparison::unequal;
}
}  // namespace sublist
"""


def main() -> int:
    config_path = EXERCISE / ".meta/config.json"
    if not config_path.exists():
        raise AssertionError("Missing sublist config.json")
    config = json.loads(config_path.read_text())

    doc_path = ROOT / "docs/maintenance/sublist.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/sublist.md")
    doc_text = doc_path.read_text()
    for anchor in ANCHOR_CASES:
        if anchor not in doc_text:
            raise AssertionError(f"Missing anchor case '{anchor}' in maintenance documentation")

    # Verify learner stubs before run
    stubs_before = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_before[sol] = sha256(sol_path)
        content = sol_path.read_text()
        if "TODO: add your solution here" not in content:
            raise AssertionError(f"Learner starter stub in {sol} was modified!")

    # 1. Build and test original reference in temp dir
    with tempfile.TemporaryDirectory(prefix="r20-t024-orig-") as orig_dir:
        temp_root = Path(orig_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)
        (temp_root / "sublist.cpp").write_text(ORIGINAL_EXAMPLE_CPP)
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "sublist.h")

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build"], temp_root)
        orig_binary = temp_root / "build/sublist"

        orig_run = run([str(orig_binary)], temp_root)
        summary_orig = re.search(r"(\d+) test cases?", orig_run.stdout)
        if not summary_orig:
            raise AssertionError("Could not verify original test count from Catch output")
        orig_count = int(summary_orig.group(1))
        if orig_count != 18:
            raise AssertionError(f"Expected 18 test cases in original run, got {orig_count}")

    # 2. Build and test refactored reference in temp dir
    with tempfile.TemporaryDirectory(prefix="r20-t024-refactored-") as ref_dir:
        temp_root = Path(ref_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)
        shutil.copy2(temp_root / ".meta/example.cpp", temp_root / "sublist.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "sublist.h")

        run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        run(["cmake", "--build", "build"], temp_root)
        ref_binary = temp_root / "build/sublist"

        ref_run = run([str(ref_binary)], temp_root)
        summary_ref = re.search(r"(\d+) test cases?", ref_run.stdout)
        if not summary_ref:
            raise AssertionError("Could not verify refactored test count from Catch output")
        ref_count = int(summary_ref.group(1))
        if ref_count != 18:
            raise AssertionError(f"Expected 18 test cases in refactored run, got {ref_count}")

    # Verify learner stubs after run
    stubs_after = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_after[sol] = sha256(sol_path)
        if stubs_after[sol] != stubs_before[sol]:
            raise AssertionError(f"Learner starter file {sol} was altered during the check!")

    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "task": "R20-T024",
        "versions": versions(),
        "exercise": "sublist",
        "original_executed_cases": orig_count,
        "refactored_executed_cases": ref_count,
        "original_summary": orig_run.stdout.strip().splitlines()[-1],
        "refactored_summary": ref_run.stdout.strip().splitlines()[-1],
        "anchor_cases": ANCHOR_CASES,
        "stubs_hash_before": stubs_before,
        "stubs_hash_after": stubs_after,
        "equivalence_verified": True,
    }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("R20-T024 check passed: both original and refactored reference passed all 18 test cases.")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"R20-T024 check failed: {err}", file=sys.stderr)
        raise SystemExit(1)
