#!/usr/bin/env python3
"""
Isolated runner for exercises/practice/resistor-color (Task R20-T029).
Runs test suite against reference implementation in an isolated temporary directory,
ensuring learner starter stubs remain completely untouched.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "resistor-color")
CONFIG_JSON = os.path.join(EXERCISE_DIR, ".meta", "config.json")

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_learner_file_hashes():
    with open(CONFIG_JSON, "r") as f:
        config = json.load(f)
    hashes = {}
    for rel_path in config["files"]["solution"]:
        full_path = os.path.join(EXERCISE_DIR, rel_path)
        if os.path.isfile(full_path):
            hashes[rel_path] = hash_file(full_path)
    return hashes

def run_isolated_test(exercise_dir=EXERCISE_DIR, example_override_dir=None, catch_args=None, require_nonzero=False):
    pre_hashes = get_learner_file_hashes()
    temp_dir = tempfile.mkdtemp(prefix="resistor_color_runner_")

    try:
        with open(CONFIG_JSON, "r") as f:
            config = json.load(f)

        dest_dir = os.path.join(temp_dir, "resistor-color")
        shutil.copytree(exercise_dir, dest_dir)

        # Substitute reference implementation
        for sol_rel, ex_rel in zip(config["files"]["solution"], config["files"]["example"]):
            src_file = os.path.join(example_override_dir or dest_dir, ex_rel)
            shutil.copyfile(src_file, os.path.join(dest_dir, sol_rel))

        build_dir = os.path.join(dest_dir, "build")
        cmake_config = subprocess.run(
            ["cmake", "-S", dest_dir, "-B", build_dir, "-DEXERCISM_RUN_ALL_TESTS=ON"],
            capture_output=True,
            text=True
        )
        if cmake_config.returncode != 0:
            return {
                "success": False,
                "exit_code": cmake_config.returncode,
                "error": f"CMake configure failed:\n{cmake_config.stderr}",
                "tests_executed": 0
            }

        cmake_build = subprocess.run(
            ["cmake", "--build", build_dir],
            capture_output=True,
            text=True
        )
        if cmake_build.returncode != 0:
            return {
                "success": False,
                "exit_code": cmake_build.returncode,
                "error": f"CMake build failed:\n{cmake_build.stderr}",
                "tests_executed": 0
            }

        test_bin = os.path.join(build_dir, "resistor-color")
        cmd = [test_bin, "-s"]
        if catch_args:
            cmd.extend(catch_args)

        test_run = subprocess.run(cmd, capture_output=True, text=True)
        stdout = test_run.stdout

        # Parse test execution count
        match = re.search(r"assertions in (\d+) test cases", stdout)
        tests_count = int(match.group(1)) if match else 0

        # Zero test run detection
        if tests_count == 0 or "No tests ran" in stdout or "0 assertions in 0 test cases" in stdout:
            return {
                "success": False,
                "exit_code": 3,
                "error": "Zero test cases executed",
                "tests_executed": 0,
                "stdout": stdout
            }

        return {
            "success": test_run.returncode == 0,
            "exit_code": test_run.returncode,
            "stdout": stdout,
            "tests_executed": tests_count
        }

    finally:
        # Cleanup temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Verify learner hashes are strictly identical
        post_hashes = get_learner_file_hashes()
        for f, h in pre_hashes.items():
            if post_hashes.get(f) != h:
                raise RuntimeError(f"CRITICAL: Learner file {f} was modified! Hash before: {h}, after: {post_hashes.get(f)}")

def main():
    parser = argparse.ArgumentParser(description="Isolated runner for resistor-color")
    parser.add_argument("catch_args", nargs="*", help="Optional arguments passed to Catch2")
    args = parser.parse_args()

    result = run_isolated_test(catch_args=args.catch_args)
    if result["success"]:
        print(f"Isolated test execution SUCCESS: {result['tests_executed']} test cases passed.")
        print(result.get("stdout", ""))
        sys.exit(0)
    else:
        print(f"Isolated test execution FAILED (exit code {result['exit_code']}): {result.get('error', '')}", file=sys.stderr)
        if "stdout" in result:
            print(result["stdout"], file=sys.stderr)
        sys.exit(result["exit_code"])

if __name__ == "__main__":
    main()
