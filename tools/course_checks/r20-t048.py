#!/usr/bin/env python3
"""Validate exercise .meta/config.json file declarations and CMake naming rules (R20-T048)."""

import argparse
import json
from pathlib import Path, PurePosixPath
import sys

EXIT_OK = 0
EXIT_INVALID_CONFIG = 2
EXIT_PATH_TRAVERSAL = 3
EXIT_MISSING_TEST = 4
EXIT_MISSING_EXAMPLE = 5
EXIT_MISSING_SOLUTION = 6
EXIT_CMAKE_MISMATCH = 7


def validate_exercise(exercise_dir):
    ex_path = Path(exercise_dir)
    if not ex_path.is_dir():
        return EXIT_INVALID_CONFIG, f"INVALID_CONFIG: exercise directory not found: {exercise_dir}", []

    ex_resolved = ex_path.resolve()
    config_path = ex_resolved / ".meta" / "config.json"
    if not config_path.is_file():
        return EXIT_INVALID_CONFIG, f"INVALID_CONFIG: missing .meta/config.json at {config_path}", []

    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return EXIT_INVALID_CONFIG, f"INVALID_CONFIG: malformed JSON in .meta/config.json: {exc}", []

    files_obj = config_data.get("files")
    if not isinstance(files_obj, dict):
        return EXIT_INVALID_CONFIG, "INVALID_CONFIG: missing 'files' object in .meta/config.json", []

    required_roles = ("solution", "test", "example")
    for role in required_roles:
        entries = files_obj.get(role)
        if not isinstance(entries, list) or len(entries) == 0:
            return EXIT_INVALID_CONFIG, f"INVALID_CONFIG: role '{role}' must be a non-empty list", []

    roles_to_check = ["solution", "test", "example"]
    if "editor" in files_obj:
        if not isinstance(files_obj["editor"], list):
            return EXIT_INVALID_CONFIG, "INVALID_CONFIG: role 'editor' must be a list when present", []
        roles_to_check.append("editor")

    rows = []
    first_error = None

    for role in roles_to_check:
        for rel_str in files_obj.get(role, []):
            if not isinstance(rel_str, str) or not rel_str.strip():
                return EXIT_INVALID_CONFIG, f"INVALID_CONFIG: empty or non-string path in role '{role}'", rows

            posix_rel = PurePosixPath(rel_str)
            if Path(rel_str).is_absolute() or posix_rel.is_absolute():
                return EXIT_PATH_TRAVERSAL, f"PATH_TRAVERSAL: absolute path rejected in '{role}': {rel_str}", rows
            if ".." in posix_rel.parts:
                return EXIT_PATH_TRAVERSAL, f"PATH_TRAVERSAL: parent traversal '..' rejected in '{role}': {rel_str}", rows

            candidate_unres = ex_resolved / rel_str
            candidate_res = candidate_unres.resolve()
            try:
                candidate_res.relative_to(ex_resolved)
            except ValueError:
                return EXIT_PATH_TRAVERSAL, f"PATH_TRAVERSAL: resolved path escapes exercise dir in '{role}': {rel_str}", rows

            exists = candidate_res.is_file()
            rows.append({"role": role, "path": rel_str, "exists": exists})
            if not exists and first_error is None:
                if role == "test":
                    first_error = (EXIT_MISSING_TEST, f"MISSING_TEST: declared test file not found: {rel_str}")
                elif role == "example":
                    first_error = (EXIT_MISSING_EXAMPLE, f"MISSING_EXAMPLE: declared reference file not found: {rel_str}")
                else:
                    first_error = (EXIT_MISSING_SOLUTION, f"MISSING_SOLUTION: declared {role} file not found: {rel_str}")

    if first_error is not None:
        return first_error[0], first_error[1], rows

    # Cross-check CMake naming rule (<file> = slug with '-' -> '_')
    cmake_path = ex_resolved / "CMakeLists.txt"
    if not cmake_path.is_file():
        return EXIT_CMAKE_MISMATCH, "CMAKE_MISMATCH: missing CMakeLists.txt", rows
    cmake_text = cmake_path.read_text(encoding="utf-8")
    if 'string(REPLACE "-" "_" file ${exercise})' not in cmake_text or "${file}_test.cpp" not in cmake_text:
        return EXIT_CMAKE_MISMATCH, "CMAKE_MISMATCH: CMakeLists.txt does not follow standard <file>_test.cpp naming rule", rows

    slug = ex_resolved.name
    file_stem = slug.replace("-", "_")
    expected_test = f"{file_stem}_test.cpp"
    expected_header = f"{file_stem}.h"
    expected_cpp = f"{file_stem}.cpp"

    if expected_test not in files_obj["test"]:
        return EXIT_CMAKE_MISMATCH, f"CMAKE_MISMATCH: expected test '{expected_test}' in config.json test list", rows
    if expected_header not in files_obj["solution"]:
        return EXIT_CMAKE_MISMATCH, f"CMAKE_MISMATCH: expected header '{expected_header}' in config.json solution list", rows
    if (ex_resolved / expected_cpp).is_file() and expected_cpp not in files_obj["solution"]:
        return EXIT_CMAKE_MISMATCH, f"CMAKE_MISMATCH: expected source '{expected_cpp}' in config.json solution list", rows
    if not any(Path(p).suffix in (".cpp", ".h", ".hpp") for p in files_obj["example"]):
        return EXIT_CMAKE_MISMATCH, "CMAKE_MISMATCH: no C++ reference extension found in example list", rows

    return EXIT_OK, f"OK: {slug} config.json and CMake rules validated ({len(rows)} files)", rows


def main():
    parser = argparse.ArgumentParser(description="Validate Exercism C++ exercise .meta/config.json paths and CMake naming.")
    parser.add_argument("exercise_dir", help="Path to exercise directory (e.g. exercises/practice/diamond)")
    args = parser.parse_args()

    rc, message, rows = validate_exercise(args.exercise_dir)

    print("role      | path                  | exists")
    print("----------+-----------------------+-------")
    for row in rows:
        print(f"{row['role']:<9} | {row['path']:<21} | {row['exists']}")
    if not any(r["role"] == "editor" for r in rows):
        print("editor    | (not declared)        | n/a")

    print(message)
    return rc


if __name__ == "__main__":
    sys.exit(main())
