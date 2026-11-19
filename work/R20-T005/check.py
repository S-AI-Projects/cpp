#!/usr/bin/env python3
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

def hash_files(file_paths):
    hashes = {}
    for path in file_paths:
        with open(path, "rb") as f:
            hashes[path] = hashlib.sha256(f.read()).hexdigest()
    return hashes

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/matching-brackets")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    results = []
    results.append("=== R20-T005 Matching Brackets Scaling Check ===")

    # 1. Verify complexity/invariant comment in example.cpp
    ex_cpp = os.path.join(exercise_dir, ".meta/example.cpp")
    with open(ex_cpp, "r", encoding="utf-8") as f:
        ex_content = f.read()
    assert "Time Complexity: O(n)" in ex_content, "Complexity comment missing"
    assert "Space Complexity: O(n)" in ex_content, "Space complexity comment missing"
    assert "std::stack<char>" in ex_content, "Invariant comment missing"
    results.append("Found complexity and invariant documentation in example.cpp.")

    # 2. Check documentation file
    doc_path = os.path.join(repo_root, "docs/maintenance/matching-brackets.md")
    assert os.path.isfile(doc_path), "docs/maintenance/matching-brackets.md missing"
    results.append(f"Found maintenance scaling doc at {doc_path}")

    # 3. Record initial hashes of learner files
    learner_files = [
        os.path.join(exercise_dir, "matching_brackets.cpp"),
        os.path.join(exercise_dir, "matching_brackets.h")
    ]
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        results.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Check learner stub in working tree is unsolved
    with open(os.path.join(exercise_dir, "matching_brackets.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "stack" not in stub_text, "Learner stub was modified!"
    results.append("Verified learner stub in working tree is unsolved.")

    # 4. Build and test in temporary scratch directory
    temp_dir = tempfile.mkdtemp(prefix="mb_check_")
    try:
        temp_ex = os.path.join(temp_dir, "matching-brackets")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        # Substitute reference solution files
        shutil.copy2(os.path.join(temp_ex, ".meta/example.cpp"), os.path.join(temp_ex, "matching_brackets.cpp"))
        shutil.copy2(os.path.join(temp_ex, ".meta/example.h"), os.path.join(temp_ex, "matching_brackets.h"))

        # Configure & build CMake
        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)

        # Run test executable
        res = subprocess.run([os.path.join(bld, "matching-brackets")], capture_output=True, text=True)
        assert res.returncode == 0, f"Tests failed: {res.stderr}"

        # Verify named cases in test source / Catch2 output
        named_cases = [
            "paired_nested_brackets",
            "paired_wrong_nested_brackets",
            "paired_incomplete_brackets"
        ]
        with open(os.path.join(exercise_dir, "matching_brackets_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()
        for case in named_cases:
            assert case in test_src, f"Named case '{case}' missing from tests"
            results.append(f"Verified named case: '{case}' is present and verified.")

        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", res.stdout)
        assert m is not None, "Could not parse Catch2 output summary"
        num_assertions = int(m.group(1))
        num_tests = int(m.group(2))
        assert num_tests >= 19, f"Expected at least 19 test cases, got {num_tests}"
        results.append(f"All {num_tests} tests passed successfully ({num_assertions} assertions).")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 5. Verify learner files remain unchanged
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
