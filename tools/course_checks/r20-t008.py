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

def check_protein_translation():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/protein-translation")
    logs = []
    logs.append("=== R20-T008 Protein Translation Configuration & Test Check ===")

    # 1. Verify docs/maintenance/protein-translation.md
    doc_path = os.path.join(repo_root, "docs/maintenance/protein-translation.md")
    assert os.path.isfile(doc_path), f"Maintenance doc missing: {doc_path}"
    logs.append(f"Found maintenance documentation at {doc_path}")

    # 2. Check config.json path validity
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    for section in ["solution", "test", "example"]:
        assert section in cfg["files"], f"Missing section '{section}' in config.json files"
        for rel_path in cfg["files"][section]:
            full_p = os.path.join(exercise_dir, rel_path)
            assert os.path.isfile(full_p), f"Configured file '{rel_path}' does not exist on disk!"
            logs.append(f"Config path verified: [{section}] {rel_path}")

    # 3. Check learner files hash and unsolved status
    learner_files = [
        os.path.join(exercise_dir, "protein_translation.cpp"),
        os.path.join(exercise_dir, "protein_translation.h")
    ]
    initial_hashes = hash_files(learner_files)
    with open(os.path.join(exercise_dir, "protein_translation.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "Methionine" not in stub_text, "Learner stub was modified!"
    logs.append("Verified learner stubs in working tree are unsolved.")

    # 4. Isolated scratch build and test execution
    temp_dir = tempfile.mkdtemp(prefix="pt_check_")
    try:
        temp_ex = os.path.join(temp_dir, "protein-translation")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        shutil.copy2(os.path.join(temp_ex, ".meta/example.cpp"), os.path.join(temp_ex, "protein_translation.cpp"))
        shutil.copy2(os.path.join(temp_ex, ".meta/example.h"), os.path.join(temp_ex, "protein_translation.h"))

        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        subprocess.run(["cmake", "--build", bld], check=True, capture_output=True)

        res = subprocess.run([os.path.join(bld, "protein-translation")], capture_output=True, text=True)
        assert res.returncode == 0, f"Tests failed: {res.stderr}"

        # Verify anchor test cases
        named_cases = [
            "Methionine RNA sequence",
            "Phenylalanine RNA sequence 1",
            "Phenylalanine RNA sequence 2"
        ]
        with open(os.path.join(exercise_dir, "protein_translation_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()
        for case in named_cases:
            assert case in test_src, f"Anchor case '{case}' missing from test source"
            logs.append(f"Anchor case verified: '{case}'")

        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", res.stdout)
        assert m is not None, "Could not parse Catch2 test summary"
        num_assertions = int(m.group(1))
        num_tests = int(m.group(2))
        assert num_tests >= 25, f"Expected at least 25 test cases, got {num_tests}"
        logs.append(f"All {num_tests} test cases passed ({num_assertions} assertions).")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # 5. Verify learner files remained identical
    final_hashes = hash_files(learner_files)
    assert initial_hashes == final_hashes, "Learner files changed during run!"
    logs.append("Verified: learner file hashes identical before and after run.")

    return logs

if __name__ == "__main__":
    try:
        results = check_protein_translation()
        print("\n".join(results))
        print("[✓] R20-T008 check passed.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] R20-T008 check failed: {e}", file=sys.stderr)
        sys.exit(1)
