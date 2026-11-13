#!/usr/bin/env python3
"""Check script for R20-T035: Measure the scaling of the yacht reference."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/yacht"
WORK_DIR = "work/R20-T035"
REPO_ROOT = os.getcwd()

EXPECTED_TOTAL_TESTS = 29

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "yacht")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "yacht")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # Configure once
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # Test with reference implementation
        print("=" * 60)
        print("TEST: Reference implementation")
        print("=" * 60)
        
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                        os.path.join(target_dir, "yacht.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "yacht.h"))
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print(f"Reference implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
            
        if "All tests passed" not in stdout:
            print("Tests did not pass!")
            print(stdout)
            sys.exit(1)
        
        print(f"Reference: All tests passed!")
        for line in stdout.strip().split('\n'):
            if 'assertions in' in line and 'test cases' in line:
                print(f"  {line.strip()}")
                if f"{EXPECTED_TOTAL_TESTS} test cases" not in line:
                    print(f"  ERROR: Expected {EXPECTED_TOTAL_TESTS} test cases!")
                    sys.exit(1)
        
        # Save evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        print("\nCheck completed successfully!")
        print(f"- Reference: {EXPECTED_TOTAL_TESTS} tests pass")
        print(f"- Complexity analysis in docs/maintenance/yacht.md")

if __name__ == "__main__":
    run_check()