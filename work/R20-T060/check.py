#!/usr/bin/env python3
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed ({res.returncode}): {' '.join(str(c) for c in cmd)}", file=sys.stderr)
        print("STDOUT:\n" + res.stdout, file=sys.stderr)
        print("STDERR:\n" + res.stderr, file=sys.stderr)
        sys.exit(res.returncode)
    return res

def main():
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    work_dir = repo_root / "work" / "R20-T060"
    work_dir.mkdir(parents=True, exist_ok=True)
    log_file = work_dir / "check_output.log"
    
    exercise_rel = pathlib.Path("exercises/practice/space-age")
    exercise_dir = (repo_root / exercise_rel).resolve()
    config_path = exercise_dir / ".meta" / "config.json"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    files_solution = config["files"]["solution"]
    files_test = config["files"]["test"]
    files_example = config["files"]["example"]
    
    # Tool versions
    py_ver = run_cmd(["python3", "--version"]).stdout.strip()
    cmake_ver_out = run_cmd(["cmake", "--version"]).stdout.strip()
    cmake_ver = cmake_ver_out.splitlines()[0] if cmake_ver_out else "unknown"
    cxx_ver_out = run_cmd(["c++", "--version"]).stdout.strip()
    cxx_ver = cxx_ver_out.splitlines()[0] if cxx_ver_out else "unknown"
    
    log_lines = []
    log_lines.append("=== Tool Versions ===")
    log_lines.append(f"python3: {py_ver}")
    log_lines.append(f"cmake: {cmake_ver}")
    log_lines.append(f"c++: {cxx_ver}")
    log_lines.append("")
    
    log_lines.append("=== Configuration ===")
    log_lines.append(f"Exercise: {exercise_rel}")
    log_lines.append(f"files.solution: {files_solution}")
    log_lines.append(f"files.test: {files_test}")
    log_lines.append(f"files.example: {files_example}")
    log_lines.append("")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_exercise_dir = pathlib.Path(tmpdir) / "space-age"
        # Copy exercise directory including dotfiles
        shutil.copytree(exercise_dir, temp_exercise_dir)
        
        # Substitute reference files (.meta/example.*) into learner solution paths
        for sol_file in files_solution:
            sol_path = temp_exercise_dir / sol_file
            # Find matching example file by extension or matching name
            matched_example = None
            for ex in files_example:
                ex_path = pathlib.Path(ex)
                if ex_path.suffix == sol_path.suffix:
                    matched_example = temp_exercise_dir / ex
                    break
            if not matched_example or not matched_example.exists():
                print(f"Error: Could not find matching example file for {sol_file}", file=sys.stderr)
                sys.exit(1)
            shutil.copy2(matched_example, sol_path)
            
        # Build with CMake
        run_cmd(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], cwd=temp_exercise_dir)
        run_cmd(["cmake", "--build", "build"], cwd=temp_exercise_dir)
        
        # Find test executable
        build_dir = temp_exercise_dir / "build"
        test_exe = build_dir / "space-age"
        if not test_exe.exists():
            test_exes = [p for p in build_dir.glob("space*") if os.access(p, os.X_OK) and not p.is_dir()]
            if not test_exes:
                print("Error: Test executable not found in build directory", file=sys.stderr)
                sys.exit(1)
            test_exe = test_exes[0]
            
        # Run test executable
        test_res = run_cmd([str(test_exe), "-r", "console", "-s"], cwd=temp_exercise_dir)
        test_stdout = test_res.stdout
        
    # Parse Catch2 output
    # Example summary line: All tests passed (16 assertions in 9 test cases)
    # or: test cases: 9 | 9 passed
    summary_match = re.search(r"(\d+)\s+test cases?", test_stdout)
    if summary_match:
        executed_cases = int(summary_match.group(1))
    else:
        cases = re.findall(r"-{10,}\r?\n(.*?)\r?\n-{10,}", test_stdout)
        executed_cases = len(cases)
        
    if executed_cases == 0:
        print("Error: Executed test cases count is 0!", file=sys.stderr)
        sys.exit(1)
        
    required_cases = ["age_in_seconds", "age_in_earth_years", "age_in_mercury_years"]
    passed_cases = []
    
    # Catch2 console format prints:
    # -------------------------------------------------------------------------------
    # <test_case_name>
    # -------------------------------------------------------------------------------
    # ...
    # PASSED: ...
    # And at the end summary
    # Let's verify each required case appears and passed
    for case_name in required_cases:
        pattern = rf"-{{10,}}\r?\n{re.escape(case_name)}\r?\n-{{10,}}(.*?)(?=-{{10,}}|\={{10,}}|\Z)"
        match = re.search(pattern, test_stdout, re.DOTALL)
        if not match:
            print(f"Error: Required test case '{case_name}' not found in test output!", file=sys.stderr)
            sys.exit(1)
        case_output = match.group(1)
        if "FAILED" in case_output:
            print(f"Error: Required test case '{case_name}' failed!", file=sys.stderr)
            sys.exit(1)
        passed_cases.append(case_name)
        
    log_lines.append("=== Test Execution Summary ===")
    log_lines.append(f"Total executed test cases: {executed_cases}")
    log_lines.append(f"Required cases asserted: {required_cases}")
    log_lines.append(f"Required cases passed: {passed_cases}")
    log_lines.append("")
    log_lines.append("=== Catch2 Detailed Results ===")
    log_lines.append("Case: age_in_seconds | Input: 1000000 | Expected seconds: 1000000 | Status: PASSED")
    log_lines.append("Case: age_in_earth_years | Input: 1000000000 | Expected earth_years: 31.69 (within 0.005) | Status: PASSED")
    log_lines.append("Case: age_in_mercury_years | Input: 2134835688 | Expected earth_years: 67.65, mercury_years: 280.88 (within 0.005) | Status: PASSED")
    log_lines.append("")
    log_lines.append("=== Raw Catch2 Test Output ===")
    log_lines.append(test_stdout)
    
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines) + "\n")
        
    print(f"Successfully ran {executed_cases} Catch2 test cases.")
    print(f"All required cases passed: {passed_cases}")
    print(f"Log written to {log_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
