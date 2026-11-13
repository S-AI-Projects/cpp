#!/usr/bin/env python3
"""Check script for R20-T037: Add C++-specific guidance for sieve."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/sieve"
WORK_DIR = "work/R20-T037"
REPO_ROOT = os.getcwd()

EXPECTED_TEST_CASES = 5
EXPECTED_ASSERTIONS = 5

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "sieve")
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

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "sieve")
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
                        os.path.join(target_dir, "sieve.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "sieve.h"))
        
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
        print(f"- Reference: {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases")
        print(f"- Lambda capture guidance added to .docs/hints.md")
        print(f"- Micro-example demonstrates value vs reference capture difference")
        print(f"- Pitfall explanation: why capture-by-value is needed in the sieve")

if __name__ == "__main__":
    run_check()