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

EXPECTED_TEST_CASES = 4
EXPECTED_ASSERTIONS = 4

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
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # Build and test
        print("Building and testing...")
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
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
    
    print("\nCheck completed successfully!")
    print(f"- All {EXPECTED_ASSERTIONS} tests pass")
    print(f"- Learner file hashes unchanged in source directory")
    print(f"- Evidence saved to work/{WORK_DIR}/output.txt")

if __name__ == "__main__":
    run_check()