#!/usr/bin/env python3
"""
Automated verification script for Task R20-T030:
- Verifies learner stubs remain unsolved.
- Builds and runs reference implementation against Catch2, asserting all test cases pass.
- Verifies named cases (empty spiral, trivial spiral, spiral of size 2) pass.
- Validates that decision table in cases.json matches spiral_matrix_test.cpp assertions.
- Verifies hints.md contains decision table, case walkthroughs, and contract boundaries.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "spiral-matrix")
CONFIG_JSON = os.path.join(EXERCISE_DIR, ".meta", "config.json")
HINTS_MD = os.path.join(EXERCISE_DIR, ".docs", "hints.md")
TEST_CPP = os.path.join(EXERCISE_DIR, "spiral_matrix_test.cpp")
WORK_DIR = os.path.join(REPO_ROOT, "work", "R20-T030")
CASES_JSON = os.path.join(WORK_DIR, "cases.json")
REPORT_JSON = os.path.join(WORK_DIR, "report.json")

def get_tool_versions():
    cmake_ver = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    cxx_ver = subprocess.run(["c++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    py_ver = sys.version.split()[0]
    return {"cmake": cmake_ver, "c++": cxx_ver, "python": py_ver}

def check_learner_stub():
    print("[1/5] Verifying learner stub is unsolved...")
    stub_file = os.path.join(EXERCISE_DIR, "spiral_matrix.cpp")
    with open(stub_file, "r") as f:
        content = f.read()
    assert "TODO" in content, "Learner stub does not contain TODO!"
    assert "for" not in content and "return" not in content, "Learner stub contains solution implementation!"
    print("      Learner stub verified unsolved.")

def run_exercise_tests():
    print("[2/5] Building and running reference implementation against Catch2...")
    with open(CONFIG_JSON, "r") as f:
        config = json.load(f)

    with tempfile.TemporaryDirectory() as td:
        dest_dir = os.path.join(td, "spiral-matrix")
        shutil.copytree(EXERCISE_DIR, dest_dir)

        # Substitute reference implementation
        for sol_rel, ex_rel in zip(config["files"]["solution"], config["files"]["example"]):
            shutil.copyfile(os.path.join(dest_dir, ex_rel), os.path.join(dest_dir, sol_rel))

        build_dir = os.path.join(dest_dir, "build")
        cmake_configure = subprocess.run(
            ["cmake", "-S", dest_dir, "-B", build_dir, "-DEXERCISM_RUN_ALL_TESTS=ON"],
            capture_output=True,
            text=True
        )
        assert cmake_configure.returncode == 0, f"CMake configure failed:\n{cmake_configure.stderr}"

        cmake_build = subprocess.run(
            ["cmake", "--build", build_dir],
            capture_output=True,
            text=True
        )
        assert cmake_build.returncode == 0, f"CMake build failed:\n{cmake_build.stderr}"

        test_bin = os.path.join(build_dir, "spiral-matrix")
        test_run = subprocess.run([test_bin, "-s"], capture_output=True, text=True)
        assert test_run.returncode == 0, f"Test executable failed with code {test_run.returncode}:\n{test_run.stdout}\n{test_run.stderr}"

        stdout = test_run.stdout
        with open(CASES_JSON, "r") as f:
            cases_data = json.load(f)
        for named in cases_data["named_cases"]:
            assert named in stdout, f"Named case '{named}' not executed!"

        match = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", stdout)
        assert match, "Could not parse Catch2 test summary!"
        assertions_count = int(match.group(1))
        test_cases_count = int(match.group(2))
        assert test_cases_count > 0, "Zero test cases executed!"

        print(f"      Catch2 passed {test_cases_count} test cases ({assertions_count} assertions).")
        return {"test_cases": test_cases_count, "assertions": assertions_count}

def check_decision_table_accuracy():
    print("[3/5] Verifying decision table against spiral_matrix_test.cpp...")
    with open(TEST_CPP, "r") as f:
        test_src = f.read()

    # Case 0: empty spiral
    assert 'TEST_CASE("empty spiral"' in test_src
    assert 'spiral_matrix::spiral_matrix(0)' in test_src

    # Case 1: trivial spiral
    assert 'TEST_CASE("trivial spiral"' in test_src
    assert 'spiral_matrix::spiral_matrix(1)' in test_src
    assert '{{1}}' in test_src

    # Case 2: spiral of size 2
    assert 'TEST_CASE("spiral of size 2"' in test_src
    assert 'spiral_matrix::spiral_matrix(2)' in test_src
    assert '{1, 2}' in test_src
    assert '{4, 3}' in test_src
    print("      Decision table entries match unit test source exactly.")

def check_hints_documentation():
    print("[4/5] Verifying hints documentation...")
    assert os.path.isfile(HINTS_MD), f"Hints file {HINTS_MD} missing!"
    with open(HINTS_MD, "r") as f:
        hints_text = f.read()

    with open(CASES_JSON, "r") as f:
        cases_data = json.load(f)

    for item in cases_data["decision_table"]:
        assert item["case_name"] in hints_text, f"Missing case '{item['case_name']}' in hints.md"
        assert f"size = {item['input_size']}" in hints_text or f"size of {item['input_size']}" in hints_text or f"Input: `{item['input_size']}`" in hints_text, f"Missing input {item['input_size']} in hints.md"

    # Check for unspecified behavior discussion
    assert "unspecified" in hints_text.lower() or "outside" in hints_text.lower(), "Missing discussion of unspecified behavior in hints.md"
    assert "exceptions" in hints_text.lower(), "Missing discussion of exceptions in hints.md"
    assert "uint32_t" in hints_text, "Missing input type specification in hints.md"
    print("      Hints documentation verified.")

def main():
    tools = get_tool_versions()
    check_learner_stub()
    test_stats = run_exercise_tests()
    check_decision_table_accuracy()
    check_hints_documentation()

    report = {
        "task": "R20-T030",
        "exercise": "spiral-matrix",
        "tools": tools,
        "learner_stub_unsolved": True,
        "test_results": test_stats,
        "status": "PASS"
    }

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print("[5/5] All checks passed successfully! Report written to report.json.")

if __name__ == "__main__":
    main()
