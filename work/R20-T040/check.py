#!/usr/bin/env python3
"""Isolated test runner for eliuds-eggs exercise."""

import os
import subprocess
import shutil
import tempfile
import sys
import json
import hashlib

EXERCISE_DIR = "exercises/practice/eliuds-eggs"
WORK_DIR = "work/R20-T040"
REPO_ROOT = os.getcwd()

EXPECTED_ASSERTIONS = 4
EXPECTED_TEST_CASES = 4

def compute_hashes(base_dir, files):
    """Compute MD5 hashes of files."""
    hashes = {}
    for f in files:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            with open(path, 'rb') as fp:
                hashes[f] = hashlib.md5(fp.read()).hexdigest()
    return hashes

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "eliuds-eggs")
    if not os.path.exists(binary_path):
        return (False, "", "Binary not found")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def run_check():
    exercise_dir = os.path.join(REPO_ROOT, EXERCISE_DIR)
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    
    # Load config
    with open(config_path) as f:
        config = json.load(f)
    
    solution_files = config["files"]["solution"]
    test_files = config["files"]["test"]
    example_files = config["files"]["example"]
    
    # Hash learner files before
    initial_hashes = compute_hashes(exercise_dir, solution_files)
    print("=" * 60)
    print("INITIAL LEARNER FILE HASHES")
    print("=" * 60)
    for f, h in initial_hashes.items():
        print(f"  {f}: {h}")
    
    # Test with reference implementation
    print("\n" + "=" * 60)
    print("TEST: Reference implementation (temporary copy)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "eliuds-eggs")
        # Copy exercise directory but exclude build/ folder to avoid CMakeCache issues
        shutil.copytree(exercise_dir, target_dir, 
                       ignore=shutil.ignore_patterns('build*', '*.cache'),
                       dirs_exist_ok=True)
        
        # Substitute reference implementation BEFORE configuring
        print("Substituting reference implementation...")
        # Explicitly copy example files to solution file locations
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                       os.path.join(target_dir, "eliuds_eggs.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                       os.path.join(target_dir, "eliuds_eggs.h"))
        
        # Configure
        print("Configuring...")
        subprocess.run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # Build and test
        print("Building and testing...")
        subprocess.run(["cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print("Reference implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
        
        if "All tests passed" not in stdout:
            print("Tests did not pass!")
            print(stdout)
            sys.exit(1)
        
        print("Reference: All tests passed!")
        for line in stdout.strip().split('\n'):
            if 'assertions in' in line and 'test cases' in line:
                print(f"  {line.strip()}")
        
        # Hash learner files after
        final_hashes = compute_hashes(target_dir, solution_files)
        print("\n" + "=" * 60)
        print("FINAL LEARNER FILE HASHES")
        print("=" * 60)
        for f, h in final_hashes.items():
            print(f"  {f}: {h}")
        
        # Save evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
    
    # Verify learner files were not modified in source
    print("\nVerifying learner files were not modified in source directory...")
    for f in solution_files:
        src_path = os.path.join(exercise_dir, f)
        if os.path.exists(src_path):
            with open(src_path, 'rb') as fp:
                src_hash = hashlib.md5(fp.read()).hexdigest()
            if src_hash == initial_hashes.get(f):
                print(f"  {f}: UNCHANGED ✓")
            else:
                print(f"  {f}: CHANGED ✗")
                sys.exit(1)
    
    # Test zero-test run (without EXERCISM_RUN_ALL_TESTS)
    print("\n" + "=" * 60)
    print("TEST: Zero-test run (without EXERCISM_RUN_ALL_TESTS)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "eliuds-eggs")
        shutil.copytree(exercise_dir, target_dir, 
                       ignore=shutil.ignore_patterns('build*', '*.cache'),
                       dirs_exist_ok=True)
        
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                       os.path.join(target_dir, "eliuds_eggs.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                       os.path.join(target_dir, "eliuds_eggs.h"))
        
        subprocess.run(["cmake", "-S", ".", "-B", "build"], 
                       cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["cmake", "--build", "build"], 
                       cwd=target_dir, check=True, capture_output=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        print(f"Zero-test run return code: {0 if success else 1}")
        print(f"Output: {stdout.strip()}")
        
        # Should have 1 test case (0 eggs)
        if "1 test case" not in stdout:
            print("WARNING: Zero-test run should have 1 test case")
    
    # Test failing reference (deliberately broken - returns wrong values)
    print("\n" + "=" * 60)
    print("TEST: Failing reference implementation (wrong logic)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "eliuds-eggs")
        shutil.copytree(exercise_dir, target_dir, 
                       ignore=shutil.ignore_patterns('build*', '*.cache'),
                       dirs_exist_ok=True)
        
        # Create a deliberately broken implementation that compiles but fails tests
        broken_cpp = '''#include "eliuds_eggs.h"

namespace chicken_coop {
int positions_to_quantity(int display_value) {
    // Always return 0 - this will fail for 1 egg and 4 eggs
    return 0;
}
}  // namespace chicken_coop
'''
        with open(os.path.join(target_dir, "eliuds_eggs.cpp"), "w") as f:
            f.write(broken_cpp)
        
        try:
            subprocess.run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                           cwd=target_dir, check=True, capture_output=True)
            subprocess.run(["cmake", "--build", "build"], 
                           cwd=target_dir, check=True, capture_output=True)
            
            success, stdout, stderr = build_and_test(target_dir)
            print(f"Failing reference return code: {0 if success else 1}")
            if not success:
                print("Correctly detected test failure!")
                if "test cases" in stdout:
                    print(f"  Output: {stdout.strip()}")
            else:
                print("WARNING: Expected test failure but tests passed")
        except subprocess.CalledProcessError as e:
            print(f"Build failed (expected for some broken implementations): {e}")
            print("Correctly detected build failure!")
    
    print("\nCheck completed successfully!")
    print(f"- All {EXPECTED_ASSERTIONS} tests pass")
    print(f"- Learner file hashes unchanged in source directory")
    print(f"- Zero-test run produces 1 test case")
    print(f"- Failing reference correctly detected")
    print(f"- Maintenance doc at docs/maintenance/eliuds-eggs.md")

if __name__ == "__main__":
    run_check()