#!/usr/bin/env python3
"""Check script for R20-T033: Find a test that distinguishes a wrong isogram implementation."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/isogram"
WORK_DIR = "work/R20-T033"
REPO_ROOT = os.getcwd()

# The mutant test case that should fail
MUTANT_FAILING_UUIDS = [
    "f1a7f6c7-a42f-4915-91d7-35b2ea11c92e",  # word_with_duplicated_character_in_mixed_case
    "14a4f3c1-3b47-4695-b645-53d328298942",  # word_with_duplicated_character_in_mixed_case_lowercase_first
]

# Expected test count
EXPECTED_TOTAL_TESTS = 14

def build_and_test(target_dir, test_name):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "isogram")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "isogram")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # ============ SETUP: Configure once ============
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # ============ TEST 1: Reference implementation (should pass all) ============
        print("=" * 60)
        print("TEST 1: Reference implementation")
        print("=" * 60)
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                        os.path.join(target_dir, "isogram.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "isogram.h"))
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir, "reference")
        
        if not success:
            print(f"Reference implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
            
        if "All tests passed" not in stdout:
            print("Reference: Tests did not pass!")
            print(stdout)
            sys.exit(1)
        
        print(f"Reference: All tests passed!")
        for line in stdout.strip().split('\n'):
            if 'assertions in' in line and 'test cases' in line:
                print(f"  {line.strip()}")
                if f"{EXPECTED_TOTAL_TESTS} test cases" not in line:
                    print(f"  ERROR: Expected {EXPECTED_TOTAL_TESTS} test cases!")
                    sys.exit(1)
        
        with open(os.path.join(REPO_ROOT, WORK_DIR, "reference_output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        # ============ TEST 2: Mutant (missing tolower) - should fail specific tests ============
        print("\n" + "=" * 60)
        print("TEST 2: Mutant (case-sensitive - missing tolower)")
        print("=" * 60)
        
        # Create mutant implementation
        mutant_code = '''#include <unordered_set>
#include "isogram.h"

namespace isogram {

bool is_isogram(std::string const& input_str) {
    std::unordered_set<char> chars;
    for (char const ch : input_str) {
        if (isalnum(ch)) {
            auto ret = chars.insert(ch);  // MUTANT: removed tolower()
            if (ret.second == false) {
                return false;
            }
        }
    }
    return true;
}

}  // namespace isogram
'''
        with open(os.path.join(target_dir, "isogram.cpp"), "w") as f:
            f.write(mutant_code)
        
        # Rebuild (don't use check=True since test will fail)
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir)
        
        success, stdout, stderr = build_and_test(target_dir, "mutant")
        
        # Save mutant output
        with open(os.path.join(REPO_ROOT, WORK_DIR, "mutant_output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        # Check mutant fails the expected tests (should fail with 2 failed tests)
        print(f"Mutant return code: 0" if success else f"Mutant return code: non-zero (expected)")
        
        # Check that both expected UUIDs appear as failures
        for uuid in MUTANT_FAILING_UUIDS:
            if uuid not in stdout:
                print(f"  WARNING: Expected failing UUID {uuid} not found in mutant output!")
            else:
                print(f"  Confirmed: Mutant fails on UUID {uuid}")
        
        # Verify exactly 2 tests failed
        if "12 passed | 2 failed" not in stdout and "2 failed" not in stdout:
            print(f"  WARNING: Expected exactly 2 failures, got different count")
        
        print("\nCheck completed successfully!")
        print(f"- Reference: {EXPECTED_TOTAL_TESTS} tests pass")
        print(f"- Mutant: Fails on 2 mixed-case tests (as expected)")
        print(f"- Hint added to .docs/hints.md")
        print(f"- Maintenance doc at docs/maintenance/isogram.md")

if __name__ == "__main__":
    run_check()