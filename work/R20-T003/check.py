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
    exercise_dir = os.path.join(repo_root, "exercises/practice/hello-world")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    results = []
    results.append("=== R20-T003 Hello World Mutation Check ===")

    # 1. Check documentation and hints
    hints_path = os.path.join(exercise_dir, ".docs/hints.md")
    assert os.path.isfile(hints_path), "hints.md missing"
    results.append(f"Found hints at {hints_path}")

    doc_path = os.path.join(repo_root, "docs/maintenance/hello-world.md")
    assert os.path.isfile(doc_path), "maintenance documentation missing"
    results.append(f"Found maintenance doc at {doc_path}")

    # 2. Record initial hashes of learner files
    learner_files = [
        os.path.join(exercise_dir, "hello_world.cpp"),
        os.path.join(exercise_dir, "hello_world.h")
    ]
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        results.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Check that learner stub is unsolved
    with open(os.path.join(exercise_dir, "hello_world.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "Goodbye, Mars!" in stub_text, "Learner stub was modified or already solved!"
    results.append("Verified learner stub in working tree is unsolved ('Goodbye, Mars!').")

    # 3. Test reference implementation in scratch dir
    temp_dir_ref = tempfile.mkdtemp(prefix="hw_ref_")
    try:
        temp_ex = os.path.join(temp_dir_ref, "hello-world")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        # Substitute reference
        shutil.copy2(os.path.join(temp_ex, ".meta/example.cpp"), os.path.join(temp_ex, "hello_world.cpp"))
        shutil.copy2(os.path.join(temp_ex, ".meta/example.h"), os.path.join(temp_ex, "hello_world.h"))

        # Build & test
        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)
        res_ref = subprocess.run([os.path.join(bld, "hello-world")], capture_output=True, text=True)

        assert res_ref.returncode == 0, f"Reference test failed: {res_ref.stderr}"
        assert "All tests passed" in res_ref.stdout, "Reference did not pass Catch2 tests"
        results.append("Reference implementation passed all tests (Say Hi! passed).")
    finally:
        shutil.rmtree(temp_dir_ref, ignore_errors=True)

    # 4. Test mutant implementation in scratch dir
    mutant_code = """#include "hello_world.h"

using namespace std;

namespace hello_world {

string hello() { return "Hello World!"; } // mutant missing comma

}  // namespace hello_world
"""
    temp_dir_mut = tempfile.mkdtemp(prefix="hw_mut_")
    try:
        temp_ex_mut = os.path.join(temp_dir_mut, "hello-world")
        shutil.copytree(exercise_dir, temp_ex_mut, ignore=shutil.ignore_patterns("build"))

        # Substitute mutant
        with open(os.path.join(temp_ex_mut, "hello_world.cpp"), "w", encoding="utf-8") as f:
            f.write(mutant_code)
        shutil.copy2(os.path.join(temp_ex_mut, ".meta/example.h"), os.path.join(temp_ex_mut, "hello_world.h"))

        # Build mutant executable only (avoiding test_hello-world custom target which runs it during build)
        bld_mut = os.path.join(temp_ex_mut, "build")
        subprocess.run(["cmake", "-S", temp_ex_mut, "-B", bld_mut, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        bld_proc = subprocess.run(["cmake", "--build", bld_mut, "--target", "hello-world"], capture_output=True, text=True)
        assert bld_proc.returncode == 0, f"Mutant failed to compile: {bld_proc.stderr}"
        results.append("Mutant compiled successfully against header.")

        # Run mutant test
        res_mut = subprocess.run([os.path.join(bld_mut, "hello-world")], capture_output=True, text=True)
        assert res_mut.returncode != 0, "Mutant unexpectedly passed the test suite!"
        assert "FAILED" in res_mut.stdout, "Catch2 did not report failure for mutant"
        results.append("Mutant correctly failed test_hello (Say Hi!).")
        results.append(f"Mutant failure output snippet:\n{res_mut.stdout.strip()}")
    finally:
        shutil.rmtree(temp_dir_mut, ignore_errors=True)

    # 5. Verify learner file hashes after run
    final_hashes = hash_files(learner_files)
    assert initial_hashes == final_hashes, "Learner files were altered during test run!"
    results.append("Verified: learner file hashes are identical before and after.")

    # Write results
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")

    print("\n".join(results))
    print(f"[✓] Check passed! Evidence written to {results_path}")

if __name__ == "__main__":
    main()
