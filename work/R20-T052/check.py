#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def strip_timestamp_comments(text: str) -> str:
    """Strip comment lines containing dates, times, or timestamps."""
    lines = []
    # Pattern to match dates/times like 2026-11-15, 13:14:02, etc.
    timestamp_pattern = re.compile(
        r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\d{1,2}:\d{2}(:\d{2})?|timestamp|generated on)",
        re.IGNORECASE
    )
    for line in text.splitlines():
        stripped = line.strip()
        if (stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*")) and timestamp_pattern.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    work_dir = os.path.join(root_dir, "work", "R20-T052")
    os.makedirs(work_dir, exist_ok=True)

    exercise_rel = os.path.join("exercises", "practice", "acronym")
    exercise_abs = os.path.join(root_dir, exercise_rel)
    config_json_path = os.path.join(exercise_abs, ".meta", "config.json")

    output_lines = []
    def log(msg):
        print(msg)
        output_lines.append(str(msg))

    log(f"Starting check for {exercise_rel}")

    # Read exercises/practice/acronym/.meta/config.json to resolve test and solution paths
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

    # Creates two separate temporary directories and copies the exercise into both to simulate a regeneration check
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        dir1 = os.path.join(tmpdir1, "acronym")
        dir2 = os.path.join(tmpdir2, "acronym")

        log(f"Copying {exercise_abs} to {dir1}")
        shutil.copytree(exercise_abs, dir1)
        log(f"Copying {exercise_abs} to {dir2}")
        shutil.copytree(exercise_abs, dir2)

        # Compare acronym_test.cpp between the two folders and assert they are identical (ignoring any timestamp comments)
        test_file_rel = test_files[0]  # acronym_test.cpp
        test_path1 = os.path.join(dir1, test_file_rel)
        test_path2 = os.path.join(dir2, test_file_rel)

        assert os.path.exists(test_path1), f"Test file {test_path1} does not exist"
        assert os.path.exists(test_path2), f"Test file {test_path2} does not exist"

        with open(test_path1, "r", encoding="utf-8") as f1, open(test_path2, "r", encoding="utf-8") as f2:
            content1 = strip_timestamp_comments(f1.read())
            content2 = strip_timestamp_comments(f2.read())

        assert content1 == content2, f"{test_file_rel} differed between simulated regeneration directories"
        log(f"Verified {test_file_rel} is identical between the two directories (ignoring timestamps)")

        # Substitutes example.cpp into the learner solution path in one of the temp directories
        # Map example files to solution files by matching file extensions or basenames
        for ex in example_files:
            ex_base = os.path.basename(ex)
            # Match example.cpp -> acronym.cpp, example.h -> acronym.h
            target_sol = None
            if ex_base == "example.cpp":
                for sol in solution_files:
                    if sol.endswith(".cpp"):
                        target_sol = sol
                        break
            elif ex_base == "example.h":
                for sol in solution_files:
                    if sol.endswith(".h"):
                        target_sol = sol
                        break
            if not target_sol:
                for sol in solution_files:
                    if os.path.splitext(ex_base)[1] == os.path.splitext(sol)[1]:
                        target_sol = sol
                        break

            assert target_sol, f"Could not map example file {ex} to a solution file in {solution_files}"
            src_path = os.path.join(dir1, ex)
            dest_path = os.path.join(dir1, target_sol)
            log(f"Substituting {src_path} -> {dest_path}")
            shutil.copyfile(src_path, dest_path)

        # Runs cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON
        cmd_cmake_configure = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        log(f"Running command: {' '.join(cmd_cmake_configure)}")
        res_config = subprocess.run(cmd_cmake_configure, cwd=dir1, capture_output=True, text=True)
        log("--- cmake configure stdout ---")
        log(res_config.stdout)
        log("--- cmake configure stderr ---")
        log(res_config.stderr)
        assert res_config.returncode == 0, f"cmake configure failed with returncode {res_config.returncode}"

        # Runs cmake --build build
        cmd_cmake_build = ["cmake", "--build", "build"]
        log(f"Running command: {' '.join(cmd_cmake_build)}")
        res_build = subprocess.run(cmd_cmake_build, cwd=dir1, capture_output=True, text=True)
        log("--- cmake build stdout ---")
        log(res_build.stdout)
        log("--- cmake build stderr ---")
        log(res_build.stderr)
        assert res_build.returncode == 0, f"cmake build failed with returncode {res_build.returncode}"

        # Runs the generated test executable
        exe_path = os.path.join(dir1, "build", "acronym")
        assert os.path.exists(exe_path), f"Test executable not found at {exe_path}"

        cmd_run_test = [exe_path, "-s"]
        log(f"Running command: {' '.join(cmd_run_test)}")
        res_test = subprocess.run(cmd_run_test, cwd=dir1, capture_output=True, text=True)
        log("--- test execution stdout ---")
        log(res_test.stdout)
        log("--- test execution stderr ---")
        log(res_test.stderr)
        assert res_test.returncode == 0, f"Test executable failed with returncode {res_test.returncode}"

        # Validates that all child return codes are zero, reports total number of executed cases
        # Check for zero-test run
        match_test_summary = re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test.stdout)
        assert match_test_summary, "Failed to parse test execution summary"
        num_assertions = int(match_test_summary.group(1))
        num_test_cases = int(match_test_summary.group(2))
        log(f"Total number of executed test cases: {num_test_cases} ({num_assertions} assertions)")
        assert num_test_cases > 0, "Zero test cases were run!"
        assert num_assertions > 0, "Zero test assertions were run!"

        # Explicitly asserts that the test cases 'basic', 'lowercase_words', and 'punctuation' are present and pass
        required_cases = ['basic', 'lowercase_words', 'punctuation']
        for case in required_cases:
            assert case in res_test.stdout, f"Required test case '{case}' was not executed!"
            # Ensure Catch reported it passed (e.g. PASSED: ... or no failure under that test case section)
            # In Catch -s output, passing tests show `PASSED:`
            case_pattern = re.compile(rf"-\s*\n\s*{re.escape(case)}\s*\n.*?PASSED:", re.DOTALL)
            assert case_pattern.search(res_test.stdout), f"Required test case '{case}' did not pass successfully!"
            log(f"Verified required test case present and passed: '{case}'")

    # Saves all configuration, build, and test execution outputs to work/R20-T052/check_output.log
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
