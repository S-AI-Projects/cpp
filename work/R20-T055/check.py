#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.abspath(os.path.dirname(__file__))
    log_file_path = os.path.join(out_dir, "check_output.log")

    os.makedirs(out_dir, exist_ok=True)
    log_file = open(log_file_path, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()

    def run_cmd(cmd, cwd):
        log(f"=== Running command: {' '.join(cmd)} in {cwd} ===")
        res = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        log(res.stdout)
        log(f"=== Return code: {res.returncode} ===\n")
        if res.returncode != 0:
            log(f"ERROR: Command failed with return code {res.returncode}")
            sys.exit(res.returncode)
        return res

    try:
        exercise_rel_path = os.path.join("exercises", "practice", "binary-search-tree")
        exercise_src_dir = os.path.join(repo_root, exercise_rel_path)
        config_path = os.path.join(exercise_src_dir, ".meta", "config.json")

        if not os.path.exists(config_path):
            log(f"ERROR: config.json not found at {config_path}")
            sys.exit(1)

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        solution_files = config.get("files", {}).get("solution", [])
        test_files = config.get("files", {}).get("test", [])
        example_files = config.get("files", {}).get("example", [])

        log(f"Resolved config files from {config_path}:")
        log(f"  solution: {solution_files}")
        log(f"  test: {test_files}")
        log(f"  example: {example_files}")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_exercise_dir = os.path.join(tmpdir, "binary-search-tree")
            log(f"Copying {exercise_src_dir} to {temp_exercise_dir}...")
            shutil.copytree(exercise_src_dir, temp_exercise_dir)

            # Substitute reference solution (.meta/example.h and .meta/example.cpp if applicable)
            # into learner solution paths.
            for sol_rel in solution_files:
                sol_ext = os.path.splitext(sol_rel)[1]  # .h or .cpp
                # Look for matching example in config or directory
                matched_example = None
                for ex_rel in example_files:
                    if os.path.splitext(ex_rel)[1] == sol_ext:
                        matched_example = ex_rel
                        break

                if not matched_example:
                    # Check if example file exists with same extension under .meta
                    candidate = os.path.join(".meta", f"example{sol_ext}")
                    if os.path.exists(os.path.join(temp_exercise_dir, candidate)):
                        matched_example = candidate

                if matched_example:
                    src_example = os.path.join(temp_exercise_dir, matched_example)
                    dest_solution = os.path.join(temp_exercise_dir, sol_rel)
                    log(f"Substituted {matched_example} -> {sol_rel}")
                    shutil.copy2(src_example, dest_solution)
                else:
                    log(f"No reference solution to substitute for {sol_rel} (kept original).")

            # Run cmake configure
            run_cmd(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], cwd=temp_exercise_dir)

            # Run cmake build
            run_cmd(["cmake", "--build", "build"], cwd=temp_exercise_dir)

            # Locate test executable in build dir
            test_exe_name = "binary-search-tree"
            test_exe_path = os.path.join(temp_exercise_dir, "build", test_exe_name)
            if not os.path.exists(test_exe_path):
                # Search build dir for executable
                for root, _, files in os.walk(os.path.join(temp_exercise_dir, "build")):
                    if test_exe_name in files:
                        test_exe_path = os.path.join(root, test_exe_name)
                        break

            if not os.path.exists(test_exe_path):
                log(f"ERROR: Test executable {test_exe_name} not found in build directory.")
                sys.exit(1)

            # Run test executable with standard human-readable output
            test_run_res = run_cmd([test_exe_path, "-s"], cwd=temp_exercise_dir)

            # Run test executable with XML reporter for robust parsing and assertion
            xml_run_res = run_cmd([test_exe_path, "-r", "xml"], cwd=temp_exercise_dir)

            # Parse XML output
            root_xml = ET.fromstring(xml_run_res.stdout)
            test_cases = root_xml.findall(".//TestCase")
            total_cases = len(test_cases)
            log(f"Total executed test cases: {total_cases}")

            if total_cases == 0:
                log("ERROR: Zero test cases were executed!")
                sys.exit(1)

            # Verify and record status of each test case
            passed_cases = set()
            failed_cases = set()
            for tc in test_cases:
                tc_name = tc.attrib.get("name", "")
                overall = tc.find("OverallResult")
                if overall is not None and overall.attrib.get("success") == "true":
                    passed_cases.add(tc_name)
                else:
                    failed_cases.add(tc_name)

            if failed_cases:
                log(f"ERROR: Some test cases failed: {failed_cases}")
                sys.exit(1)

            # Explicitly assert required cases
            required_cases = [
                "data_is_retained",
                "smaller_number_at_left_node",
                "same_number_at_left_node",
            ]
            for req in required_cases:
                assert req in passed_cases, f"Assertion failed: Test case '{req}' was not found or did not pass!"
                log(f"Assertion passed: '{req}' is present and passed.")

            log("All assertions and checks succeeded!")

    finally:
        log_file.close()


if __name__ == "__main__":
    main()
