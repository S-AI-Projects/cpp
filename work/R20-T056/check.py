#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    work_dir = os.path.join(root_dir, "work", "R20-T056")
    os.makedirs(work_dir, exist_ok=True)

    exercise_rel = os.path.join("exercises", "practice", "allergies")
    exercise_abs = os.path.join(root_dir, exercise_rel)
    config_json_path = os.path.join(exercise_abs, ".meta", "config.json")

    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    log(f"Starting check for {exercise_rel}")

    # Read exercises/practice/allergies/.meta/config.json
    if not os.path.exists(config_json_path):
        raise FileNotFoundError(f"Missing config.json at {config_json_path}")

    with open(config_json_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    files_config = config_data.get("files", {})
    solution_files = files_config.get("solution", [])
    example_files = files_config.get("example", [])
    test_files = files_config.get("test", [])

    log(f"Config solution files: {solution_files}")
    log(f"Config example files: {example_files}")
    log(f"Config test files: {test_files}")

    assert solution_files, "No solution files configured in config.json"
    assert example_files, "No example files configured in config.json"

    # Map example files to solution files by matching file extension / base pattern
    file_substitutions = []
    for ex in example_files:
        ex_base = os.path.basename(ex)
        target = None
        for sol in solution_files:
            sol_base = os.path.basename(sol)
            if ex_base.replace("example", "allergies") == sol_base:
                target = sol
                break
        if not target:
            # Fallback matching by file extension if exact pattern does not match
            ex_ext = os.path.splitext(ex_base)[1]
            for sol in solution_files:
                if os.path.splitext(sol)[1] == ex_ext:
                    target = sol
                    break
        assert target, f"Could not map example file {ex} to a solution file in {solution_files}"
        file_substitutions.append((ex, target))

    log(f"Planned substitutions: {file_substitutions}")

    # Create temporary directory and run cmake configure, build, and test
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = os.path.join(tmpdir, "allergies")
        log(f"Copying {exercise_abs} -> {dest_dir}")
        shutil.copytree(exercise_abs, dest_dir)

        # Substitute reference solution (.meta/example.cpp and .meta/example.h) into learner solution path
        for ex, sol in file_substitutions:
            src_path = os.path.join(dest_dir, ex)
            dest_path = os.path.join(dest_dir, sol)
            log(f"Substituting reference file {src_path} -> {dest_path}")
            shutil.copyfile(src_path, dest_path)

        # 1. Run cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON
        cmd_cmake_configure = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        log(f"Running command: {' '.join(cmd_cmake_configure)}")
        res_config = subprocess.run(cmd_cmake_configure, cwd=dest_dir, capture_output=True, text=True)
        log("--- cmake configure stdout ---")
        log(res_config.stdout)
        log("--- cmake configure stderr ---")
        log(res_config.stderr)
        assert res_config.returncode == 0, f"cmake configure failed with code {res_config.returncode}"

        # 2. Run cmake --build build
        cmd_cmake_build = ["cmake", "--build", "build"]
        log(f"Running command: {' '.join(cmd_cmake_build)}")
        res_build = subprocess.run(cmd_cmake_build, cwd=dest_dir, capture_output=True, text=True)
        log("--- cmake build stdout ---")
        log(res_build.stdout)
        log("--- cmake build stderr ---")
        log(res_build.stderr)
        assert res_build.returncode == 0, f"cmake build failed with code {res_build.returncode}"

        # 3. Locate and run generated test executable
        exe_path = os.path.join(dest_dir, "build", "allergies")
        assert os.path.exists(exe_path), f"Test executable not found at {exe_path}"

        cmd_run_test = [exe_path, "-s"]
        log(f"Running command: {' '.join(cmd_run_test)}")
        res_test = subprocess.run(cmd_run_test, cwd=dest_dir, capture_output=True, text=True)
        log("--- test execution stdout ---")
        log(res_test.stdout)
        log("--- test execution stderr ---")
        log(res_test.stderr)
        assert res_test.returncode == 0, f"Test executable failed with code {res_test.returncode}"

        # 4. Report total number of executed test cases and assertions
        match_test_summary = re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test.stdout)
        assert match_test_summary, "Failed to parse test execution summary"
        num_assertions = int(match_test_summary.group(1))
        num_test_cases = int(match_test_summary.group(2))

        log(f"Total executed test cases: {num_test_cases}")
        log(f"Total assertions: {num_assertions}")

        # Check for zero-test run
        assert num_test_cases > 0, "Zero test cases were run!"
        assert num_assertions > 0, "Zero test assertions were run!"

        # 5. Explicitly assert required cases are present and pass
        required_cases = [
            "testing for eggs allergy -> not allergic to anything",
            "testing for eggs allergy -> allergic only to eggs",
            "testing for eggs allergy -> allergic to eggs and something else"
        ]

        for case in required_cases:
            assert case in res_test.stdout, f"Required test case '{case}' was not executed!"
            log(f"Explicit assertion passed: '{case}' is present and executed.")

        # Ensure no failures in test output
        assert "All tests passed" in res_test.stdout or "failed" not in res_test.stdout.lower(), \
            "Detected test failures in output"

    # Save all outputs to work/R20-T056/check_output.log
    output_log_file = os.path.join(work_dir, "check_output.log")
    with open(output_log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    log(f"Successfully saved all output logs to {output_log_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Check script failed with exception: {e}", file=sys.stderr)
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        work_dir = os.path.join(root_dir, "work", "R20-T056")
        os.makedirs(work_dir, exist_ok=True)
        with open(os.path.join(work_dir, "error.log"), "a", encoding="utf-8") as f:
            f.write(f"Exception: {e}\n")
        sys.exit(1)
