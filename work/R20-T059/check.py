#!/usr/bin/env python3
"""
work/R20-T059/check.py

Verification runner for exercises/practice/two-bucket.
Computes SHA-256 hashes of learner files, executes three mandatory test scenarios
in isolated temporary directories, verifies Catch2 test results and test metadata,
and ensures complete cleanup and immutability of learner files.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


# Project paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "two-bucket"
META_DIR = EXERCISE_DIR / ".meta"
CONFIG_JSON_PATH = META_DIR / "config.json"
TESTS_TOML_PATH = META_DIR / "tests.toml"
TEST_CPP_PATH = EXERCISE_DIR / "two_bucket_test.cpp"
OUTPUT_LOG_PATH = REPO_ROOT / "work" / "R20-T059" / "check_output.log"


def log(msg: str, log_file=None):
    """Print to stdout and append to the log file."""
    print(msg)
    if log_file:
        log_file.write(msg + "\n")
        log_file.flush()


def compute_dir_hashes(directory: Path) -> dict[str, str]:
    """Compute SHA-256 hash for every file in the given directory (relative path -> sha256)."""
    hashes = {}
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            rel = p.relative_to(directory).as_posix()
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            hashes[rel] = sha
    return hashes


def parse_catch2_output(stdout: str) -> dict:
    """
    Parse Catch2 test results output.
    Returns:
        dict with keys:
          'executed_cases': int
          'failed_cases': int
          'passed_cases': int
          'passed_assertions': int
          'failed_assertions': int
          'total_assertions': int
          'all_passed': bool
          'no_tests_ran': bool
    """
    res = {
        "executed_cases": 0,
        "failed_cases": 0,
        "passed_cases": 0,
        "passed_assertions": 0,
        "failed_assertions": 0,
        "total_assertions": 0,
        "all_passed": False,
        "no_tests_ran": False,
    }

    if "No tests ran" in stdout:
        res["no_tests_ran"] = True
        return res

    # Check for "All tests passed (X assertions in Y test cases)"
    all_passed_match = re.search(
        r"All tests passed \((\d+) assertions? in (\d+) test cases?\)", stdout
    )
    if all_passed_match:
        assertions = int(all_passed_match.group(1))
        cases = int(all_passed_match.group(2))
        res["all_passed"] = True
        res["executed_cases"] = cases
        res["passed_cases"] = cases
        res["total_assertions"] = assertions
        res["passed_assertions"] = assertions
        return res

    # Check for multi-line summary:
    # test cases:  9 |  9 failed
    # assertions: 23 | 2 passed | 21 failed
    # or variations with passed / failed
    tc_match = re.search(r"test cases:\s*(\d+)\s*\|(.*)", stdout)
    if tc_match:
        total_tc = int(tc_match.group(1))
        res["executed_cases"] = total_tc
        tc_rest = tc_match.group(2)
        failed_tc_match = re.search(r"(\d+)\s+failed", tc_rest)
        passed_tc_match = re.search(r"(\d+)\s+passed", tc_rest)
        if failed_tc_match:
            res["failed_cases"] = int(failed_tc_match.group(1))
        if passed_tc_match:
            res["passed_cases"] = int(passed_tc_match.group(1))
        if not failed_tc_match and passed_tc_match:
            res["all_passed"] = (res["passed_cases"] == total_tc)

    as_match = re.search(r"assertions:\s*(\d+)\s*\|(.*)", stdout)
    if as_match:
        total_as = int(as_match.group(1))
        res["total_assertions"] = total_as
        as_rest = as_match.group(2)
        failed_as_match = re.search(r"(\d+)\s+failed", as_rest)
        passed_as_match = re.search(r"(\d+)\s+passed", as_rest)
        if failed_as_match:
            res["failed_assertions"] = int(failed_as_match.group(1))
        if passed_as_match:
            res["passed_assertions"] = int(passed_as_match.group(1))

    return res


def extract_enabled_test_cases(test_cpp_path: Path) -> list[dict]:
    """
    Extract test cases from two_bucket_test.cpp.
    Returns list of dicts: {'name': str, 'tag': str, 'enabled': bool}
    """
    content = test_cpp_path.read_text(encoding="utf-8")
    test_case_regex = re.compile(
        r'TEST_CASE\s*\(\s*(?://[^\n]*\n\s*)*"([^"]+)"\s*,\s*(?://[^\n]*\n\s*)*"\[([^\]]+)\]"\s*\)',
        re.MULTILINE,
    )
    cases = []
    for match in test_case_regex.finditer(content):
        name = match.group(1)
        tag = match.group(2)
        # All test cases inside #if defined(EXERCISM_RUN_ALL_TESTS) are enabled with EXERCISM_RUN_ALL_TESTS=ON.
        # The first test case is outside the #if block, so it is always enabled.
        cases.append({"name": name, "tag": tag, "enabled": True})
    return cases


def verify_tests_toml(tests_toml_path: Path, test_cases: list[dict], log_file=None):
    """Verify tests.toml structure and test UUID entries against test_cases in test_cpp."""
    toml_data = tomllib.loads(tests_toml_path.read_text(encoding="utf-8"))
    log(f"Verifying tests.toml: found {len(toml_data)} UUID entries in tests.toml.", log_file)
    case_uuids = {case["tag"] for case in test_cases}
    for uuid, entry in toml_data.items():
        if uuid not in case_uuids:
            raise AssertionError(f"UUID {uuid} from tests.toml not found in test file!")
        if "description" not in entry:
            raise AssertionError(f"Entry {uuid} missing 'description' field in tests.toml!")
    log(f"All {len(toml_data)} entries in tests.toml correctly match test cases.", log_file)


def run_two_bucket_check(
    exercise_dir: Path,
    file_overrides: dict[str, str] = None,
    test_filter: str = None,
    log_file=None,
) -> dict:
    """
    Core runner function:
    1. Parse .meta/config.json for files.solution, files.test, files.example
    2. Copy exercise into TemporaryDirectory() under an exercise-named folder
    3. Substitute reference files (or overrides) into learner solution paths
    4. Run cmake configure, build, and Catch2 test executable
    5. Clean up temp dir and verify cleanup
    6. Return result summary dict with returncodes, outputs, parsed stats, and status
    """
    # 1. Parse config.json
    config_file = exercise_dir / ".meta" / "config.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]

    exercise_name = exercise_dir.name
    temp_dir_obj = tempfile.TemporaryDirectory()
    temp_root = Path(temp_dir_obj.name)
    temp_exercise = temp_root / exercise_name

    try:
        # 2. Copy exercise into temp directory
        shutil.copytree(exercise_dir, temp_exercise)

        # 3. Substitute reference files or overrides
        if file_overrides:
            for rel_path, content in file_overrides.items():
                target_file = temp_exercise / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content, encoding="utf-8")
        else:
            # Substitute default example files
            # config.json: example: [".meta/example.cpp", ".meta/example.h"], solution: ["two_bucket.cpp", "two_bucket.h"]
            # Match by file extension or name
            for sol_rel in solution_files:
                sol_path = Path(sol_rel)
                matching_ex = None
                for ex_rel in example_files:
                    ex_path = Path(ex_rel)
                    if ex_path.suffix == sol_path.suffix:
                        matching_ex = ex_rel
                        break
                if matching_ex:
                    shutil.copy2(temp_exercise / matching_ex, temp_exercise / sol_rel)
                else:
                    raise FileNotFoundError(f"No matching example file found for solution file: {sol_rel}")

        # 4. Run cmake configure
        cmake_config_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        log(f"Running cmake configure: {' '.join(cmake_config_cmd)}", log_file)
        res_config = subprocess.run(
            cmake_config_cmd,
            cwd=temp_exercise,
            capture_output=True,
            text=True,
        )
        if res_config.returncode != 0:
            return {
                "success": False,
                "stage": "cmake_config",
                "returncode": res_config.returncode,
                "stdout": res_config.stdout,
                "stderr": res_config.stderr,
                "executed_cases": 0,
                "all_passed": False,
            }

        # Run cmake build (building target directly)
        cmake_build_cmd = ["cmake", "--build", "build", "--target", exercise_name]
        log(f"Running cmake build: {' '.join(cmake_build_cmd)}", log_file)
        res_build = subprocess.run(
            cmake_build_cmd,
            cwd=temp_exercise,
            capture_output=True,
            text=True,
        )
        if res_build.returncode != 0:
            return {
                "success": False,
                "stage": "cmake_build",
                "returncode": res_build.returncode,
                "stdout": res_build.stdout,
                "stderr": res_build.stderr,
                "executed_cases": 0,
                "all_passed": False,
            }

        # Locate executable
        test_exe = temp_exercise / "build" / exercise_name
        if not test_exe.exists():
            test_exe = temp_exercise / "build" / "Debug" / exercise_name
        if not test_exe.exists():
            raise FileNotFoundError(f"Test executable {exercise_name} not found in build directory")

        # Run Catch2 test executable
        test_cmd = [str(test_exe)]
        if test_filter:
            test_cmd.append(test_filter)
        log(f"Running test executable: {' '.join(test_cmd)}", log_file)
        res_test = subprocess.run(
            test_cmd,
            cwd=temp_exercise,
            capture_output=True,
            text=True,
        )

        test_stats = parse_catch2_output(res_test.stdout)

        # Failure condition:
        # non-zero child exit, assertion failure, or zero-test run (executed_cases == 0)
        has_failure = (
            res_test.returncode != 0
            or test_stats["failed_cases"] > 0
            or test_stats["failed_assertions"] > 0
            or test_stats["executed_cases"] == 0
            or not test_stats["all_passed"]
        )

        return {
            "success": not has_failure,
            "stage": "test_execution",
            "returncode": res_test.returncode,
            "stdout": res_test.stdout,
            "stderr": res_test.stderr,
            "executed_cases": test_stats["executed_cases"],
            "failed_cases": test_stats["failed_cases"],
            "passed_cases": test_stats["passed_cases"],
            "total_assertions": test_stats["total_assertions"],
            "passed_assertions": test_stats["passed_assertions"],
            "failed_assertions": test_stats["failed_assertions"],
            "all_passed": test_stats["all_passed"],
            "no_tests_ran": test_stats["no_tests_ran"],
        }

    finally:
        # Ensure temporary directory is cleaned up
        temp_dir_obj.cleanup()
        assert not temp_root.exists(), f"Temporary directory {temp_root} was not cleaned up!"


def assert_hashes_unchanged(initial_hashes: dict[str, str], stage_name: str, log_file=None):
    """Re-hash exercise directory and assert SHA-256 hashes match initial hashes."""
    current_hashes = compute_dir_hashes(EXERCISE_DIR)
    if current_hashes != initial_hashes:
        diff_keys = set(initial_hashes.keys()) ^ set(current_hashes.keys())
        mismatched = [k for k in initial_hashes if k in current_hashes and initial_hashes[k] != current_hashes[k]]
        err_msg = f"Learner files modified after {stage_name}! Diff keys: {diff_keys}, Mismatched: {mismatched}"
        log(f"ERROR: {err_msg}", log_file)
        raise AssertionError(err_msg)
    log(f"Assertion passed: all {len(initial_hashes)} files unchanged after {stage_name}.", log_file)


def get_tool_version(cmd: list[str]) -> str:
    """Run command and return first output lines."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
        return out
    except Exception as e:
        return f"Error retrieving version: {e}"


