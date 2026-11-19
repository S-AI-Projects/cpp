#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def run_isolated_build_and_test(exercise_dir, run_id):
    temp_dir = tempfile.mkdtemp(prefix=f"leap_run_{run_id}_")
    try:
        temp_exercise = os.path.join(temp_dir, "leap")
        shutil.copytree(exercise_dir, temp_exercise, ignore=shutil.ignore_patterns("build"))

        # Load config.json
        with open(os.path.join(temp_exercise, ".meta/config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)

        # Substitute reference solution (.meta/example.h -> leap.h)
        example_h = os.path.join(temp_exercise, ".meta/example.h")
        target_h = os.path.join(temp_exercise, "leap.h")
        shutil.copy2(example_h, target_h)

        # Clear leap.cpp since example.h is header-only
        cpp_stub = os.path.join(temp_exercise, "leap.cpp")
        if os.path.exists(cpp_stub):
            with open(cpp_stub, "w", encoding="utf-8") as f:
                f.write('// Header-only solution in leap.h\n')

        # CMake configure & build
        build_dir = os.path.join(temp_exercise, "build")
        cfg_res = subprocess.run(
            ["cmake", "-S", temp_exercise, "-B", build_dir, "-DEXERCISM_RUN_ALL_TESTS=ON"],
            capture_output=True, text=True
        )
        if cfg_res.returncode != 0:
            raise RuntimeError(f"CMake configure failed in run {run_id}: {cfg_res.stderr}")

        bld_res = subprocess.run(
            ["cmake", "--build", build_dir],
            capture_output=True, text=True
        )
        if bld_res.returncode != 0:
            raise RuntimeError(f"CMake build failed in run {run_id}: {bld_res.stderr}")

        # Run tests
        exe = os.path.join(build_dir, "leap")
        test_res = subprocess.run([exe], capture_output=True, text=True)
        if test_res.returncode != 0:
            raise RuntimeError(f"Tests failed in run {run_id} with exit code {test_res.returncode}")

        # Read the test source
        with open(os.path.join(temp_exercise, "leap_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()

        return {
            "exit_code": test_res.returncode,
            "stdout": test_res.stdout,
            "test_src": test_src
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def verify_leap():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/leap")
    logs = []
    logs.append("=== R20-T002 Leap Test-Generation Round-Trip Check ===")

    # 1. Verify learner stubs remain unsolved in working tree
    for stub_name in ["leap.cpp", "leap.h"]:
        stub_path = os.path.join(exercise_dir, stub_name)
        with open(stub_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "year % 4" not in content and "year % 400" not in content, f"Stub {stub_name} should remain unsolved"
    logs.append("Verified learner stubs in working tree are unsolved.")

    # 2. Check documentation exists
    doc_path = os.path.join(repo_root, "docs/maintenance/leap.md")
    assert os.path.isfile(doc_path), f"Documentation missing: {doc_path}"
    logs.append(f"Found maintenance documentation at {doc_path}")

    # 3. Check named cases exist in test source
    named_cases = [
        "not_divisible_by_4",
        "divisible_by_2_not_divisible_by_4",
        "divisible_by_4_not_divisible_by_100"
    ]
    with open(os.path.join(exercise_dir, "leap_test.cpp"), "r", encoding="utf-8") as f:
        orig_test_src = f.read()
    for case in named_cases:
        assert case in orig_test_src, f"Named case {case} missing from leap_test.cpp"
        logs.append(f"Anchor case confirmed: {case}")

    # 4. Run two isolated scratch builds to verify reproducibility
    run1 = run_isolated_build_and_test(exercise_dir, 1)
    run2 = run_isolated_build_and_test(exercise_dir, 2)

    assert run1["test_src"] == run2["test_src"], "Test source differed between independent scratch runs"
    assert run1["exit_code"] == 0 and run2["exit_code"] == 0, "Test runs failed"

    # Verify executed test count from Catch2 summary
    m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", run1["stdout"])
    assert m is not None, "Could not parse Catch2 summary"
    num_tests = int(m.group(2))
    assert num_tests >= 6, f"Expected at least 6 test cases, got {num_tests}"
    logs.append(f"Reproducible test execution confirmed across two clean scratch runs: {num_tests} tests passed.")

    return logs

if __name__ == "__main__":
    try:
        results = verify_leap()
        print("\n".join(results))
        print("[✓] R20-T002 check passed.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] R20-T002 check failed: {e}", file=sys.stderr)
        sys.exit(1)
