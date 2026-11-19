#!/usr/bin/env python3
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXERCISE_DIR = REPO_ROOT / "exercises" / "practice" / "crypto-square"
REAL_CONFIG_PATH = EXERCISE_DIR / ".meta" / "config.json"
WORK_DIR = pathlib.Path(__file__).resolve().parent
LOG_FILE = WORK_DIR / "check_output.log"

log_lines = []

def log(msg=""):
    print(msg)
    log_lines.append(str(msg))

class ValidationError(Exception):
    pass

class PathTraversalError(ValidationError):
    pass

class MissingFileError(ValidationError):
    pass

def validate_config(config_dict, base_dir: pathlib.Path):
    """
    Validates the files section in config_dict against base_dir.
    Resolves every declared path relative to base_dir.
    Strictly rejects parent directory traversal (..) or paths resolving outside base_dir.
    Asserts every declared file exists.
    Returns a dict mapping category to resolved Path objects.
    """
    files_sec = config_dict.get("files", {})
    resolved_paths = {}
    
    # We check solution, test, example, and editor if present
    for category in ["solution", "test", "example", "editor"]:
        file_list = files_sec.get(category, [])
        resolved_paths[category] = []
        for raw_path in file_list:
            p = pathlib.Path(raw_path)
            # Check for explicit traversal components
            if ".." in p.parts:
                raise PathTraversalError(f"Directory traversal ('..') detected in path: '{raw_path}'")
            
            # Resolve relative to base_dir
            target = (base_dir / p).resolve()
            
            # Check if resolved path is within base_dir
            try:
                target.relative_to(base_dir.resolve())
            except ValueError:
                raise PathTraversalError(f"Path '{raw_path}' resolves outside base directory '{base_dir}': '{target}'")
            
            # Check file existence
            if not target.exists():
                raise MissingFileError(f"Declared file does not exist: '{raw_path}' (resolved: '{target}')")
            if not target.is_file():
                raise MissingFileError(f"Declared path is not a file: '{raw_path}' (resolved: '{target}')")
            
            resolved_paths[category].append((raw_path, target))
            
    return resolved_paths

def get_tool_versions():
    tools = {}
    for cmd, name in [
        (["cmake", "--version"], "cmake"),
        (["c++", "--version"], "c++"),
        ([sys.executable, "--version"], "python3"),
    ]:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        tools[name] = res.stdout.strip()
    return tools

