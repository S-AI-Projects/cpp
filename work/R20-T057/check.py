#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def extract_code_and_expected_output(hints_md_path):
    """
    Extracts the two C++ micro-examples and their expected outputs from hints.md.
    Returns a list of dicts: [{'title': ..., 'code': ..., 'expected_output': ...}, ...]
    """
    with open(hints_md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern to find cpp code blocks and their subsequent expected text blocks
    # Example 1: Passing by Const Reference
    # Example 2: Pitfall Example: Unchecked Arithmetic / Out-of-Bounds Shift
    examples = []

    sections = re.split(r"^###\s+", content, flags=re.MULTILINE)
    for sec in sections:
        if not sec.strip():
            continue
        lines = sec.splitlines()
        title = lines[0].strip()

        # Find ```cpp ... ```
        cpp_match = re.search(r"```cpp\n(.*?)```", sec, re.DOTALL)
        # Find ```text ... ``` under Expected Output
        text_match = re.search(r"```text\n(.*?)```", sec, re.DOTALL)

        if cpp_match and text_match:
            code = cpp_match.group(1)
            expected = text_match.group(1)
            examples.append({
                "title": title,
                "code": code,
                "expected_output": expected
            })

    return examples

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    work_dir = os.path.join(repo_root, "work", "R20-T057")
    os.makedirs(work_dir, exist_ok=True)
    log_file_path = os.path.join(work_dir, "check_output.log")

    output_lines = []

    def record_and_print(msg):
        print(msg)
        output_lines.append(str(msg))

    record_and_print("=== Starting check for pangram (R20-T057) ===")

    # 1. Record tool versions
    record_and_print("\n--- Tool Versions ---")
    for tool_cmd in [["c++", "--version"], ["cmake", "--version"]]:
        res = subprocess.run(tool_cmd, capture_output=True, text=True)
        record_and_print(f"Command: {' '.join(tool_cmd)}")
        record_and_print(f"Exit Code: {res.returncode}")
        record_and_print(res.stdout.strip())
        if res.stderr.strip():
            record_and_print(res.stderr.strip())
        if res.returncode != 0:
            record_and_print(f"ERROR: Tool check failed for {' '.join(tool_cmd)}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(res.returncode)

    exercise_rel = os.path.join("exercises", "practice", "pangram")
    exercise_abs = os.path.join(repo_root, exercise_rel)
    config_json_path = os.path.join(exercise_abs, ".meta", "config.json")
    hints_md_path = os.path.join(exercise_abs, ".docs", "hints.md")

    # 2. Read config.json to resolve solution, test, and example paths
    record_and_print(f"\n--- Reading Config from {config_json_path} ---")
    if not os.path.exists(config_json_path):
        record_and_print(f"ERROR: config.json not found at {config_json_path}")
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines) + "\n")
        sys.exit(1)

    with open(config_json_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    files_cfg = config_data.get("files", {})
    solution_files = files_cfg.get("solution", [])
    test_files = files_cfg.get("test", [])
    example_files = files_cfg.get("example", [])

    record_and_print(f"Solution files: {solution_files}")
    record_and_print(f"Test files: {test_files}")
    record_and_print(f"Example files: {example_files}")

    assert solution_files, "No solution files configured"
    assert test_files, "No test files configured"
    assert example_files, "No example files configured"

    # Map example files to solution files by matching file extensions
    file_substitutions = []
    for ex in example_files:
        ex_base = os.path.basename(ex)
        _, ex_ext = os.path.splitext(ex_base)
        matched_sol = [s for s in solution_files if s.endswith(ex_ext)]
        assert matched_sol, f"No matching solution file for example {ex} with extension {ex_ext}"
        file_substitutions.append((ex, matched_sol[0]))

    record_and_print(f"Resolved file substitutions: {file_substitutions}")

    # 3. Create temporary directory and run tests
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_exercise_dir = os.path.join(tmpdir, "pangram")
        record_and_print(f"\nCopying exercise (including dotfiles) to temp directory: {tmp_exercise_dir}")
        shutil.copytree(exercise_abs, tmp_exercise_dir)

        # Substitute .meta/example.cpp and .meta/example.h only in that copy
        record_and_print("\nPerforming file substitutions in temporary copy:")
        for src_rel, dest_rel in file_substitutions:
            src_full = os.path.join(tmp_exercise_dir, src_rel)
            dest_full = os.path.join(tmp_exercise_dir, dest_rel)
            record_and_print(f"Substituting: {src_rel} -> {dest_rel}")
            shutil.copyfile(src_full, dest_full)

        # Step 3a: cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON
        cmd_cmake_configure = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        record_and_print(f"\nRunning command: {' '.join(cmd_cmake_configure)}")
        res_config = subprocess.run(
            cmd_cmake_configure, cwd=tmp_exercise_dir, capture_output=True, text=True
        )
        record_and_print(f"Exit Code: {res_config.returncode}")
        record_and_print("--- cmake configure stdout ---")
        record_and_print(res_config.stdout)
        record_and_print("--- cmake configure stderr ---")
        record_and_print(res_config.stderr)
        if res_config.returncode != 0:
            record_and_print(f"ERROR: CMake configure failed with code {res_config.returncode}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(res_config.returncode)

        # Step 3b: cmake --build build
        cmd_cmake_build = ["cmake", "--build", "build"]
        record_and_print(f"\nRunning command: {' '.join(cmd_cmake_build)}")
        res_build = subprocess.run(
            cmd_cmake_build, cwd=tmp_exercise_dir, capture_output=True, text=True
        )
        record_and_print(f"Exit Code: {res_build.returncode}")
        record_and_print("--- cmake build stdout ---")
        record_and_print(res_build.stdout)
        record_and_print("--- cmake build stderr ---")
        record_and_print(res_build.stderr)
        if res_build.returncode != 0:
            record_and_print(f"ERROR: CMake build failed with code {res_build.returncode}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(res_build.returncode)

        # Step 3c: Run Catch2 test executable
        exe_path = os.path.join(tmp_exercise_dir, "build", "pangram")
        if not os.path.isfile(exe_path):
            record_and_print(f"ERROR: Test executable not found at {exe_path}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(1)

        cmd_run_test = [exe_path, "-s"]
        record_and_print(f"\nRunning command: {' '.join(cmd_run_test)}")
        res_test = subprocess.run(
            cmd_run_test, cwd=tmp_exercise_dir, capture_output=True, text=True
        )
        record_and_print(f"Exit Code: {res_test.returncode}")
        record_and_print("--- test execution stdout ---")
        record_and_print(res_test.stdout)
        record_and_print("--- test execution stderr ---")
        record_and_print(res_test.stderr)
        if res_test.returncode != 0:
            record_and_print(f"ERROR: Catch2 test executable failed with code {res_test.returncode}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(res_test.returncode)

        # Parse test counts
        # Catch2 output typically: "All tests passed (9 assertions in 9 test cases)"
        # or "test cases: 9 | 9 passed"
        total_test_cases = 0
        total_assertions = 0
        match_summary = re.search(r"(\d+)\s+assertions?\s+in\s+(\d+)\s+test cases?", res_test.stdout)
        if match_summary:
            total_assertions = int(match_summary.group(1))
            total_test_cases = int(match_summary.group(2))
        else:
            match_cases = re.search(r"test cases:\s*(\d+)\s*\|\s*(\d+)\s*passed", res_test.stdout)
            if match_cases:
                total_test_cases = int(match_cases.group(2))

        record_and_print(f"Executed test counts: {total_test_cases} test cases, {total_assertions} assertions")
        if total_test_cases <= 0:
            record_and_print("ERROR: Executed test count must be > 0!")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(1)

        # Assert sentence_empty, pangram_with_only_lower_case, and missing_character_x pass
        required_cases = ["sentence_empty", "pangram_with_only_lower_case", "missing_character_x"]
        for case in required_cases:
            case_pattern = re.compile(rf"-{{10,}}\s*\n\s*{re.escape(case)}\s*\n.*?PASSED:", re.DOTALL)
            if not (case_pattern.search(res_test.stdout) or case in res_test.stdout):
                record_and_print(f"ERROR: Required test case '{case}' was not executed or not passed!")
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines) + "\n")
                sys.exit(1)
            record_and_print(f"ASSERTION PASSED: Test case '{case}' executed and passed.")

        # 4. Compile and run micro-examples from hints.md
        record_and_print(f"\n--- Extracting and Running Micro-Examples from {hints_md_path} ---")
        micro_examples = extract_code_and_expected_output(hints_md_path)
        record_and_print(f"Found {len(micro_examples)} micro-examples in hints.md")
        if len(micro_examples) != 2:
            record_and_print(f"ERROR: Expected 2 micro-examples, found {len(micro_examples)}")
            with open(log_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines) + "\n")
            sys.exit(1)

        for i, example in enumerate(micro_examples, start=1):
            title = example["title"]
            source_code = example["code"]
            expected_output = example["expected_output"].strip()

            src_file_name = f"micro_example_{i}.cpp"
            bin_file_name = f"micro_example_{i}.out"
            src_file_path = os.path.join(tmp_exercise_dir, src_file_name)
            bin_file_path = os.path.join(tmp_exercise_dir, bin_file_name)

            record_and_print(f"\nEvaluating Micro-Example {i}: {title}")
            record_and_print(f"Source file: {src_file_name}")
            with open(src_file_path, "w", encoding="utf-8") as src_f:
                src_f.write(source_code)

            # Compile with c++ -std=c++17
            compile_cmd = ["c++", "-std=c++17", src_file_path, "-o", bin_file_path]
            record_and_print(f"Compile command: {' '.join(compile_cmd)}")
            res_comp = subprocess.run(compile_cmd, cwd=tmp_exercise_dir, capture_output=True, text=True)
            record_and_print(f"Compile exit code: {res_comp.returncode}")
            if res_comp.stdout.strip():
                record_and_print(f"Compile stdout:\n{res_comp.stdout}")
            if res_comp.stderr.strip():
                record_and_print(f"Compile stderr:\n{res_comp.stderr}")
            if res_comp.returncode != 0:
                record_and_print(f"ERROR: Failed to compile {src_file_name}")
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines) + "\n")
                sys.exit(res_comp.returncode)

            # Run micro-example executable
            record_and_print(f"Running executable: {bin_file_path}")
            res_run = subprocess.run([bin_file_path], cwd=tmp_exercise_dir, capture_output=True, text=True)
            actual_output = res_run.stdout.strip()
            record_and_print(f"Run exit code: {res_run.returncode}")
            record_and_print(f"Actual output:\n{actual_output}")
            record_and_print(f"Expected output:\n{expected_output}")

            if res_run.returncode != 0:
                record_and_print(f"ERROR: Micro-example {i} execution returned non-zero code {res_run.returncode}")
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines) + "\n")
                sys.exit(res_run.returncode)

            if actual_output != expected_output:
                record_and_print(f"ERROR: Output mismatch for micro-example {i}!")
                record_and_print(f"Expected: {repr(expected_output)}")
                record_and_print(f"Actual:   {repr(actual_output)}")
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines) + "\n")
                sys.exit(1)

            record_and_print(f"ASSERTION PASSED: Micro-example {i} output matches expected output perfectly.")

    # 5. Save all outputs to log file
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    record_and_print(f"\nAll checks succeeded! Log written to {log_file_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unhandled error during check execution: {e}", file=sys.stderr)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        log_file_path = os.path.join(repo_root, "work", "R20-T057", "check_output.log")
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"\nUnhandled Exception: {e}\n")
        sys.exit(1)
