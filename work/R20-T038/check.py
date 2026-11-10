#!/usr/bin/env python3
"""Check script for R20-T038: Map the maintained files for minesweeper."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/minesweeper"
WORK_DIR = "work/R20-T038"
REPO_ROOT = os.getcwd()

EXPECTED_TEST_CASES = 12
EXPECTED_ASSERTIONS = 12

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "minesweeper")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def verify_output(stdout, label):
    """Verify test output has expected test cases and assertions."""
    if "All tests passed" not in stdout:
        print(f"{label}: Tests did not pass!")
        print(stdout)
        sys.exit(1)
    
    for line in stdout.strip().split('\n'):
        if 'assertions in' in line and 'test cases' in line:
            print(f"  {line.strip()}")
            if f"{EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases" not in line:
                print(f"  ERROR: Expected {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases!")
                sys.exit(1)

def check_config(config_path, exercise_dir):
    """Validate the config.json file structure and paths."""
    errors = []
    
    with open(config_path) as f:
        config = json.load(f)
    
    if "files" not in config:
        errors.append("Missing 'files' key in config.json")
        return errors
    
    files = config["files"]
    
    for role, paths in files.items():
        if not isinstance(paths, list):
            errors.append(f"Files for '{role}' must be a list")
            continue
        
        for path in paths:
            # Check for parent traversal
            if ".." in path or path.startswith("/"):
                errors.append(f"Path '{path}' in '{role}' has parent traversal or absolute path")
                continue
            
            # Check file exists (relative to exercise directory)
            full_path = os.path.join(exercise_dir, path)
            if not os.path.exists(full_path):
                errors.append(f"File '{path}' in '{role}' does not exist at {full_path}")
            elif not os.path.isfile(full_path):
                errors.append(f"Path '{path}' in '{role}' is not a file")
    
    return errors

def run_check():
    # First check config validation
    print("=" * 60)
    print("STEP 1: Config Validation")
    print("=" * 60)
    
    config_path = os.path.join(REPO_ROOT, EXERCISE_DIR, ".meta/config.json")
    exercise_dir = os.path.join(REPO_ROOT, EXERCISE_DIR)
    
    if not os.path.exists(config_path):
        print(f"ERROR: config.json not found at {config_path}")
        sys.exit(1)
    
    errors = check_config(config_path, exercise_dir)
    
    if errors:
        print("Configuration errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("Configuration is valid!")
    print(f"  Exercise: {EXERCISE_DIR}")
    print(f"  Config: .meta/config.json")
    print(f"  All declared files exist and are valid")
    
    # Now test with reference implementation
    print("\n" + "=" * 60)
    print("STEP 2: Reference Implementation Test")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "minesweeper")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # Configure once
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                        os.path.join(target_dir, "minesweeper.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "minesweeper.h"))
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print(f"Reference implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
        
        print(f"Reference: All tests passed!")
        verify_output(stdout, "Reference")
        
        # Save evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        print("\nCheck completed successfully!")
        print(f"- Config validation: PASSED")
        print(f"- Reference: {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases")
        print(f"- File mapping documented in docs/maintenance/minesweeper.md")

if __name__ == "__main__":
    run_check()