def main():
    log("=== R20-T058 Verification Script ===")
    log()
    
    # 1. Tool versions
    log("--- Tool Versions ---")
    versions = get_tool_versions()
    for tool, ver in versions.items():
        log(f"[{tool}]\n{ver}\n")
    
    # 2. Test Negative Fixtures
    log("--- Negative Metadata Fixtures Testing ---")
    with open(REAL_CONFIG_PATH, "r", encoding="utf-8") as f:
        real_config = json.load(f)
        
    fixtures = [
        (
            "missing-reference",
            {
                "files": {
                    "solution": real_config["files"]["solution"],
                    "test": real_config["files"]["test"],
                    "example": [".meta/nonexistent_example.cpp", ".meta/example.h"]
                }
            },
            MissingFileError
        ),
        (
            "missing-test",
            {
                "files": {
                    "solution": real_config["files"]["solution"],
                    "test": ["missing_test.cpp"],
                    "example": real_config["files"]["example"]
                }
            },
            MissingFileError
        ),
        (
            "outside-exercise",
            {
                "files": {
                    "solution": ["../pangram/pangram.cpp"],
                    "test": real_config["files"]["test"],
                    "example": real_config["files"]["example"]
                }
            },
            PathTraversalError
        )
    ]
    
    all_fixtures_passed = True
    for name, fixture_dict, expected_exc in fixtures:
        log(f"Testing fixture: '{name}'")
        log(f"Input config:\n{json.dumps(fixture_dict, indent=2)}")
        try:
            validate_config(fixture_dict, EXERCISE_DIR)
            log(f"FAILED: Expected {expected_exc.__name__}, but validation succeeded.\n")
            all_fixtures_passed = False
        except expected_exc as e:
            log(f"PASSED (Expected {expected_exc.__name__}): {e}\n")
        except Exception as e:
            log(f"FAILED: Expected {expected_exc.__name__}, but got {type(e).__name__}: {e}\n")
            all_fixtures_passed = False

    if not all_fixtures_passed:
        log("Negative fixture tests failed!")
        with open(LOG_FILE, "w", encoding="utf-8") as lf:
            lf.write("\n".join(log_lines) + "\n")
        sys.exit(1)

    # 3. Test Real Config
    log("--- Real config.json Validation ---")
    log(f"Path: {REAL_CONFIG_PATH}")
    log(f"Content:\n{json.dumps(real_config, indent=2)}")
    try:
        resolved = validate_config(real_config, EXERCISE_DIR)
        log("PASSED: Real config.json successfully validated.")
        for cat, items in resolved.items():
            log(f"  {cat}: {[r[0] for r in items]}")
        log()
    except Exception as e:
        log(f"FAILED: Real config validation failed: {e}\n")
        with open(LOG_FILE, "w", encoding="utf-8") as lf:
            lf.write("\n".join(log_lines) + "\n")
        sys.exit(1)

    # 4. Temporary Copy & Catch2 Test Execution
    log("--- Temporary Copy & Catch2 Test Execution ---")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = pathlib.Path(temp_dir).resolve()
        temp_exercise_dir = (temp_dir_path / "crypto-square").resolve()
        log(f"Copying '{EXERCISE_DIR}' to temporary directory '{temp_exercise_dir}'")
        shutil.copytree(EXERCISE_DIR, temp_exercise_dir, symlinks=True)
        
        # Validate temp copy config using paths resolved from config.json
        temp_config_path = temp_exercise_dir / ".meta" / "config.json"
        with open(temp_config_path, "r", encoding="utf-8") as f:
            temp_config = json.load(f)
            
        temp_resolved = validate_config(temp_config, temp_exercise_dir)
        example_files = [item[1] for item in temp_resolved.get("example", [])]
        solution_files = [item[1] for item in temp_resolved.get("solution", [])]
        
        log(f"Example files to substitute: {[f.name for f in example_files]}")
        log(f"Learner solution files to replace: {[f.name for f in solution_files]}")
        
        # Substitute example files into learner solution paths:
        # e.g., example.cpp -> crypto_square.cpp, example.h -> crypto_square.h
        for sol_path in solution_files:
            matching_examples = [ex for ex in example_files if ex.suffix == sol_path.suffix]
            if not matching_examples:
                raise RuntimeError(f"No matching example file found for solution file '{sol_path.name}' with suffix '{sol_path.suffix}'")
            ex_source = matching_examples[0]
            log(f"Substituting '{ex_source.relative_to(temp_exercise_dir)}' -> '{sol_path.relative_to(temp_exercise_dir)}'")
            shutil.copy2(ex_source, sol_path)
            
        # Run cmake configuration
        build_dir = temp_exercise_dir / "build"
        log("\nRunning: cmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=ON")
        cmake_configure_cmd = ["cmake", "-S", str(temp_exercise_dir), "-B", str(build_dir), "-DEXERCISM_RUN_ALL_TESTS=ON"]
        res_config = subprocess.run(cmake_configure_cmd, cwd=temp_exercise_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log(f"Exit code: {res_config.returncode}")
        log(f"Output:\n{res_config.stdout}")
        if res_config.returncode != 0:
            log("FAILED: cmake configuration failed.")
            with open(LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_lines) + "\n")
            sys.exit(res_config.returncode)

        # Run cmake build
        log("\nRunning: cmake --build build")
        cmake_build_cmd = ["cmake", "--build", str(build_dir)]
        res_build = subprocess.run(cmake_build_cmd, cwd=temp_exercise_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log(f"Exit code: {res_build.returncode}")
        log(f"Output:\n{res_build.stdout}")
        if res_build.returncode != 0:
            log("FAILED: cmake build failed.")
            with open(LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_lines) + "\n")
            sys.exit(res_build.returncode)

        # Find Catch2 test executable (crypto-square in build/)
        test_exe = build_dir / "crypto-square"
        if not test_exe.exists():
            # Try searching in build_dir
            exes = [p for p in build_dir.rglob("crypto-square") if p.is_file() and os.access(p, os.X_OK)]
            if exes:
                test_exe = exes[0]
            else:
                log(f"FAILED: Test executable '{test_exe}' does not exist.")
                with open(LOG_FILE, "w", encoding="utf-8") as lf:
                    lf.write("\n".join(log_lines) + "\n")
                sys.exit(1)

        # Run Catch2 test executable
        log(f"\nRunning test executable: {test_exe} -r console -s")
        test_cmd = [str(test_exe), "-r", "console", "-s"]
        res_test = subprocess.run(test_cmd, cwd=temp_exercise_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log(f"Exit code: {res_test.returncode}")
        log(f"Output:\n{res_test.stdout}")
        if res_test.returncode != 0:
            log("FAILED: test executable exited with non-zero code.")
            with open(LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_lines) + "\n")
            sys.exit(res_test.returncode)

        # Assert Catch2 results:
        # Check total number of test cases and that it's > 0
        output_text = res_test.stdout
        required_cases = [
            "empty plaintext results in an empty ciphertext",
            "normalization results in empty plaintext",
            "Lowercase"
        ]
        
        log("\n--- Checking Test Cases in Output ---")
        for case in required_cases:
            if case in output_text:
                log(f"ASSERTION PASSED: Test case '{case}' is present in output.")
            else:
                log(f"ASSERTION FAILED: Test case '{case}' is NOT found in output.")
                with open(LOG_FILE, "w", encoding="utf-8") as lf:
                    lf.write("\n".join(log_lines) + "\n")
                sys.exit(1)
                
        # Parse test count summary e.g. "All tests passed (8 assertions in 8 test cases)" or "test cases:  8 |  8 passed"
        import re
        match = re.search(r"All tests passed \(\d+ assertions in (\d+) test cases\)", output_text, re.IGNORECASE)
        if not match:
            match = re.search(r"test cases:\s+(\d+)\s+\|\s+(\d+)\s+passed", output_text, re.IGNORECASE)
        
        if match:
            total_cases = int(match.group(1))
            passed_cases = int(match.group(2)) if match.lastindex >= 2 else total_cases
            log(f"Parsed test summary: {total_cases} test cases, {passed_cases} passed.")
            if total_cases == 0:
                log("ASSERTION FAILED: Total test cases executed is 0.")
                with open(LOG_FILE, "w", encoding="utf-8") as lf:
                    lf.write("\n".join(log_lines) + "\n")
                sys.exit(1)
            if total_cases != passed_cases:
                log(f"ASSERTION FAILED: Only {passed_cases} out of {total_cases} passed.")
                with open(LOG_FILE, "w", encoding="utf-8") as lf:
                    lf.write("\n".join(log_lines) + "\n")
                sys.exit(1)
        else:
            log("ASSERTION FAILED: 'All tests passed' not found in test output.")
            with open(LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_lines) + "\n")
            sys.exit(1)

    # 5. Check Working Tree
    log("\n--- Working Tree Learner Stub Verification ---")
    git_cmd = ["git", "status", "--porcelain"]
    res_git = subprocess.run(git_cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log(f"git status --porcelain:\n{res_git.stdout}")
    
    # Check that learner stubs are not modified
    for line in res_git.stdout.splitlines():
        if "crypto_square.cpp" in line or "crypto_square.h" in line:
            log(f"ASSERTION FAILED: Working tree learner stub modified: {line}")
            with open(LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_lines) + "\n")
            sys.exit(1)
    log("ASSERTION PASSED: Working tree learner stubs (crypto_square.cpp, crypto_square.h) are unmodified.")

    log("\n=== ALL CHECKS PASSED SUCCESSFULLY ===")
    with open(LOG_FILE, "w", encoding="utf-8") as lf:
        lf.write("\n".join(log_lines) + "\n")

if __name__ == "__main__":
    main()
