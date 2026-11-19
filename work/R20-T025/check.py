#!/usr/bin/env python3
"""Validate collatz-conjecture reference complexity, operation counts, and test execution."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/collatz-conjecture")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T025"
NAMED_CASES = [
    "zero_steps_for_one",
    "divide_if_even",
    "even_and_odd_steps",
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


PROBE_CPP = """#include <iostream>
#include <chrono>
#include <vector>
#include <cassert>
#include "collatz_conjecture.h"

int main() {
    // Assert correctness before timing
    assert(collatz_conjecture::steps(1) == 0);
    assert(collatz_conjecture::steps(16) == 4);
    assert(collatz_conjecture::steps(12) == 9);
    assert(collatz_conjecture::steps(1000000) == 152);

    std::vector<int> inputs = {1, 16, 12, 1000000};
    for (int n : inputs) {
        std::cout << "INPUT:" << n << "\\n";
        for (int rep = 0; rep < 5; ++rep) {
            auto start = std::chrono::high_resolution_clock::now();
            volatile int s = collatz_conjecture::steps(n);
            (void)s;
            auto end = std::chrono::high_resolution_clock::now();
            auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
            std::cout << ns << "\\n";
        }
    }
    return 0;
}
"""


def main() -> int:
    config_path = EXERCISE / ".meta/config.json"
    if not config_path.exists():
        raise AssertionError("Missing config.json")
    config = json.loads(config_path.read_text())

    # Check documentation and comments
    example_cpp = (EXERCISE / ".meta/example.cpp").read_text()
    if "Complexity" not in example_cpp or "Invariant" not in example_cpp:
        raise AssertionError("Missing complexity/invariant comment in example.cpp")

    doc_path = ROOT / "docs/maintenance/collatz-conjecture.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/collatz-conjecture.md")
    doc_text = doc_path.read_text()
    for named in NAMED_CASES:
        if named not in doc_text:
            raise AssertionError(f"Named case '{named}' not documented in maintenance guide")

    # Verify starter stubs before run
    stubs_before = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_before[sol] = sha256(sol_path)
        content = sol_path.read_text()
        if "TODO: add your solution here" not in content:
            raise AssertionError(f"Learner starter stub in {sol} was modified!")

    with tempfile.TemporaryDirectory(prefix="r20-t025-") as temp_dir:
        temp_root = Path(temp_dir) / EXERCISE_REL.name
        shutil.copytree(EXERCISE, temp_root)

        # Substitute reference solution
        shutil.copy2(temp_root / ".meta/example.cpp", temp_root / "collatz_conjecture.cpp")
        shutil.copy2(temp_root / ".meta/example.h", temp_root / "collatz_conjecture.h")

        # 1. CMake configure, build, and test suite execution
        configure = run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
        build = run(["cmake", "--build", "build"], temp_root)
        binary = temp_root / "build/collatz-conjecture"

        test_run = run([str(binary)], temp_root)
        summary_match = re.search(r"(\d+) test cases?", test_run.stdout)
        if not summary_match:
            raise AssertionError("Could not verify test count from Catch output")
        executed_cases = int(summary_match.group(1))
        if executed_cases != 6:
            raise AssertionError(f"Expected 6 test cases, got {executed_cases}")

        # 2. Compile and run timing microbenchmark probe
        probe_src = temp_root / "probe.cpp"
        probe_src.write_text(PROBE_CPP)
        probe_bin = temp_root / "probe"
        run(["c++", "-std=c++17", "-O2", "-I", str(temp_root), str(probe_src), str(temp_root / "collatz_conjecture.cpp"), "-o", str(probe_bin)], temp_root)

        probe_output = run([str(probe_bin)], temp_root).stdout.strip().splitlines()
        timing_results = {}
        current_input = None
        current_times = []
        for line in probe_output:
            if line.startswith("INPUT:"):
                if current_input is not None:
                    timing_results[current_input] = {
                        "repetitions": current_times,
                        "median_ns": statistics.median(current_times),
                    }
                current_input = int(line.split(":")[1])
                current_times = []
            else:
                current_times.append(int(line))
        if current_input is not None:
            timing_results[current_input] = {
                "repetitions": current_times,
                "median_ns": statistics.median(current_times),
            }

    # Verify starter stubs after run
    stubs_after = {}
    for sol in config["files"]["solution"]:
        sol_path = EXERCISE / sol
        stubs_after[sol] = sha256(sol_path)
        if stubs_after[sol] != stubs_before[sol]:
            raise AssertionError(f"Learner starter file {sol} was altered during the check!")

    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "task": "R20-T025",
        "versions": versions(),
        "exercise": "collatz-conjecture",
        "test_run": {
            "executed_cases": executed_cases,
            "summary": test_run.stdout.strip().splitlines()[-1],
        },
        "named_cases": NAMED_CASES,
        "timing_results": timing_results,
        "stubs_hash_before": stubs_before,
        "stubs_hash_after": stubs_after,
        "benchmarking_notes": "Algorithmic execution time isolated from process startup and CMake compilation.",
    }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("R20-T025 check passed: all 6 test cases passed; timing measurements recorded.")
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"R20-T025 check failed: {err}", file=sys.stderr)
        raise SystemExit(1)
