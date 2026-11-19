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
    work_dir = os.path.join(root_dir, "work", "R20-T053")
    os.makedirs(work_dir, exist_ok=True)

    exercise_rel = os.path.join("exercises", "practice", "kindergarten-garden")
    exercise_abs = os.path.join(root_dir, exercise_rel)
    config_json_path = os.path.join(exercise_abs, ".meta", "config.json")

    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    log(f"Starting check for {exercise_rel}")

    # Read config.json to resolve paths
    with open(config_json_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    log(f"Loaded config.json: {config_data.get('files', {})}")

    solution_files = config_data.get("files", {}).get("solution", [])
    test_files = config_data.get("files", {}).get("test", [])
    example_files = config_data.get("files", {}).get("example", [])

    log(f"Solution files: {solution_files}")
    log(f"Test files: {test_files}")
    log(f"Example files: {example_files}")

    assert test_files, "No test files defined in config.json"
    assert solution_files, "No solution files defined in config.json"
    assert example_files, "No example files defined in config.json"

    # Find example.cpp and target solution .cpp path
    example_cpp_rel = next((f for f in example_files if f.endswith(".cpp")), None)
    solution_cpp_rel = next((f for f in solution_files if f.endswith(".cpp")), None)
    assert example_cpp_rel, "example.cpp not found in example files"
    assert solution_cpp_rel, "solution .cpp not found in solution files"

    # Map header files if present
    example_h_rel = next((f for f in example_files if f.endswith(".h")), None)
    solution_h_rel = next((f for f in solution_files if f.endswith(".h")), None)

    # Mutation strings documented in maintenance.md
    target_str = "const int first_plant_index = 2 * (student.at(0) - 'A');"
    mutant_str = "const int first_plant_index = 1 * (student.at(0) - 'A');"

    # Create two separate temporary directories and copy the exercise into both
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        dir1 = os.path.join(tmpdir1, "kindergarten-garden")
        dir2 = os.path.join(tmpdir2, "kindergarten-garden")

        log(f"Copying {exercise_abs} to {dir1}")
        shutil.copytree(exercise_abs, dir1)
        log(f"Copying {exercise_abs} to {dir2}")
        shutil.copytree(exercise_abs, dir2)

        # -------------------------------------------------------------
        # Part 1: Original Test
        # -------------------------------------------------------------
        log("\n=== Running Original Test in Dir 1 ===")
        # Substitute example files into solution path
        shutil.copyfile(os.path.join(dir1, example_cpp_rel), os.path.join(dir1, solution_cpp_rel))
        if example_h_rel and solution_h_rel:
            shutil.copyfile(os.path.join(dir1, example_h_rel), os.path.join(dir1, solution_h_rel))

        # cmake configure
        cmd_cmake_configure = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        log(f"Running command: {' '.join(cmd_cmake_configure)}")
        res_config = subprocess.run(cmd_cmake_configure, cwd=dir1, capture_output=True, text=True)
        log("--- cmake configure stdout ---")
        log(res_config.stdout)
        log("--- cmake configure stderr ---")
        log(res_config.stderr)
        assert res_config.returncode == 0, f"cmake configure failed with returncode {res_config.returncode}"

        # cmake build target
        # Specifying --target kindergarten-garden ensures the executable is compiled.
        cmd_cmake_build = ["cmake", "--build", "build", "--target", "kindergarten-garden"]
        log(f"Running command: {' '.join(cmd_cmake_build)}")
        res_build = subprocess.run(cmd_cmake_build, cwd=dir1, capture_output=True, text=True)
        log("--- cmake build stdout ---")
        log(res_build.stdout)
        log("--- cmake build stderr ---")
        log(res_build.stderr)
        assert res_build.returncode == 0, f"cmake build failed with returncode {res_build.returncode}"

        # run test executable
        exe_path1 = os.path.join(dir1, "build", "kindergarten-garden")
        assert os.path.exists(exe_path1), f"Test executable not found at {exe_path1}"

        cmd_run_test1 = [exe_path1, "-s"]
        log(f"Running command: {' '.join(cmd_run_test1)}")
        res_test1 = subprocess.run(cmd_run_test1, cwd=dir1, capture_output=True, text=True)
        log("--- original test execution stdout ---")
        log(res_test1.stdout)
        log("--- original test execution stderr ---")
        log(res_test1.stderr)

        # Assert child return code is zero
        assert res_test1.returncode == 0, f"Original test failed with returncode {res_test1.returncode}"

        # Check for zero-test run
        match_test_summary1 = re.search(r"test cases:\s+(\d+)", res_test1.stdout) or \
                              re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test1.stdout)
        assert match_test_summary1, "Failed to parse test execution summary in original test"
        if "assertions" in match_test_summary1.group(0):
            num_test_cases1 = int(match_test_summary1.group(2))
            num_assertions1 = int(match_test_summary1.group(1))
        else:
            num_test_cases1 = int(match_test_summary1.group(1))
            m_asserts = re.search(r"assertions:\s+(\d+)", res_test1.stdout)
            num_assertions1 = int(m_asserts.group(1)) if m_asserts else 1

        log(f"Original test summary: {num_test_cases1} test cases, {num_assertions1} assertions")
        assert num_test_cases1 > 0, "Zero test cases were run in original test!"
        assert num_assertions1 > 0, "Zero assertions were run in original test!"

        # Explicitly verify that required cases are present and pass
        required_cases = [
            "garden with single student",
            "different garden with single student",
            "garden with two students"
        ]
        for case in required_cases:
            assert case in res_test1.stdout, f"Required test case '{case}' was not executed!"
            # Catch -s reports test cases with PASSED assertions when successful
            case_pattern = re.compile(rf"-\s*\n\s*{re.escape(case)}\s*\n.*?PASSED:", re.DOTALL)
            assert case_pattern.search(res_test1.stdout), f"Required test case '{case}' did not pass successfully!"
            log(f"Verified required test case present and passed in original: '{case}'")

        # -------------------------------------------------------------
        # Part 2: Mutant Test
        # -------------------------------------------------------------
        log("\n=== Running Mutant Test in Dir 2 ===")
        # Read example.cpp and apply exact string mutation using replace()
        src_example_cpp = os.path.join(dir2, example_cpp_rel)
        with open(src_example_cpp, "r", encoding="utf-8") as f:
            original_code = f.read()

        assert target_str in original_code, f"Target mutation string '{target_str}' not found in {example_cpp_rel}"
        mutated_code = original_code.replace(target_str, mutant_str)
        assert mutated_code != original_code, "Mutation replace() had no effect"

        # Write mutated code to solution path
        dest_solution_cpp = os.path.join(dir2, solution_cpp_rel)
        with open(dest_solution_cpp, "w", encoding="utf-8") as f:
            f.write(mutated_code)

        if example_h_rel and solution_h_rel:
            shutil.copyfile(os.path.join(dir2, example_h_rel), os.path.join(dir2, solution_h_rel))

        # cmake configure
        log(f"Running command: {' '.join(cmd_cmake_configure)}")
        res_config2 = subprocess.run(cmd_cmake_configure, cwd=dir2, capture_output=True, text=True)
        log("--- mutant cmake configure stdout ---")
        log(res_config2.stdout)
        log("--- mutant cmake configure stderr ---")
        log(res_config2.stderr)
        assert res_config2.returncode == 0, f"mutant cmake configure failed with returncode {res_config2.returncode}"

        # cmake build target (building target 'kindergarten-garden' compiles the mutant binary cleanly)
        cmd_cmake_build2 = ["cmake", "--build", "build", "--target", "kindergarten-garden"]
        log(f"Running command: {' '.join(cmd_cmake_build2)}")
        res_build2 = subprocess.run(cmd_cmake_build2, cwd=dir2, capture_output=True, text=True)
        log("--- mutant cmake build stdout ---")
        log(res_build2.stdout)
        log("--- mutant cmake build stderr ---")
        log(res_build2.stderr)
        assert res_build2.returncode == 0, f"mutant cmake build failed with returncode {res_build2.returncode}"

        # run test executable
        exe_path2 = os.path.join(dir2, "build", "kindergarten-garden")
        assert os.path.exists(exe_path2), f"Test executable not found at {exe_path2}"

        cmd_run_test2 = [exe_path2, "-s"]
        log(f"Running command: {' '.join(cmd_run_test2)}")
        res_test2 = subprocess.run(cmd_run_test2, cwd=dir2, capture_output=True, text=True)
        log("--- mutant test execution stdout ---")
        log(res_test2.stdout)
        log("--- mutant test execution stderr ---")
        log(res_test2.stderr)

        # Assert that the test executable fails (returns non-zero exit code)
        assert res_test2.returncode != 0, "Mutant test unexpectedly passed with returncode 0!"
        log(f"Confirmed mutant test failed as expected with returncode {res_test2.returncode}")

        # Check for zero-test run on mutant
        match_test_summary2 = re.search(r"test cases:\s+(\d+)", res_test2.stdout) or \
                              re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test2.stdout)
        assert match_test_summary2, "Failed to parse test execution summary in mutant test"
        if "assertions" in match_test_summary2.group(0):
            num_test_cases2 = int(match_test_summary2.group(2))
        else:
            num_test_cases2 = int(match_test_summary2.group(1))

        log(f"Mutant test summary: {num_test_cases2} test cases executed")
        assert num_test_cases2 > 0, "Zero test cases were run in mutant test!"

        # Ensure that 'garden with two students' is among the failed cases
        assert "garden with two students" in res_test2.stdout, "'garden with two students' not in mutant test output"
        # Confirm 'garden with two students' failed
        case_failed_pattern = re.compile(rf"-\s*\n\s*garden with two students\s*\n.*?FAILED:", re.DOTALL)
        assert case_failed_pattern.search(res_test2.stdout), "'garden with two students' did not fail as expected!"
        log("Verified 'garden with two students' failed and rejected the mutant.")

    # Save all outputs from both original and mutant runs to work/R20-T053/check_output.log
    output_log_file = os.path.join(work_dir, "check_output.log")
    with open(output_log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")
    log(f"\nSaved all outputs to {output_log_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Check failed: {e}", file=sys.stderr)
        work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        with open(os.path.join(work_dir, "error.log"), "a", encoding="utf-8") as f:
            f.write(f"Exception: {e}\n")
        sys.exit(1)
