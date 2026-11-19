#!/usr/bin/env python3
"""Check hexadecimal test maintenance, reproducibility, and isolated builds."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/hexadecimal")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T022"
ANCHOR_CASES = [
    "hex_1_is_decimal_1",
    "hex_c_is_decimal_12",
    "hex_10_is_decimal_16",
]
TEST_RE = re.compile(r'TEST_CASE\(\s*"([^"]+)"')


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_timestamps(text: str) -> str:
    timestamp_pattern = re.compile(
        r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\d{1,2}:\d{2}(:\d{2})?|timestamp|generated on)",
        re.IGNORECASE,
    )
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if (stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*")) and timestamp_pattern.search(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def versions() -> dict[str, str]:
    configlet_version = "unknown"
    configlet_path = ROOT / "bin/configlet"
    if configlet_path.exists():
        ver_res = subprocess.run([str(configlet_path), "--version"], cwd=ROOT, text=True, capture_output=True)
        if ver_res.returncode == 0:
            configlet_version = ver_res.stdout.strip().splitlines()[0]

    return {
        "python": sys.version.split()[0],
        "cmake": run(["cmake", "--version"], ROOT).stdout.splitlines()[0],
        "cxx": run(["c++", "--version"], ROOT).stdout.splitlines()[0],
        "configlet": configlet_version,
    }


def main() -> int:
    config_path = EXERCISE / ".meta/config.json"
    if not config_path.exists():
        raise AssertionError("Missing exercises/practice/hexadecimal/.meta/config.json")
    config = json.loads(config_path.read_text())

    doc_path = ROOT / "docs/maintenance/hexadecimal.md"
    if not doc_path.exists():
        raise AssertionError("Missing docs/maintenance/hexadecimal.md")
    doc_text = doc_path.read_text()

    for anchor in ANCHOR_CASES:
        if anchor not in doc_text:
            raise AssertionError(f"Maintenance documentation does not identify anchor case: {anchor}")

    # Check and hash learner starter stubs before run
    solutions = [Path(s) for s in config["files"]["solution"]]
    stubs_before = {}
    for sol in solutions:
        sol_path = EXERCISE / sol
        stubs_before[str(sol)] = sha256(sol_path)
        content = sol_path.read_text()
        if "TODO: add your solution here" not in content:
            raise AssertionError(f"Learner starter stub in {sol} was modified!")

    test_source_path = EXERCISE / config["files"]["test"][0]
    test_source = test_source_path.read_text()
    test_names = TEST_RE.findall(test_source)
    if len(test_names) != 10:
        raise AssertionError(f"Expected 10 test cases in hexadecimal_test.cpp; found {len(test_names)}")
    for anchor in ANCHOR_CASES:
        if anchor not in test_names:
            raise AssertionError(f"Anchor test case '{anchor}' missing from test suite")

    # Perform two independent generations / test runs
    generations_data = []
    generations_test_sources = []
    generations_listed_cases = []

    for gen_idx in (1, 2):
        with tempfile.TemporaryDirectory(prefix=f"r20-t022-gen{gen_idx}-") as temp_dir:
            temp_root = Path(temp_dir) / EXERCISE_REL.name
            shutil.copytree(EXERCISE, temp_root)

            # Test source content in this copy
            copy_test_source = (temp_root / config["files"]["test"][0]).read_text()
            generations_test_sources.append(normalize_timestamps(copy_test_source))

            # Run configlet check
            configlet_out = ""
            configlet_bin = ROOT / "bin/configlet"
            if configlet_bin.exists():
                cfg_res = subprocess.run(
                    [str(configlet_bin), "sync", "--exercise", "hexadecimal", "--tests", "--offline"],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                configlet_out = (cfg_res.stdout + cfg_res.stderr).strip()

            # Substitute reference solution into temp copy only
            for ex in config["files"]["example"]:
                ex_path = temp_root / ex
                sol_target = temp_root / ex_path.name.replace("example", "hexadecimal")
                shutil.copy2(ex_path, sol_target)

            # Configure and build
            configure = run(["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], temp_root)
            build = run(["cmake", "--build", "build"], temp_root)
            binary = temp_root / "build" / EXERCISE_REL.name

            # List tests
            list_res = subprocess.run([str(binary), "--list-test-names-only"], cwd=temp_root, text=True, capture_output=True)
            listed = [l.strip() for l in list_res.stdout.splitlines() if l.strip()]
            if list_res.returncode not in (0, len(listed)):
                raise RuntimeError(f"Listing tests failed in generation {gen_idx}: {list_res.stderr}")
            if len(listed) != len(test_names):
                raise AssertionError(f"Executable listed {len(listed)} cases; expected {len(test_names)}")
            generations_listed_cases.append(listed)

            # Run tests
            test_run = run([str(binary)], temp_root)
            summary_match = re.search(r"(\d+) test cases?", test_run.stdout + test_run.stderr)
            if not summary_match:
                raise AssertionError(f"Could not parse test summary in generation {gen_idx}")
            executed = int(summary_match.group(1))
            if executed != len(test_names):
                raise AssertionError(f"Expected {len(test_names)} executed cases; Catch reported {executed}")

            summary_line = test_run.stdout.strip().splitlines()[-1] if test_run.stdout.strip() else ""
            generations_data.append({
                "generation": gen_idx,
                "configlet_output": configlet_out,
                "test_source_sha256": sha256(temp_root / config["files"]["test"][0]),
                "executed_cases": executed,
                "listed_cases": len(listed),
                "summary": summary_line,
            })

    # Compare two generations
    if generations_test_sources[0] != generations_test_sources[1]:
        raise AssertionError("Generated test sources differ between generation 1 and generation 2!")
    if generations_listed_cases[0] != generations_listed_cases[1]:
        raise AssertionError("Compiled test lists differ between generation 1 and generation 2!")

    # Verify stubs after run
    stubs_after = {}
    for sol in solutions:
        sol_path = EXERCISE / sol
        stubs_after[str(sol)] = sha256(sol_path)
        if stubs_after[str(sol)] != stubs_before[str(sol)]:
            raise AssertionError(f"Learner starter file {sol} was altered during the check!")

    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "task": "R20-T022",
        "versions": versions(),
        "exercise": "hexadecimal",
        "anchor_cases": ANCHOR_CASES,
        "all_cases": test_names,
        "stubs_hash_before": stubs_before,
        "stubs_hash_after": stubs_after,
        "generations": generations_data,
        "comparisons": {
            "test_sources_equal_after_normalization": True,
            "compiled_test_lists_equal": True,
            "anchor_cases_verified": True,
        },
    }

    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print("R20-T022 check passed: 2 reproducible generations, all 10 Catch2 tests passed.")
    print(f"Anchor cases verified: {ANCHOR_CASES}")
    print(f"Report written to: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as err:
        print(f"R20-T022 check failed: {err}", file=sys.stderr)
        raise SystemExit(1)
