#!/usr/bin/env python3
"""
Automated verification script for Task R20-T029:
- Checks learner stubs remain unsolved.
- Tests isolated runner across 3 scenarios:
  1. Real reference (must pass, 4 test cases including Black, White, Orange).
  2. Deliberately failing reference (must return non-zero exit code).
  3. Empty test selection (must return non-zero exit code).
- Asserts learner file hashes remain identical across all scenarios.
- Verifies documentation in docs/maintenance/resistor-color.md.
"""

import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXERCISE_DIR = os.path.join(REPO_ROOT, "exercises", "practice", "resistor-color")
DOCS_MD = os.path.join(REPO_ROOT, "docs", "maintenance", "resistor-color.md")
WORK_DIR = os.path.join(REPO_ROOT, "work", "R20-T029")
CASES_JSON = os.path.join(WORK_DIR, "cases.json")
REPORT_JSON = os.path.join(WORK_DIR, "report.json")

spec = importlib.util.spec_from_file_location("r20_t029", os.path.join(REPO_ROOT, "tools", "course_checks", "r20-t029.py"))
r20_t029_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r20_t029_mod)
run_isolated_test = r20_t029_mod.run_isolated_test
get_learner_file_hashes = r20_t029_mod.get_learner_file_hashes

def get_tool_versions():
    cmake_ver = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    cxx_ver = subprocess.run(["c++", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    py_ver = sys.version.split()[0]
    return {"cmake": cmake_ver, "c++": cxx_ver, "python": py_ver}

def check_learner_stub():
    print("[1/5] Verifying learner stubs are unsolved...")
    stub_file = os.path.join(EXERCISE_DIR, "resistor_color.cpp")
    with open(stub_file, "r") as f:
        content = f.read()
    assert "TODO" in content, "Learner stub does not contain TODO!"
    assert "black" not in content.lower(), "Learner stub contains solution details!"
    print("      Learner stub is unsolved.")

def test_runner_scenarios():
    print("[2/5] Testing isolated runner across scenarios...")
    initial_hashes = get_learner_file_hashes()

    with open(CASES_JSON, "r") as f:
        cases_data = json.load(f)
    named_cases = cases_data["named_cases"]

    scenario_reports = {}

    # Scenario 1: Real reference
    print("      Testing Scenario 1: Real reference...")
    res1 = run_isolated_test()
    assert res1["success"] is True, f"Real reference run failed: {res1}"
    assert res1["exit_code"] == 0, f"Expected exit code 0, got {res1['exit_code']}"
    assert res1["tests_executed"] >= 4, f"Expected >= 4 tests, got {res1['tests_executed']}"
    for named in named_cases:
        assert named in res1["stdout"], f"Named case '{named}' missing from output!"

    post_hashes_1 = get_learner_file_hashes()
    assert post_hashes_1 == initial_hashes, "Learner hashes changed after real reference run!"
    scenario_reports["real_reference"] = {
        "status": "PASS",
        "exit_code": res1["exit_code"],
        "tests_executed": res1["tests_executed"]
    }

    # Scenario 2: Deliberately failing reference
    print("      Testing Scenario 2: Deliberately failing reference...")
    with tempfile.TemporaryDirectory() as failing_dir:
        meta_dir = os.path.join(failing_dir, ".meta")
        os.makedirs(meta_dir)
        # Copy original header
        shutil.copyfile(os.path.join(EXERCISE_DIR, ".meta", "example.h"), os.path.join(meta_dir, "example.h"))
        # Create mutated example that returns wrong code
        with open(os.path.join(meta_dir, "example.cpp"), "w") as f:
            f.write('''#include "resistor_color.h"
namespace resistor_color {
int color_code(std::string const&) {
    return 999; // Deliberate failure
}
std::vector<std::string> colors() {
    return {"wrong"};
}
}
''')

        res2 = run_isolated_test(example_override_dir=failing_dir)
        assert res2["success"] is False, "Deliberately failing reference unexpectedly succeeded!"
        assert res2["exit_code"] != 0, f"Expected non-zero exit code, got {res2['exit_code']}"

    post_hashes_2 = get_learner_file_hashes()
    assert post_hashes_2 == initial_hashes, "Learner hashes changed after failing reference run!"
    scenario_reports["deliberately_failing_reference"] = {
        "status": "PASS_DETECTED_FAILURE",
        "exit_code": res2["exit_code"]
    }

    # Scenario 3: Empty test selection (zero-test run)
    print("      Testing Scenario 3: Empty test selection...")
    res3 = run_isolated_test(catch_args=["~*"])
    assert res3["success"] is False, "Zero test run unexpectedly succeeded!"
    assert res3["exit_code"] != 0, f"Expected non-zero exit code for zero tests, got {res3['exit_code']}"

    post_hashes_3 = get_learner_file_hashes()
    assert post_hashes_3 == initial_hashes, "Learner hashes changed after zero-test run!"
    scenario_reports["empty_test_selection"] = {
        "status": "PASS_DETECTED_ZERO_TESTS",
        "exit_code": res3["exit_code"]
    }

    print("      All scenarios verified.")
    return scenario_reports, initial_hashes

def check_temp_cleanup():
    print("[3/5] Verifying temporary files cleanup...")
    temp_pattern = os.path.join(tempfile.gettempdir(), "resistor_color_runner_*")
    leaked = glob.glob(temp_pattern)
    assert len(leaked) == 0, f"Leaked temporary directories found: {leaked}"
    print("      No leaked temporary files detected.")

def check_documentation():
    print("[4/5] Verifying maintenance documentation...")
    assert os.path.isfile(DOCS_MD), f"Maintenance doc {DOCS_MD} missing!"
    with open(DOCS_MD, "r") as f:
        text = f.read()
    assert "tools/course_checks/r20-t029.py" in text, "Missing runner command in docs!"
    assert "Tool Requirements" in text or "compiler" in text.lower(), "Missing tool requirements in docs!"
    print("      Maintenance documentation verified.")

def main():
    tools = get_tool_versions()
    check_learner_stub()
    scenarios, hashes = test_runner_scenarios()
    check_temp_cleanup()
    check_documentation()

    report = {
        "task": "R20-T029",
        "exercise": "resistor-color",
        "tools": tools,
        "learner_file_hashes": hashes,
        "scenarios": scenarios,
        "learner_stubs_intact": True,
        "status": "PASS"
    }

    with open(REPORT_JSON, "w") as f:
        json.dump(report, f, indent=2)

    print("[5/5] All checks passed successfully! Report written to report.json.")

if __name__ == "__main__":
    main()
