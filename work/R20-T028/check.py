#!/usr/bin/env python3
"""
Automated verification script for Task R20-T028:
- Verifies learner stubs remain unsolved.
- Validates the real config.json using tools/course_checks/r20-t028.py.
- Asserts that all three deliberately invalid metadata fixtures fail for the intended reason.
- Runs reference implementation against Catch2, asserting named cases pass.
- Verifies docs/maintenance/raindrops.md names stubs, reference, tests, and generated artifacts.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
import importlib.util
spec = importlib.util.spec_from_file_location("r20_t028", os.path.join(REPO_ROOT, "tools", "course_checks", "r20-t028.py"))
r20_t028_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r20_t028_mod)
validate_exercise_config = r20_t028_mod.validate_exercise_config

EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "raindrops")
CONFIG_JSON = os.path.join(EXERCISE_DIR, ".meta", "config.json")
DOCS_MD = os.path.join(REPO_ROOT, "docs", "maintenance", "raindrops.md")
WORK_DIR = os.path.join(REPO_ROOT, "work", "R20-T028")
CASES_JSON = os.path.join(WORK_DIR, "cases.json")
REPORT_JSON = os.path.join(WORK_DIR, "report.json")

def get_tool_versions():
    cmake_ver = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    cxx_ver = subprocess.run(["c++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    py_ver = sys.version.split()[0]
    return {"cmake": cmake_ver, "c++": cxx_ver, "python": py_ver}

def check_learner_stub():
    print("[1/5] Verifying learner stubs are unsolved...")
    stub_file = os.path.join(EXERCISE_DIR, "raindrops.cpp")
    with open(stub_file, "r") as f:
        content = f.read()
    assert "TODO" in content, "Learner stub does not contain TODO!"
    assert "Pling" not in content, "Learner stub contains solution implementation!"
    print("      Learner stub verified unsolved.")

def check_config_fixtures():
    print("[2/5] Testing config validation and invalid fixtures...")
    # Real config must pass
    real_results = validate_exercise_config(EXERCISE_DIR)
    assert len(real_results["solution"]) == 2, "Expected 2 solution files"
    assert len(real_results["test"]) == 1, "Expected 1 test file"
    assert len(real_results["example"]) == 2, "Expected 2 example files"
    print("      Real config passed successfully.")

    with open(CASES_JSON, "r") as f:
        cases_data = json.load(f)

    fixture_results = {}
    for name, fixture in cases_data["invalid_fixtures"].items():
        expected_err = fixture["expected_error"]
        dummy_config = {"files": fixture["files"]}
        caught = False
        try:
            validate_exercise_config(EXERCISE_DIR, config_override=dummy_config)
        except Exception as e:
            err_type = type(e).__name__
            assert err_type == expected_err, f"Fixture '{name}' expected {expected_err}, got {err_type}: {e}"
            caught = True
            fixture_results[name] = {"status": "FAILED_AS_EXPECTED", "error": err_type, "message": str(e)}

        assert caught, f"Fixture '{name}' unexpectedly passed without error!"
        print(f"      Fixture '{name}' failed as expected with {expected_err}.")

    return fixture_results

def run_exercise_tests():
    print("[3/5] Building and running reference implementation against Catch2...")
    with open(CONFIG_JSON, "r") as f:
        config = json.load(f)

    with tempfile.TemporaryDirectory() as td:
        dest_dir = os.path.join(td, "raindrops")
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

        test_bin = os.path.join(build_dir, "raindrops")
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

def check_documentation():
    print("[4/5] Verifying maintenance documentation...")
    assert os.path.isfile(DOCS_MD), f"Maintenance doc {DOCS_MD} missing!"
    with open(DOCS_MD, "r") as f:
        text = f.read()

    assert "raindrops.cpp" in text, "Documentation does not mention raindrops.cpp"
    assert "raindrops_test.cpp" in text, "Documentation does not mention raindrops_test.cpp"
    assert ".meta/example.cpp" in text, "Documentation does not mention .meta/example.cpp"
    assert "Generated Artifacts" in text or "generated" in text.lower(), "Documentation does not distinguish generated artifacts"
    print("      Maintenance documentation verified.")

def main():
    tools = get_tool_versions()
    check_learner_stub()
    fixture_results = check_config_fixtures()
    test_stats = run_exercise_tests()
    check_documentation()

    report = {
        "task": "R20-T028",
        "exercise": "raindrops",
        "tools": tools,
        "learner_stub_unsolved": True,
        "config_fixtures": fixture_results,
        "test_results": test_stats,
        "status": "PASS"
    }

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print("[5/5] All checks passed successfully! Report written to report.json.")

if __name__ == "__main__":
    main()
