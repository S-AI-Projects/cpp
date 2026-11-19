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

def run_isolated(exercise_dir, mode="real"):
    temp_dir = tempfile.mkdtemp(prefix=f"hs_{mode}_")
    try:
        temp_ex = os.path.join(temp_dir, "high-scores")
        shutil.copytree(exercise_dir, temp_ex, ignore=shutil.ignore_patterns("build"))

        ref_cpp = os.path.join(temp_ex, ".meta/example.cpp")
        ref_h = os.path.join(temp_ex, ".meta/example.h")

        if mode == "real":
            shutil.copy2(ref_cpp, os.path.join(temp_ex, "high_scores.cpp"))
            shutil.copy2(ref_h, os.path.join(temp_ex, "high_scores.h"))
        elif mode == "failing":
            # Deliberately failing reference
            with open(ref_cpp, "r", encoding="utf-8") as f:
                code = f.read()
            # Mutate latest_score to return wrong value
            code = code.replace("return scores.back();", "return -999;")
            with open(os.path.join(temp_ex, "high_scores.cpp"), "w", encoding="utf-8") as f:
                f.write(code)
            shutil.copy2(ref_h, os.path.join(temp_ex, "high_scores.h"))

        bld = os.path.join(temp_ex, "build")
        subprocess.run(["cmake", "-S", temp_ex, "-B", bld, "-DEXERCISM_RUN_ALL_TESTS=ON"], check=True, capture_output=True)
        # Build executable target
        subprocess.run(["cmake", "--build", bld, "--target", "high-scores"], check=True, capture_output=True)

        exe = os.path.join(bld, "high-scores")
        if mode == "zero_test":
            shutil.copy2(ref_cpp, os.path.join(temp_ex, "high_scores.cpp"))
            shutil.copy2(ref_h, os.path.join(temp_ex, "high_scores.h"))
            # Run with non-matching tag filter
            res = subprocess.run([exe, "[nonexistent_filter_tag]"], capture_output=True, text=True)
        else:
            res = subprocess.run([exe], capture_output=True, text=True)

        return res
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/high-scores")
    learner_files = [
        os.path.join(exercise_dir, "high_scores.cpp"),
        os.path.join(exercise_dir, "high_scores.h")
    ]

    logs = []
    logs.append("=== R20-T009 High Scores Isolated Runner Check ===")

    # 1. Record initial learner hashes
    initial_hashes = hash_files(learner_files)
    for p, h in initial_hashes.items():
        logs.append(f"Initial hash: {os.path.basename(p)} = {h[:12]}...")

    # Verify learner stub is unsolved in working tree
    with open(os.path.join(exercise_dir, "high_scores.cpp"), "r", encoding="utf-8") as f:
        stub_text = f.read()
    assert "scores.back()" not in stub_text, "Learner stub in working tree was solved!"
    logs.append("Verified learner stub in working tree is unsolved.")

    try:
        # 2. Test Real Reference
        logs.append("\n--- Mode 1: Real Reference Run ---")
        real_res = run_isolated(exercise_dir, mode="real")
        assert real_res.returncode == 0, f"Real reference failed with exit code {real_res.returncode}"

        # Verify anchor test cases
        named_cases = ["List of scores", "Latest score", "Personal best"]
        with open(os.path.join(exercise_dir, "high_scores_test.cpp"), "r", encoding="utf-8") as f:
            test_src = f.read()
        for case in named_cases:
            assert case in test_src, f"Anchor case '{case}' missing from test source"
            logs.append(f"Anchor case verified: '{case}'")

        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", real_res.stdout)
        assert m is not None, "Could not parse Catch2 summary for real reference"
        num_tests = int(m.group(2))
        assert num_tests > 0, "Zero tests executed!"
        logs.append(f"Real reference passed all {num_tests} test cases successfully.")

        # 3. Test Deliberately Failing Reference
        logs.append("\n--- Mode 2: Deliberately Failing Reference Run ---")
        fail_res = run_isolated(exercise_dir, mode="failing")
        assert fail_res.returncode != 0, "Failing reference unexpectedly passed!"
        assert "FAILED" in fail_res.stdout, "Catch2 did not report test failure"
        logs.append("Failing reference correctly produced non-zero exit code and failure assertion.")

        # 4. Test Zero Test Selection
        logs.append("\n--- Mode 3: Zero-Test Selection Run ---")
        zero_res = run_isolated(exercise_dir, mode="zero_test")
        is_zero = "No tests ran" in zero_res.stdout or "0 test cases" in zero_res.stdout
        assert is_zero, f"Expected zero tests executed with nonexistent filter, got:\n{zero_res.stdout}"
        logs.append("Zero-test selection correctly detected 'No tests ran' and verified zero-run handling.")

    finally:
        # 5. Verify learner files remained completely unchanged
        final_hashes = hash_files(learner_files)
        assert initial_hashes == final_hashes, "Learner files changed during run!"
        logs.append("\nVerified: learner file hashes identical before and after all runs.")

    return logs

if __name__ == "__main__":
    try:
        results = main()
        print("\n".join(results))
        print("\n[✓] R20-T009 check passed.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] R20-T009 check failed: {e}", file=sys.stderr)
        sys.exit(1)
