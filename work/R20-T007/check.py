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
    exercise_dir = os.path.join(repo_root, "exercises/practice/nth-prime")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    results = []
    results.append("=== R20-T007 Nth Prime Guidance Check ===")

    # 1. Verify hints.md content
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    assert os.path.isfile(hints_path), "hints.md missing"
    with open(hints_path, "r", encoding="utf-8") as f:
        hints_text = f.read()

    assert "<stdexcept>" in hints_text, "Missing <stdexcept> header reference"
    assert "<cmath>" in hints_text or "std::sqrt" in hints_text, "Missing <cmath>/std::sqrt reference"
    assert "Executable Micro-Example" in hints_text, "Missing micro-example"
    assert "Expected Output" in hints_text, "Missing expected output"
    assert "cppreference.com" in hints_text, "Missing reference link"
    results.append("Verified C++-specific guidance in hints.md (headers, constraints, micro-example, doc links).")

    # 2. Extract and compile micro-example from hints.md
    m_code = re.search(r"```cpp\n(.*?)```", hints_text, re.DOTALL)
    assert m_code is not None, "Could not extract C++ micro-example"
    micro_code = m_code.group(1)

    temp_micro = tempfile.mkdtemp(prefix="micro_prime_")
    try:
        src_file = os.path.join(temp_micro, "micro.cpp")
        bin_file = os.path.join(temp_micro, "micro")
        with open(src_file, "w", encoding="utf-8") as f:
            f.write(micro_code)

        compile_proc = subprocess.run(["clang++", "-std=c++17", "-O2", src_file, "-o", bin_file], capture_output=True, text=True)
        assert compile_proc.returncode == 0, f"Micro-example failed to compile: {compile_proc.stderr}"

        run_proc = subprocess.run([bin_file], capture_output=True, text=True)
        assert run_proc.returncode == 0, f"Micro-example run failed: {run_proc.stderr}"
        assert "1st prime: 2" in run_proc.stdout
        assert "2nd prime: 3" in run_proc.stdout
        assert "6th prime: 13" in run_proc.stdout
        results.append("Executable micro-example compiled and verified with exact expected output.")
    finally:
        shutil.rmtree(temp_micro, ignore_errors=True)

    # 3. Record initial hashes of learner files
    learner_files = [
        os.path.join(exercise_dir, "nth_prime.cpp"),
        os.path.join(exercise_dir, "nth_prime.h")
    ]
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        results.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Check learner stub in working tree is unsolved
    with open(os.path.join(exercise_dir, "nth_prime.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "is_prime" not in stub_text, "Learner stub was modified!"
    results.append("Verified learner stub in working tree is unsolved.")

    # 4. Build and test reference implementation in temp directory
    temp_dir = tempfile.mkdtemp(prefix="np_check_")
    try:
        temp_ex = os.path.join(temp_dir, "nth-prime")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        shutil.copy2(os.path.join(temp_ex, ".meta/example.cpp"), os.path.join(temp_ex, "nth_prime.cpp"))
        shutil.copy2(os.path.join(temp_ex, ".meta/example.h"), os.path.join(temp_ex, "nth_prime.h"))

        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)

        res = subprocess.run([os.path.join(bld, "nth-prime")], capture_output=True, text=True)
        assert res.returncode == 0, f"Tests failed: {res.stderr}"

        # Verify named cases in test source
        named_cases = ["first", "second", "sixth"]
        with open(os.path.join(exercise_dir, "nth_prime_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()
        for case in named_cases:
            assert f'TEST_CASE("{case}")' in test_src, f"Named case '{case}' missing from tests"
            results.append(f"Verified anchor case '{case}' is present.")

        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", res.stdout)
        assert m is not None, "Could not parse Catch2 summary"
        num_assertions = int(m.group(1))
        num_tests = int(m.group(2))
        assert num_tests >= 5, f"Expected at least 5 test cases, got {num_tests}"
        results.append(f"Reference implementation passed all {num_tests} tests ({num_assertions} assertions).")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 5. Verify learner files remain identical
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
