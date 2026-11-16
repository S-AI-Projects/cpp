#!/usr/bin/env python3
"""Build and verify prime-factors against its reference in a disposable copy."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


EXERCISE_REL = Path("exercises/practice/prime-factors")
SELECTED = [
    {
        "uuid": "924fc966-a8f5-4288-82f2-6b9224819ccd",
        "name": "no factors",
        "input": 1,
        "expected": [],
    },
    {
        "uuid": "17e30670-b105-4305-af53-ddde182cb6ad",
        "name": "prime number",
        "input": 2,
        "expected": [2],
    },
    {
        "uuid": "238d57c8-4c12-42ef-af34-ae4929f94789",
        "name": "another prime number",
        "input": 3,
        "expected": [3],
    },
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(command: list[str], *, cwd: Path, timeout: int = 300) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    result = {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    require(
        completed.returncode == 0,
        f"Command failed ({completed.returncode}): {' '.join(command)}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
    )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def junit_summary(junit_root: ET.Element, expected_count: int) -> dict:
    test_cases = list(junit_root.iter("testcase"))
    failures = [
        item
        for test_case in test_cases
        for item in list(test_case)
        if item.tag in {"failure", "error"}
    ]
    require(test_cases, "The test executable reported zero test cases")
    require(
        len(test_cases) == expected_count,
        f"Expected {expected_count} executed cases, found {len(test_cases)}",
    )
    require(not failures, f"JUnit report contains {len(failures)} failure/error entries")
    return {
        "executed": len(test_cases),
        "failures": len(failures),
        "names": [item.attrib.get("name", "") for item in test_cases],
    }


def expect_failure(action, expected_message: str) -> None:
    try:
        action()
    except RuntimeError as exc:
        require(expected_message in str(exc), f"Unexpected failure reason: {exc}")
        return
    raise RuntimeError(f"Expected checker to reject: {expected_message}")


def verify_failure_contract(root: Path) -> dict:
    expect_failure(
        lambda: run(
            [sys.executable, "-c", "raise SystemExit(9)"], cwd=root
        ),
        "Command failed (9)",
    )
    zero_tests = ET.fromstring("<testsuites><testsuite tests='0'/></testsuites>")
    expect_failure(lambda: junit_summary(zero_tests, 12), "zero test cases")
    failed_assertion = ET.fromstring(
        "<testsuites><testsuite tests='1'><testcase name='mutant'>"
        "<failure message='expected assertion failure'/></testcase></testsuite></testsuites>"
    )
    expect_failure(lambda: junit_summary(failed_assertion, 1), "failure/error entries")
    return {
        "nonzero_child_exit": "rejected",
        "zero_test_run": "rejected",
        "assertion_failure": "rejected",
    }


def repo_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / EXERCISE_REL / ".meta/config.json").is_file():
            return candidate

    # The original local harness lived beside the repository at work/cpp.
    candidate = Path(__file__).resolve().parents[1] / "cpp"
    require(
        (candidate / EXERCISE_REL / ".meta/config.json").is_file(),
        f"Could not find repository exercise at {candidate / EXERCISE_REL}",
    )
    return candidate


def verify_selected_source(test_source: str, metadata: dict) -> None:
    require(len(metadata) == 12, f"Expected 12 canonical cases, found {len(metadata)}")
    for case in SELECTED:
        require(case["uuid"] in metadata, f"{case['name']} UUID missing from tests.toml")
        block_match = re.search(
            rf'TEST_CASE\("{re.escape(case["name"])}",.*?(?=TEST_CASE\(|#endif)',
            test_source,
            flags=re.DOTALL,
        )
        require(block_match is not None, f"Could not locate test block: {case['name']}")
        block = block_match.group(0)
        require(case["uuid"] in block, f"UUID mismatch in test block: {case['name']}")
        require(
            re.search(rf"prime_factors::of\({case['input']}\)", block) is not None,
            f"Unexpected input in test block: {case['name']}",
        )
        expected_values = r",\s*".join(map(str, case["expected"]))
        expected_pattern = (
            r"expected\s*\{\s*\};"
            if not case["expected"]
            else rf"expected\s*\{{\s*{expected_values}\s*\}};"
        )
        require(
            re.search(expected_pattern, block) is not None,
            f"Unexpected expected vector in test block: {case['name']}",
        )


def main() -> int:
    root = repo_root()
    source_exercise = root / EXERCISE_REL
    config = json.loads((source_exercise / ".meta/config.json").read_text())
    test_source_path = source_exercise / config["files"]["test"][0]
    test_source = test_source_path.read_text()
    metadata_text = (source_exercise / ".meta/tests.toml").read_text()
    test_ids = re.findall(r"^\[([0-9a-f-]+)\]$", metadata_text, flags=re.MULTILINE)
    tests_toml = dict.fromkeys(test_ids)
    verify_selected_source(test_source, tests_toml)

    solution_paths = config["files"]["solution"]
    example_paths = config["files"]["example"]
    require(
        len(solution_paths) == len(example_paths),
        "Reference solution and example file lists do not map one-to-one",
    )
    learner_files = [source_exercise / relative for relative in solution_paths]
    before_hashes = {str(path.relative_to(root)): sha256(path) for path in learner_files}
    require(all(path.is_file() for path in learner_files), "A learner solution file is missing")

    result = {
        "task": "R20-T020",
        "exercise": str(EXERCISE_REL),
        "tool_versions": {
            "python": sys.version.split()[0],
            "cmake": run(["cmake", "--version"], cwd=root)["stdout"].splitlines()[0],
            "compiler": run(
                [os.environ.get("CXX", "c++"), "--version"], cwd=root
            )["stdout"].splitlines()[0],
        },
        "selected_cases": SELECTED,
        "expected_case_count": len(tests_toml),
        "checker_failure_paths": verify_failure_contract(root),
        "children": [],
    }

    temp_parent: Path
    with tempfile.TemporaryDirectory(prefix="r20-t020-") as temp_name:
        temp_parent = Path(temp_name)
        copied_exercise = temp_parent / source_exercise.name
        shutil.copytree(source_exercise, copied_exercise)
        for solution_relative, example_relative in zip(solution_paths, example_paths):
            destination = copied_exercise / solution_relative
            reference = copied_exercise / example_relative
            require(reference.is_file(), f"Missing configured reference file: {example_relative}")
            shutil.copy2(reference, destination)

        result["children"].append(
            run(
                [
                    "cmake",
                    "-S",
                    ".",
                    "-B",
                    "build",
                    "-DEXERCISM_RUN_ALL_TESTS=ON",
                ],
                cwd=copied_exercise,
            )
        )
        result["children"].append(
            run(["cmake", "--build", "build", "--parallel"], cwd=copied_exercise)
        )

        test_executable = copied_exercise / "build" / "prime-factors"
        require(test_executable.is_file(), f"Built test executable not found: {test_executable}")
        junit_file = temp_parent / "prime-factors-junit.xml"
        result["children"].append(
            run(
                [
                    str(test_executable),
                    "--reporter",
                    "junit",
                    "--out",
                    str(junit_file),
                ],
                cwd=copied_exercise,
            )
        )
        junit = junit_summary(ET.parse(junit_file).getroot(), len(tests_toml))
        executed_names = junit["names"]
        for case in SELECTED:
            require(
                any(case["name"] in name for name in executed_names),
                f"Selected case was not executed: {case['name']}",
            )
        result["junit"] = junit

        probe_source = temp_parent / "selected_cases_probe.cpp"
        probe_source.write_text(
            '#include <iostream>\n'
            '#include "prime_factors.h"\n'
            'int main() {\n'
            '    for (long long input : {1LL, 2LL, 3LL}) {\n'
            '        const auto factors = prime_factors::of(input);\n'
            '        std::cout << "[";\n'
            '        for (std::size_t index = 0; index < factors.size(); ++index) {\n'
            '            if (index != 0) std::cout << ",";\n'
            '            std::cout << factors[index];\n'
            '        }\n'
            '        std::cout << "]\\n";\n'
            '    }\n'
            '}\n'
        )
        compiler = os.environ.get("CXX", "c++")
        probe_executable = temp_parent / "selected_cases_probe"
        result["children"].append(
            run(
                [
                    compiler,
                    "-std=c++17",
                    "-Wall",
                    "-Wextra",
                    "-Wpedantic",
                    "-Werror",
                    "-I",
                    str(copied_exercise),
                    str(copied_exercise / "prime_factors.cpp"),
                    str(probe_source),
                    "-o",
                    str(probe_executable),
                ],
                cwd=copied_exercise,
            )
        )
        probe = run([str(probe_executable)], cwd=copied_exercise)
        result["children"].append(probe)
        actual_lines = probe["stdout"].splitlines()
        expected_lines = ["[]", "[2]", "[3]"]
        require(
            actual_lines == expected_lines,
            f"Selected-case probe mismatch: expected {expected_lines}, got {actual_lines}",
        )
        result["selected_case_probe"] = {
            "expected_lines": expected_lines,
            "actual_lines": actual_lines,
        }

    after_hashes = {str(path.relative_to(root)): sha256(path) for path in learner_files}
    require(before_hashes == after_hashes, "Learner solution files changed during the check")
    result["learner_hashes"] = {"before": before_hashes, "after": after_hashes}
    result["temporary_copy_removed"] = not temp_parent.exists()
    require(result["temporary_copy_removed"], "Temporary exercise copy was not removed")

    evidence_dir = Path(__file__).resolve().parent
    (evidence_dir / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (evidence_dir / "cases.json").write_text(
        json.dumps(
            {
                "selected_cases": SELECTED,
                "expected_outputs": ["[]", "[2]", "[3]"],
                "actual_outputs": result["selected_case_probe"]["actual_lines"],
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"PASS: {result['junit']['executed']} reference test cases; "
        f"selected outputs {result['selected_case_probe']['actual_lines']}; "
        "learner files unchanged; temporary copy removed"
    )
    print(f"Evidence: {evidence_dir / 'results.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # Keep failures visible to shell/CI callers.
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
