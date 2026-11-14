#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

def get_toml_counts(toml_path):
    if not os.path.exists(toml_path):
        return {"included": 0, "excluded": 0, "total": 0}
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    included = 0
    excluded = 0
    for key, val in data.items():
        if isinstance(val, dict):
            # An omitted `include` key implies inclusion (include = true by default)
            if val.get("include", True) is False:
                excluded += 1
            else:
                included += 1
    return {"included": included, "excluded": excluded, "total": included + excluded}

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    work_dir = os.path.join(root_dir, "work", "R20-T051")
    os.makedirs(work_dir, exist_ok=True)

    exercise_rel = os.path.join("exercises", "practice", "rotational-cipher")
    exercise_abs = os.path.join(root_dir, exercise_rel)
    config_json_path = os.path.join(exercise_abs, ".meta", "config.json")
    tests_toml_path = os.path.join(exercise_abs, ".meta", "tests.toml")

    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    log(f"Starting check for {exercise_rel}")

    # Record included/excluded counts before
    counts_before = get_toml_counts(tests_toml_path)
    log(f"Counts before: {counts_before}")

    # Read config.json
    with open(config_json_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    log(f"Loaded config.json: {config_data.get('files', {})}")

    solution_files = config_data.get("files", {}).get("solution", [])
    example_files = config_data.get("files", {}).get("example", [])

    # Map example files to solution files
    file_substitutions = []
    for ex in example_files:
        ex_base = os.path.basename(ex)
        target = None
        for sol in solution_files:
            sol_base = os.path.basename(sol)
            if ex_base.replace("example", "rotational_cipher") == sol_base:
                target = sol
                break
        if not target and solution_files:
            target = solution_files[0]
        file_substitutions.append((ex, target))

    log(f"File substitutions planned: {file_substitutions}")

    # Use a temporary directory to build and run tests
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = os.path.join(tmpdir, "rotational-cipher")
        log(f"Copying {exercise_abs} to {dest_dir}")
        shutil.copytree(exercise_abs, dest_dir)

        # Substitute example.cpp (and headers if defined) into solution location
        for ex, sol in file_substitutions:
            src_path = os.path.join(dest_dir, ex)
            dest_path = os.path.join(dest_dir, sol)
            log(f"Substituting {src_path} -> {dest_path}")
            shutil.copyfile(src_path, dest_path)

        # Run cmake configure
        cmd_cmake_configure = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        log(f"Running command: {' '.join(cmd_cmake_configure)}")
        res_config = subprocess.run(cmd_cmake_configure, cwd=dest_dir, capture_output=True, text=True)
        log("--- cmake configure stdout ---")
        log(res_config.stdout)
        log("--- cmake configure stderr ---")
        log(res_config.stderr)
        assert res_config.returncode == 0, f"cmake configure failed with returncode {res_config.returncode}"

        # Run cmake build
        cmd_cmake_build = ["cmake", "--build", "build"]
        log(f"Running command: {' '.join(cmd_cmake_build)}")
        res_build = subprocess.run(cmd_cmake_build, cwd=dest_dir, capture_output=True, text=True)
        log("--- cmake build stdout ---")
        log(res_build.stdout)
        log("--- cmake build stderr ---")
        log(res_build.stderr)
        assert res_build.returncode == 0, f"cmake build failed with returncode {res_build.returncode}"

        # Run generated test executable
        exe_path = os.path.join(dest_dir, "build", "rotational-cipher")
        assert os.path.exists(exe_path), f"Test executable not found at {exe_path}"

        # Run with -s to show individual test case results and assertions
        cmd_run_test = [exe_path, "-s"]
        log(f"Running command: {' '.join(cmd_run_test)}")
        res_test = subprocess.run(cmd_run_test, cwd=dest_dir, capture_output=True, text=True)
        log("--- test execution stdout ---")
        log(res_test.stdout)
        log("--- test execution stderr ---")
        log(res_test.stderr)
        assert res_test.returncode == 0, f"Test executable failed with returncode {res_test.returncode}"

        # Check for zero-test run
        match_test_summary = re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test.stdout)
        assert match_test_summary, "Failed to parse test execution summary"
        num_assertions = int(match_test_summary.group(1))
        num_test_cases = int(match_test_summary.group(2))
        log(f"Test summary parsed: {num_test_cases} test cases, {num_assertions} assertions")
        assert num_test_cases > 0, "Zero test cases were run!"
        assert num_assertions > 0, "Zero test assertions were run!"

        # Assert specific cases pass
        required_cases = [
            "rotate a by 0, same output as input",
            "rotate a by 1",
            "rotate a by 26, same output as input"
        ]

        for case in required_cases:
            assert case in res_test.stdout, f"Required test case '{case}' was not executed!"
            # Ensure it passed in Catch output
            # In Catch, a test case section begins with "--- \n <case> \n ---"
            # and ends without failures, or has PASSED assertions
            log(f"Verified required test case passed: '{case}'")

    # Record counts after
    counts_after = get_toml_counts(tests_toml_path)
    log(f"Counts after: {counts_after}")
    assert counts_before == counts_after, f"Counts changed: before={counts_before}, after={counts_after}"

    # Save output to work/R20-T051/
    output_log_file = os.path.join(work_dir, "check_output.log")
    with open(output_log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    log(f"Saved all outputs to {output_log_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Check failed: {e}", file=sys.stderr)
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        with open(os.path.join(work_dir, "error.log"), "a", encoding="utf-8") as f:
            f.write(f"Exception: {e}\n")
        sys.exit(1)
