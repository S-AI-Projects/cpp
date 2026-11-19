#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    exercise_rel_path = os.path.join("exercises", "practice", "pascals-triangle")
    exercise_dir = os.path.join(repo_root, exercise_rel_path)
    config_file = os.path.join(exercise_dir, ".meta", "config.json")

    log_output_path = os.path.join(repo_root, "work", "R20-T054", "check_output.log")
    os.makedirs(os.path.dirname(log_output_path), exist_ok=True)

    log_lines = []

    def record_and_print(msg):
        print(msg)
        log_lines.append(str(msg))

    record_and_print("=== Starting verification for pascals-triangle ===")
    record_and_print(f"Reading configuration from: {config_file}")

    if not os.path.isfile(config_file):
        record_and_print(f"ERROR: config.json not found at {config_file}")
        with open(log_output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    solution_files = config_data.get("files", {}).get("solution", [])
    example_files = config_data.get("files", {}).get("example", [])

    record_and_print(f"Resolved solution files from config: {solution_files}")
    record_and_print(f"Resolved example files from config: {example_files}")

    # Map example files to solution files by extension (.cpp -> .cpp, .h -> .h)
    substitutions = []
    for ex_file in example_files:
        ex_base = os.path.basename(ex_file)
        _, ex_ext = os.path.splitext(ex_base)
        matching_sol = [s for s in solution_files if s.endswith(ex_ext)]
        if matching_sol:
            substitutions.append((ex_file, matching_sol[0]))
        else:
            record_and_print(f"WARNING: Could not find matching solution file for {ex_file}")

    record_and_print(f"File substitution mappings: {substitutions}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise_dir = os.path.join(tmpdir, "pascals-triangle")
        record_and_print(f"Creating temporary directory and copying exercise: {tmp_exercise_dir}")
        shutil.copytree(exercise_dir, tmp_exercise_dir)

        # Substitute refactored example files into the solution paths
        for src_rel, dest_rel in substitutions:
            src_path = os.path.join(tmp_exercise_dir, src_rel)
            dest_path = os.path.join(tmp_exercise_dir, dest_rel)
            record_and_print(f"Substituted: {src_rel} -> {dest_rel}")
            shutil.copyfile(src_path, dest_path)

        # Step 1: Run cmake configure
        cmake_config_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        record_and_print(f"\n--- Running CMake Configure: {' '.join(cmake_config_cmd)} ---")
        proc_config = subprocess.run(
            cmake_config_cmd,
            cwd=tmp_exercise_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        record_and_print(proc_config.stdout)
        if proc_config.returncode != 0:
            record_and_print(f"ERROR: CMake configure exited with code {proc_config.returncode}")
            with open(log_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
            sys.exit(proc_config.returncode)

        # Step 2: Run cmake build
        cmake_build_cmd = ["cmake", "--build", "build"]
        record_and_print(f"\n--- Running CMake Build: {' '.join(cmake_build_cmd)} ---")
        proc_build = subprocess.run(
            cmake_build_cmd,
            cwd=tmp_exercise_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        record_and_print(proc_build.stdout)
        if proc_build.returncode != 0:
            record_and_print(f"ERROR: CMake build exited with code {proc_build.returncode}")
            with open(log_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
            sys.exit(proc_build.returncode)

        # Step 3: Run the generated test executable
        test_exe_path = os.path.join(tmp_exercise_dir, "build", "pascals-triangle")
        if not os.path.isfile(test_exe_path):
            record_and_print(f"ERROR: Test executable not found at {test_exe_path}")
            with open(log_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
            sys.exit(1)

        test_run_cmd = [test_exe_path, "-s"]
        record_and_print(f"\n--- Running Test Executable: {' '.join(test_run_cmd)} ---")
        proc_test = subprocess.run(
            test_run_cmd,
            cwd=tmp_exercise_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        record_and_print(proc_test.stdout)
        if proc_test.returncode != 0:
            record_and_print(f"ERROR: Test execution exited with code {proc_test.returncode}")
            with open(log_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
            sys.exit(proc_test.returncode)

        # Step 4: Validate test cases and assertions
        test_output = proc_test.stdout

        # Extract total test cases executed
        total_test_cases = 0
        match_all_passed = re.search(r"All tests passed \(.*in (\d+) test cases?\)", test_output)
        if match_all_passed:
            total_test_cases = int(match_all_passed.group(1))
        else:
            match_summary = re.search(r"test cases:\s*(\d+)\s*\|\s*(\d+)\s*passed", test_output)
            if match_summary:
                total_test_cases = int(match_summary.group(2))

        record_and_print(f"\nTotal test cases reported: {total_test_cases}")

        # Fail if zero tests were executed
        if total_test_cases == 0:
            record_and_print("ASSERTION FAILURE: Zero tests were executed!")
            with open(log_output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines) + "\n")
            sys.exit(1)

        # Validate that specific cases 'zero_rows', 'single_row', and 'two_rows' are present and pass
        required_cases = ["zero_rows", "single_row", "two_rows"]
        for case in required_cases:
            pattern = re.compile(rf"-{{10,}}\s*\n{case}\s*\n-{{10,}}.*?PASSED:", re.DOTALL)
            if not pattern.search(test_output):
                record_and_print(f"ASSERTION FAILURE: Test case '{case}' was not found or did not pass!")
                with open(log_output_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(log_lines) + "\n")
                sys.exit(1)
            record_and_print(f"ASSERTION SUCCESS: Test case '{case}' is present and passed.")

        record_and_print("\nAll validations passed successfully!")

    # Write all captured outputs to log file
    with open(log_output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")

    print(f"\nSaved check output log to {log_output_path}")

if __name__ == "__main__":
    main()
