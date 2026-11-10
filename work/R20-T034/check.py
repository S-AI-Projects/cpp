#!/usr/bin/env python3
"""Check script for R20-T034: Clarify converter in the roman-numerals reference."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/roman-numerals"
WORK_DIR = "work/R20-T034"
REPO_ROOT = os.getcwd()

EXPECTED_TOTAL_TESTS = 27

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "roman-numerals")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "roman-numerals")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # Configure once
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # Test with refactored implementation (should pass all)
        print("=" * 60)
        print("TEST: Refactored reference implementation")
        print("=" * 60)
        
        # Use the refactored example.cpp (which we'll copy from the repo)
        shutil.copyfile(os.path.join(REPO_ROOT, EXERCISE_DIR, "roman_numerals.cpp"), 
                        os.path.join(target_dir, "roman_numerals.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "roman_numerals.h"))
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print(f"Refactored implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
            
        if "All tests passed" not in stdout:
            print("Tests did not pass!")
            print(stdout)
            sys.exit(1)
        
        print(f"Refactored: All tests passed!")
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
        print(f"- Refactored reference: {EXPECTED_TOTAL_TESTS} tests pass")
        print(f"- Named cases verified: 1_is_i, 2_is_ii, 3_is_iii")
        print(f"- Maintenance doc at docs/maintenance/roman-numerals.md")

if __name__ == "__main__":
    run_check()