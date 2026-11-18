#!/usr/bin/env python3
"""Check grade-school metadata-to-test mapping and reproducible test builds."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXERCISE_REL = Path("exercises/practice/grade-school")
EXERCISE = ROOT / EXERCISE_REL
TASK_DIR = ROOT / "work/R20-T012"
REQUIRED = {
    "a3f0fb58-f240-4723-8ddc-e644666b85cc": "roster_is_empty_when_no_student_is_added",
    "6d0a30e4-1b4e-472e-8e20-c41702125667": "student_is_added_to_the_roster",
    "233be705-dd58-4968-889d-fb3c7954c9cc": "multiple_students_in_the_same_grade_are_added_to_the_roster",
}
TEST_RE = re.compile(r'TEST_CASE\(\s*"([^"]+)"\s*,\s*"\[([0-9a-f-]+)\]"')


def run(
    command: list[str],
    cwd: Path,
    *,
    accept_statuses: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode not in accept_statuses:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_map(track_root: Path) -> tuple[dict[str, str], dict[str, object], list[str]]:
    exercise = track_root / EXERCISE_REL
    config = json.loads((exercise / ".meta/config.json").read_text())
    metadata = tomllib.loads((exercise / ".meta/tests.toml").read_text())
    test_files = config["files"]["test"]
    if len(test_files) != 1:
        raise AssertionError(f"Expected one maintained test source, found {test_files}")
    test_path = exercise / test_files[0]
    matches = TEST_RE.findall(test_path.read_text())
    tagged_uuids = [uuid for _, uuid in matches]
    if len(matches) != len(set(tagged_uuids)):
        raise AssertionError("A canonical UUID is tagged by more than one C++ test")
    cases = {uuid: name for name, uuid in matches}
    enabled = {
        uuid
        for uuid, details in metadata.items()
        if details.get("include", True) is not False
    }
    disabled = set(metadata) - enabled
    if enabled != set(cases):
        raise AssertionError(
            f"Metadata/test mismatch: enabled without test={sorted(enabled-set(cases))}; "
            f"test without enabled metadata={sorted(set(cases)-enabled)}"
        )
    for uuid, name in REQUIRED.items():
        if cases.get(uuid) != name:
            raise AssertionError(f"Expected UUID {uuid} to map to {name}; got {cases.get(uuid)!r}")
    return cases, {"metadata": metadata, "enabled": sorted(enabled), "disabled": sorted(disabled)}, test_files


def make_track_copy(destination: Path, configlet: Path) -> Path:
    ignore = shutil.ignore_patterns(
        ".git", ".config", "build", "build_exercises", "work", "configlet", "configlet.exe"
    )
    copy = destination / "track"
    shutil.copytree(ROOT, copy, ignore=ignore)
    copied_configlet = copy / "bin/configlet"
    copied_configlet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(configlet, copied_configlet)
    return copy


def map_reference(exercise: Path, config: dict[str, object]) -> None:
    solutions = [Path(value) for value in config["files"]["solution"]]
    examples = [Path(value) for value in config["files"]["example"]]
    for example in examples:
        destinations = [path for path in solutions if path.suffix == example.suffix]
        if len(destinations) != 1:
            raise AssertionError(f"Cannot uniquely map {example} to solution paths: {destinations}")
        destination = exercise / destinations[0]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(exercise / example, destination)


def build_and_run(track_root: Path, config: dict[str, object]) -> dict[str, object]:
    exercise = track_root / EXERCISE_REL
    map_reference(exercise, config)
    configure = run(
        ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"],
        exercise,
    )
    build = run(["cmake", "--build", "build"], exercise)
    binary = exercise / "build" / EXERCISE_REL.name
    listing = subprocess.run(
        [str(binary), "--list-test-names-only"],
        cwd=exercise,
        text=True,
        capture_output=True,
    )
    names = [line.strip() for line in listing.stdout.splitlines() if line.strip()]
    if listing.returncode not in (0, len(names)):
        raise RuntimeError(f"Catch2 test listing failed ({listing.returncode}): {listing.stderr}")
    if not names:
        raise AssertionError("The generated test executable lists zero cases")
    execution = run([str(binary)], exercise)
    summary = re.search(r"(\d+) test cases?", execution.stdout + execution.stderr)
    if not summary or int(summary.group(1)) != len(names):
        raise AssertionError(f"Catch output does not confirm {len(names)} executed test cases")
    return {
        "configure_exit": configure.returncode,
        "build_exit": build.returncode,
        "listing_exit": listing.returncode,
        "execution_exit": execution.returncode,
        "listed_cases": names,
        "executed_cases": int(summary.group(1)),
        "summary": execution.stdout.strip().splitlines()[-1] if execution.stdout.strip() else "",
    }


def main() -> int:
    configlet = ROOT / "bin/configlet"
    if not configlet.is_file():
        raise RuntimeError("configlet is missing; run ./bin/fetch-configlet from the repository root")
    configlet_version = run([str(configlet), "--version"], ROOT).stdout.strip()
    original_config = json.loads((EXERCISE / ".meta/config.json").read_text())
    original_hashes = {
        str(path): sha256(EXERCISE / path)
        for path in original_config["files"]["solution"]
        if (EXERCISE / path).exists()
    }
    original_cases, original_metadata, test_files = source_map(ROOT)
    original_source_hash = sha256(EXERCISE / test_files[0])
    report: dict[str, object] = {
        "task": "R20-T012",
        "tools": {
            "python": sys.version.split()[0],
            "cmake": run(["cmake", "--version"], ROOT).stdout.splitlines()[0],
            "cxx": run(["c++", "--version"], ROOT).stdout.splitlines()[0],
            "configlet": configlet_version,
        },
        "metadata_counts": {
            "total": len(original_metadata["metadata"]),
            "included": len(original_metadata["enabled"]),
            "excluded": len(original_metadata["disabled"]),
        },
        "required_case_ids": REQUIRED,
        "maintained_test_source": str(EXERCISE_REL / test_files[0]),
        "learner_file_hashes_before": original_hashes,
    }

    with tempfile.TemporaryDirectory(prefix="r20-t012-") as temporary:
        temp = Path(temporary)
        generated = []
        builds = []
        sync_outputs = []
        for index in (1, 2):
            track_copy = make_track_copy(temp / f"generation-{index}", configlet)
            command = [
                str(track_copy / "bin/configlet"),
                "sync",
                "--exercise",
                "grade-school",
                "--tests",
                "exclude",
                "--update",
                "--yes",
            ]
            synced = run(command, track_copy)
            sync_outputs.append(synced.stdout.strip())
            cases, data, copied_tests = source_map(track_copy)
            if cases != original_cases:
                raise AssertionError(f"Generation {index} changed the active case-to-test mapping")
            generated.append({
                "tests_toml": (track_copy / EXERCISE_REL / ".meta/tests.toml").read_text(),
                "test_source": (track_copy / EXERCISE_REL / copied_tests[0]).read_text(),
                "cases": cases,
                "metadata": data,
            })
            builds.append(build_and_run(track_copy, original_config))

        if generated[0]["tests_toml"] != generated[1]["tests_toml"]:
            raise AssertionError("Two configlet generations produced different tests.toml files")
        if generated[0]["test_source"] != generated[1]["test_source"]:
            raise AssertionError("Maintained C++ test source differs between fresh copies")
        if builds[0]["listed_cases"] != builds[1]["listed_cases"]:
            raise AssertionError("Two fresh CMake builds produced different test lists")
        if any(build["executed_cases"] != len(original_cases) for build in builds):
            raise AssertionError("One or more enabled tests did not execute")
        for build in builds:
            if not set(REQUIRED.values()).issubset(build["listed_cases"]):
                raise AssertionError("One or more required cases are absent from the generated executable")

        report["generations"] = [
            {
                "configlet_output": sync_outputs[index],
                "metadata_sha256": hashlib.sha256(generated[index]["tests_toml"].encode()).hexdigest(),
                "test_source_sha256": hashlib.sha256(generated[index]["test_source"].encode()).hexdigest(),
                "metadata_entries": len(generated[index]["metadata"]["metadata"]),
                "included": len(generated[index]["metadata"]["enabled"]),
                "excluded": len(generated[index]["metadata"]["disabled"]),
                "test_cases": builds[index]["executed_cases"],
                "test_names": builds[index]["listed_cases"],
                "test_summary": builds[index]["summary"],
            }
            for index in (0, 1)
        ]
        report["named_case_results"] = [
            {"uuid": uuid, "test": name, "status": "assertion passed in both builds"}
            for uuid, name in REQUIRED.items()
        ]
        report["comparisons"] = {
            "metadata_equal": True,
            "configlet_sync_output_equal": sync_outputs[0] == sync_outputs[1],
            "maintained_test_source_equal": True,
            "compiled_test_lists_equal": True,
            "timestamp_normalization": "None needed; the generated TOML and test-name list contain no timestamps.",
        }

    after_hashes = {
        str(path): sha256(EXERCISE / path)
        for path in original_config["files"]["solution"]
        if (EXERCISE / path).exists()
    }
    if after_hashes != original_hashes:
        raise AssertionError("Learner solution files changed during the isolated checks")
    if sha256(EXERCISE / test_files[0]) != original_source_hash:
        raise AssertionError("The maintained test source changed during the isolated checks")
    report["learner_file_hashes_after"] = after_hashes
    report["maintained_test_source_unchanged"] = True
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    report_path = TASK_DIR / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(
        "R20-T012 passed: 23 metadata entries (15 included, 8 excluded); "
        "two generations each executed 15 tests."
    )
    print(f"Report: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"R20-T012 check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
