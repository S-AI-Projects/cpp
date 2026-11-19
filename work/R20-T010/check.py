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

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/meetup")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    results = []
    results.append("=== R20-T010 Meetup Contract Cases Check ===")

    # 1. Verify hints.md documentation and decision table
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    assert os.path.isfile(hints_path), "hints.md missing"
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_text = f.read()

    assert "Decision Table" in hints_text, "Decision table missing in hints.md"
    assert "monteenth_of_May_2013" in hints_text, "monteenth_of_May_2013 missing from hints.md"
    assert "2013-05-13" in hints_text, "2013-05-13 outcome missing"
    assert "monteenth_of_August_2013" in hints_text, "monteenth_of_August_2013 missing from hints.md"
    assert "2013-08-19" in hints_text, "2013-08-19 outcome missing"
    assert "monteenth_of_September_2013" in hints_text, "monteenth_of_September_2013 missing from hints.md"
    assert "2013-09-16" in hints_text, "2013-09-16 outcome missing"
    assert "Unspecified Behavior" in hints_text, "Unspecified behavior section missing"
    results.append("Verified hints.md with input/output walkthrough, decision table, and contract boundaries.")

    # 2. Record initial hashes of learner files
    learner_files = [
        os.path.join(exercise_dir, "meetup.cpp"),
        os.path.join(exercise_dir, "meetup.h")
    ]
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        results.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Check learner stub in working tree is unsolved
    with open(os.path.join(exercise_dir, "meetup.h"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "teenth_day" not in stub_text and "scheduler" not in stub_text, "Learner stub was modified!"
    results.append("Verified learner stub in working tree is unsolved.")

    # 3. Build and test reference implementation in temp directory
    temp_dir = tempfile.mkdtemp(prefix="meetup_check_")
    try:
        temp_ex = os.path.join(temp_dir, "meetup")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        shutil.copy2(os.path.join(temp_ex, ".meta/example.h"), os.path.join(temp_ex, "meetup.h"))
        with open(os.path.join(temp_ex, "meetup.cpp"), "w", encoding="utf-8") as f:
            f.write("// header-only reference\n")

        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)

        res = subprocess.run([os.path.join(bld, "meetup")], capture_output=True, text=True)
        assert res.returncode == 0, f"Tests failed: {res.stderr}"

        # Verify anchor cases in test source
        named_cases = [
            "monteenth_of_May_2013",
            "monteenth_of_August_2013",
            "monteenth_of_September_2013"
        ]
        with open(os.path.join(exercise_dir, "meetup_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()
        for case in named_cases:
            assert f'TEST_CASE("{case}")' in test_src, f"Anchor case '{case}' missing from test source"
            results.append(f"Verified anchor case '{case}' is present.")

        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", res.stdout)
        assert m is not None, "Could not parse Catch2 summary"
        num_assertions = int(m.group(1))
        num_tests = int(m.group(2))
        assert num_tests >= 90, f"Expected at least 90 test cases, got {num_tests}"
        results.append(f"Reference passed all {num_tests} test cases ({num_assertions} assertions).")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 4. Verify learner files remain identical
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
