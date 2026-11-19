#!/usr/bin/env python3
"""
Automated verification script for Task R20-T027:
- Builds and runs reference implementation against Catch2 test suite.
- Checks learner stubs are still unsolved.
- Asserts that all enabled test cases, including named cases, pass.
- Compiles and runs micro-example, asserting both outputs.
- Verifies published hints.md contains matching outputs, construct name, and cppreference link.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "parallel-letter-frequency")
CONFIG_JSON = os.path.join(EXERCISE_DIR, ".meta", "config.json")
HINTS_MD = os.path.join(EXERCISE_DIR, ".docs", "hints.md")
WORK_DIR = os.path.join(REPO_ROOT, "work", "R20-T027")
MICRO_EXAMPLE = os.path.join(WORK_DIR, "micro_example.cpp")
CASES_JSON = os.path.join(WORK_DIR, "cases.json")
REPORT_JSON = os.path.join(WORK_DIR, "report.json")

def get_tool_versions():
    cmake_ver = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    cxx_ver = subprocess.run(["c++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    py_ver = sys.version.split()[0]
    return {"cmake": cmake_ver, "c++": cxx_ver, "python": py_ver}

def check_learner_stub():
    print("[1/5] Verifying learner stub is unsolved...")
    stub_file = os.path.join(EXERCISE_DIR, "parallel_letter_frequency.cpp")
    with open(stub_file, "r") as f:
        content = f.read()
    # Stub should only contain include and empty namespace or TODO
    assert "frequency(" not in content or "TODO" in content, "Learner stub contains solution implementation!"
    print("      Learner stub is unsolved.")

def run_exercise_tests():
    print("[2/5] Building and running reference implementation against Catch2...")
    with open(CONFIG_JSON, "r") as f:
        config = json.load(f)

    with tempfile.TemporaryDirectory() as td:
        dest_dir = os.path.join(td, "parallel-letter-frequency")
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

        test_bin = os.path.join(build_dir, "parallel-letter-frequency")
        test_run = subprocess.run([test_bin, "-s"], capture_output=True, text=True)
        assert test_run.returncode == 0, f"Test executable failed with code {test_run.returncode}:\n{test_run.stdout}\n{test_run.stderr}"

        stdout = test_run.stdout
        # Verify named cases
        with open(CASES_JSON, "r") as f:
            cases_data = json.load(f)
        for named in cases_data["named_cases"]:
            assert named in stdout, f"Named case '{named}' not executed!"

        # Extract number of test cases and assertions
        match = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", stdout)
        assert match, "Could not parse Catch2 test summary!"
        assertions_count = int(match.group(1))
        test_cases_count = int(match.group(2))
        assert test_cases_count > 0, "Zero test cases executed!"

        print(f"      Catch2 passed {test_cases_count} test cases ({assertions_count} assertions).")
        return {"test_cases": test_cases_count, "assertions": assertions_count}

def check_micro_example():
    print("[3/5] Compiling and running micro-example...")
    with open(CASES_JSON, "r") as f:
        cases_data = json.load(f)
    exp1 = cases_data["micro_example"]["expression_1"]["expected_output"]
    exp2 = cases_data["micro_example"]["expression_2"]["expected_output"]

    with tempfile.TemporaryDirectory() as td:
        exe_path = os.path.join(td, "micro_example")
        comp = subprocess.run(
            ["c++", "-std=c++17", MICRO_EXAMPLE, "-o", exe_path],
            capture_output=True,
            text=True
        )
        assert comp.returncode == 0, f"Micro-example compilation failed:\n{comp.stderr}"

        run_res = subprocess.run([exe_path], capture_output=True, text=True)
        assert run_res.returncode == 0, f"Micro-example execution failed:\n{run_res.stderr}"

        lines = [line.strip() for line in run_res.stdout.strip().splitlines() if line.strip()]
        assert len(lines) == 2, f"Expected 2 output lines from micro-example, got: {lines}"
        assert lines[0] == exp1, f"Expression 1 mismatch: expected '{exp1}', got '{lines[0]}'"
        assert lines[1] == exp2, f"Expression 2 mismatch: expected '{exp2}', got '{lines[1]}'"

        print(f"      Expression 1 output: '{lines[0]}'")
        print(f"      Expression 2 output: '{lines[1]}'")
        return {"expression_1": lines[0], "expression_2": lines[1]}

def check_hints_documentation(micro_outputs):
    print("[4/5] Verifying hints documentation...")
    assert os.path.isfile(HINTS_MD), f"Hints file {HINTS_MD} does not exist!"
    with open(HINTS_MD, "r") as f:
        hints_text = f.read()

    # Check construct name
    assert "const reference" in hints_text.lower() or "const&" in hints_text, "Hints does not mention const reference construct!"
    # Check cppreference link
    assert "cppreference.com" in hints_text, "Hints does not contain a link to cppreference!"
    # Check micro-example outputs agree
    assert micro_outputs["expression_1"] in hints_text, "Hints does not include Expression 1 expected output!"
    assert micro_outputs["expression_2"] in hints_text, "Hints does not include Expression 2 expected output!"
    print("      Hints documentation verified.")

def main():
    tools = get_tool_versions()
    check_learner_stub()
    test_stats = run_exercise_tests()
    micro_outputs = check_micro_example()
    check_hints_documentation(micro_outputs)

    report = {
        "task": "R20-T027",
        "exercise": "parallel-letter-frequency",
        "tools": tools,
        "learner_stub_unsolved": True,
        "test_results": test_stats,
        "micro_example_outputs": micro_outputs,
        "status": "PASS"
    }

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print("[5/5] All checks passed successfully! Report written to report.json.")

if __name__ == "__main__":
    main()