def main():
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_LOG_PATH, "w", encoding="utf-8") as log_file:
        log("=== Two-Bucket Test Verification Run ===", log_file)

        # 1. Evidence logging: Tool versions
        log("\n--- Tool Versions ---", log_file)
        log(f"cmake version:\n{get_tool_version(['cmake', '--version'])}", log_file)
        log(f"c++ version:\n{get_tool_version(['c++', '--version'])}", log_file)
        log(f"python3 version:\n{get_tool_version(['python3', '--version'])}", log_file)

        # 2. Pre-Run Hashing
        log("\n--- Pre-Run Hashing ---", log_file)
        initial_hashes = compute_dir_hashes(EXERCISE_DIR)
        for rel_path, h in initial_hashes.items():
            log(f"  {rel_path}: {h}", log_file)

        # 3. Verify .meta/tests.toml and test cases in two_bucket_test.cpp
        log("\n--- Metadata & Test Suite Verification ---", log_file)
        test_cases = extract_enabled_test_cases(TEST_CPP_PATH)
        log(f"Parsed {len(test_cases)} test cases from {TEST_CPP_PATH.name}:", log_file)
        for idx, tc in enumerate(test_cases, 1):
            log(f"  [{idx}] {tc['name']} ({tc['tag']})", log_file)
        verify_tests_toml(TESTS_TOML_PATH, test_cases, log_file)

        overall_success = True

        # ==========================================
        # Scenario A: Real Reference (Expected Pass)
        # ==========================================
        log("\n=== Scenario A: Real Reference (Expected Pass) ===", log_file)
        res_a = run_two_bucket_check(EXERCISE_DIR, log_file=log_file)
        log(f"Scenario A result: success={res_a['success']}, exit_code={res_a['returncode']}, executed_cases={res_a['executed_cases']}", log_file)
        log(f"Catch2 Output:\n{res_a['stdout']}", log_file)

        try:
            assert res_a["success"] is True, f"Scenario A expected success, got {res_a}"
            assert res_a["returncode"] == 0, f"Scenario A expected exit code 0, got {res_a['returncode']}"
            assert res_a["executed_cases"] == len(test_cases), (
                f"Scenario A expected {len(test_cases)} executed cases, got {res_a['executed_cases']}"
            )
            assert res_a["all_passed"] is True, "Scenario A expected all tests passed"
            log("Scenario A passed all assertions successfully.", log_file)
        except AssertionError as e:
            log(f"Scenario A assertion failed: {e}", log_file)
            overall_success = False

        assert_hashes_unchanged(initial_hashes, "Scenario A", log_file)

        # ==========================================
        # Scenario B: Deliberately Failing Reference (Expected Failure)
        # ==========================================
        log("\n=== Scenario B: Deliberately Failing Reference (Expected Failure) ===", log_file)
        broken_cpp = """#include "two_bucket.h"
two_bucket::measure_result two_bucket::measure(int, int, int, bucket_id) {
    // Deliberately broken values to fail assertions
    return {999, bucket_id::one, 999};
}
"""
        res_b = run_two_bucket_check(
            EXERCISE_DIR,
            file_overrides={"two_bucket.cpp": broken_cpp},
            log_file=log_file,
        )
        log(f"Scenario B result: success={res_b['success']}, exit_code={res_b['returncode']}, executed_cases={res_b['executed_cases']}", log_file)
        log(f"Catch2 Output:\n{res_b['stdout']}", log_file)

        try:
            assert res_b["success"] is False, f"Scenario B expected failure, got success={res_b['success']}"
            assert res_b["returncode"] != 0, f"Scenario B expected non-zero exit code, got {res_b['returncode']}"
            assert res_b["failed_cases"] > 0 or res_b["failed_assertions"] > 0, (
                f"Scenario B expected Catch2 failures, got failed_cases={res_b['failed_cases']}, failed_assertions={res_b['failed_assertions']}"
            )
            log("Scenario B correctly detected Catch2 failure and returned non-zero status.", log_file)
        except AssertionError as e:
            log(f"Scenario B assertion failed: {e}", log_file)
            overall_success = False

        assert_hashes_unchanged(initial_hashes, "Scenario B", log_file)

        # ==========================================
        # Scenario C: Empty Test Selection / Zero-Test Run (Expected Failure)
        # ==========================================
        log("\n=== Scenario C: Empty Test Selection / Zero-Test Run (Expected Failure) ===", log_file)
        res_c = run_two_bucket_check(
            EXERCISE_DIR,
            test_filter="nonexistent_test_case_xyz",
            log_file=log_file,
        )
        log(f"Scenario C result: success={res_c['success']}, exit_code={res_c['returncode']}, executed_cases={res_c['executed_cases']}", log_file)
        log(f"Catch2 Output:\n{res_c['stdout']}", log_file)

        try:
            assert res_c["success"] is False, f"Scenario C expected failure due to zero tests executed, got {res_c}"
            assert res_c["executed_cases"] == 0, f"Scenario C expected 0 executed cases, got {res_c['executed_cases']}"
            assert res_c["no_tests_ran"] is True, "Scenario C expected 'no_tests_ran' flag to be True"
            log("Scenario C correctly detected zero-test run and propagated failure status.", log_file)
        except AssertionError as e:
            log(f"Scenario C assertion failed: {e}", log_file)
            overall_success = False

        assert_hashes_unchanged(initial_hashes, "Scenario C", log_file)

        # Summary
        log("\n=== Final Verification Summary ===", log_file)
        if overall_success:
            log("ALL SCENARIOS AND ASSERTIONS PASSED SUCCESSFULLY.", log_file)
        else:
            log("ONE OR MORE VERIFICATION ASSERTIONS FAILED.", log_file)

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
