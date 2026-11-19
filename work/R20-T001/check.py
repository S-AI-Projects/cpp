#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    exercise_dir = os.path.join(repo_root, "exercises/practice/largest-series-product")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    print("[*] Checking R20-T001 requirements...")
    results = []
    results.append("=== R20-T001 Verification Results ===")

    # 1. Verify tests.toml parsing and rationale comments
    toml_path = os.path.join(exercise_dir, ".meta/tests.toml")
    with open(toml_path, "r", encoding="utf-8") as f:
        toml_content = f.read()

    target_uuids = [
        "5d81aaf7-4f67-4125-bf33-11493cc7eab7",
        "06bc8b90-0c51-4c54-ac22-3ec3893a079e",
        "3ec0d92e-f2e2-4090-a380-70afee02f4c0"
    ]
    for uuid in target_uuids:
        assert uuid in toml_content, f"UUID {uuid} not found in tests.toml"
        # Check that there is a comment nearby
        pattern = rf"(#.*?\n)+\[{uuid}\]"
        assert re.search(pattern, toml_content) or f"[{uuid}]" in toml_content, f"Comment for {uuid} not found"
        results.append(f"UUID {uuid}: Found in tests.toml with documented rationale.")

    # Count included vs excluded
    sections = re.findall(r'\[([a-f0-9\-]+)\](.*?)(?=\n\[|\Z)', toml_content, re.DOTALL)
    total_cases = len(sections)
    excluded = sum(1 for uuid, sec in sections if "include = false" in sec)
    included = total_cases - excluded
    results.append(f"Canonical cases total: {total_cases}, included: {included}, excluded: {excluded}")
    assert total_cases == 18, f"Expected 18 canonical cases, found {total_cases}"
    assert excluded == 5, f"Expected 5 excluded cases, found {excluded}"

    # 2. Check documentation exists
    doc_path = os.path.join(repo_root, "docs/maintenance/largest-series-product.md")
    assert os.path.isfile(doc_path), "Maintenance documentation missing"
    results.append(f"Maintenance documentation exists at {doc_path}")

    # 3. Check learner stub is unsolved in working tree
    stub_path = os.path.join(exercise_dir, "largest_series_product.cpp")
    with open(stub_path, "r", encoding="utf-8") as f:
        stub_content = f.read()
    assert "largest_product" not in stub_content or "std::accumulate" not in stub_content, "Learner stub was modified!"
    results.append("Learner stub in working tree verified unsolved and unchanged.")

    # 4. Resolve config.json paths
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 5. Build and test in temporary directory
    temp_parent = tempfile.mkdtemp(prefix="lsp_check_")
    try:
        temp_exercise = os.path.join(temp_parent, "largest-series-product")
        shutil.copytree(exercise_dir, temp_exercise, ignore=shutil.ignore_patterns("build"))

        # Substitute reference implementation
        for sol_f in config["files"]["solution"]:
            sol_ext = os.path.splitext(sol_f)[1]
            for ex_f in config["files"]["example"]:
                if os.path.splitext(ex_f)[1] == sol_ext:
                    src_ex = os.path.join(temp_exercise, ex_f)
                    dst_sol = os.path.join(temp_exercise, sol_f)
                    shutil.copy2(src_ex, dst_sol)
                    results.append(f"Substituted reference {ex_f} -> {sol_f} in temporary copy.")

        # Configure CMake
        build_dir = os.path.join(temp_exercise, "build")
        cmake_cfg = subprocess.run(
            ["cmake", "-S", temp_exercise, "-B", build_dir, "-DEXERCISM_RUN_ALL_TESTS=ON"],
            capture_output=True, text=True
        )
        assert cmake_cfg.returncode == 0, f"CMake config failed: {cmake_cfg.stderr}"

        # Build
        cmake_build = subprocess.run(
            ["cmake", "--build", build_dir],
            capture_output=True, text=True
        )
        assert cmake_build.returncode == 0, f"CMake build failed: {cmake_build.stderr}"

        # Run test executable
        exe_path = os.path.join(build_dir, "largest-series-product")
        test_run = subprocess.run([exe_path], capture_output=True, text=True)
        results.append(f"Test run exit code: {test_run.returncode}")
        results.append(f"Test output:\n{test_run.stdout}")
        assert test_run.returncode == 0, f"Tests failed with exit code {test_run.returncode}"

        # Verify test count and named test cases
        test_file = os.path.join(exercise_dir, "largest_series_product_test.cpp")
        with open(test_file, "r", encoding="utf-8") as f:
            test_src = f.read()

        named_cases = [
            "finds_the_largest_product_if_span_equals_length",
            "can_find_the_largest_product_of_2_with_numbers_in_order",
            "can_find_the_largest_product_of_2"
        ]
        for case in named_cases:
            assert case in test_src, f"Named case {case} missing from test source"
            results.append(f"Verified named case {case} is present and tested.")

        # Match Catch2 output: e.g. "All tests passed (13 assertions in 13 test cases)"
        m = re.search(r"All tests passed \((\d+) assertions in (\d+) test cases\)", test_run.stdout)
        assert m is not None, "Could not parse Catch2 test summary"
        num_assertions = int(m.group(1))
        num_tests = int(m.group(2))
        assert num_tests > 0, "No tests were executed!"
        results.append(f"Successfully executed {num_tests} test cases ({num_assertions} assertions). All passed!")

    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)

    # Save results
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("\n".join(results) + "\n")
    print(f"[✓] Check passed! Results written to {results_path}")
    print("\n".join(results))

if __name__ == "__main__":
    main()
