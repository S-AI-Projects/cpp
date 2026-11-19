#!/usr/bin/env python3
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def hash_files(file_paths):
    hashes = {}
    for path in file_paths:
        with open(path, "rb") as f:
            hashes[path] = hashlib.sha256(f.read()).hexdigest()
    return hashes

def build_and_run(exercise_dir, impl_cpp, impl_h, label):
    temp_dir = tempfile.mkdtemp(prefix=f"rcd_{label}_")
    try:
        temp_ex = os.path.join(temp_dir, "resistor-color-duo")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        shutil.copy2(impl_cpp, os.path.join(temp_ex, "resistor_color_duo.cpp"))
        shutil.copy2(impl_h, os.path.join(temp_ex, "resistor_color_duo.h"))

        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)

        res = subprocess.run([os.path.join(bld, "resistor-color-duo")], capture_output=True, text=True)
        assert res.returncode == 0, f"Execution failed for {label}: {res.stderr}"
        return res.stdout
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/resistor-color-duo")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    results = []
    results.append("=== R20-T006 Resistor Color Duo Check ===")

    # 1. Verify hints.md documentation
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    assert os.path.isfile(hints_path), "hints.md missing"
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_text = f.read()
    assert "Approach Selection" in hints_text, "Approach selection section missing"
    assert "std::find" in hints_text or "Vector" in hints_text, "Approach 1 missing"
    assert "std::unordered_map" in hints_text or "map" in hints_text, "Approach 2 missing"
    results.append("Verified Approach Selection documentation in hints.md.")

    # 2. Record initial hashes of learner files
    learner_files = [
        os.path.join(exercise_dir, "resistor_color_duo.cpp"),
        os.path.join(exercise_dir, "resistor_color_duo.h")
    ]
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        results.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Check learner stub in working tree is unsolved
    with open(os.path.join(exercise_dir, "resistor_color_duo.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "color_code" not in stub_text and "color_map" not in stub_text, "Learner stub was modified!"
    results.append("Verified learner stub in working tree is unsolved.")

    # 3. Test reference implementation
    ref_cpp = os.path.join(exercise_dir, ".meta/example.cpp")
    ref_h = os.path.join(exercise_dir, ".meta/example.h")
    stdout_ref = build_and_run(exercise_dir, ref_cpp, ref_h, "ref")

    # Verify named cases in test source
    named_cases = ["Brown and black", "Blue and grey", "White and red"]
    with open(os.path.join(exercise_dir, "resistor_color_duo_test.cpp"), "r", encoding="utf-8") as f:
        test_src = f.read()
    for case in named_cases:
        assert case in test_src, f"Named case '{case}' missing from tests"
        results.append(f"Verified anchor case '{case}' is present.")

    m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", stdout_ref)
    assert m is not None, "Could not parse Catch2 summary"
    num_assertions = int(m.group(1))
    num_tests = int(m.group(2))
    assert num_tests >= 7, f"Expected at least 7 test cases, got {num_tests}"
    results.append(f"Reference implementation passed all {num_tests} tests ({num_assertions} assertions).")

    # 4. Test experimental Approach 1 (Vector search)
    app1_cpp = os.path.join(work_dir, "approach_vector.cpp")
    stdout_app1 = build_and_run(exercise_dir, app1_cpp, ref_h, "app1")
    assert "All tests passed" in stdout_app1, "Approach 1 (vector) failed tests"
    results.append("Experimental Approach 1 (vector/std::find) passed all tests.")

    # 5. Test experimental Approach 2 (Map lookup)
    app2_cpp = os.path.join(work_dir, "approach_map.cpp")
    stdout_app2 = build_and_run(exercise_dir, app2_cpp, ref_h, "app2")
    assert "All tests passed" in stdout_app2, "Approach 2 (unordered_map) failed tests"
    results.append("Experimental Approach 2 (unordered_map) passed all tests.")

    # 6. Verify learner files remain identical
    final_hashes = hash_files(learner_files)
    assert initial_hashes == final_hashes, "Learner files changed during run!"
    results.append("Verified: learner file hashes identical before and after run.")

    # Write results
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")

    print("\n".join(results))
    print(f"[✓] Check passed! Evidence saved to {results_path}")

if __name__ == "__main__":
    main()
