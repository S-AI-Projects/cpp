#!/usr/bin/env python3
"""
Path and configuration checker for raindrops (R20-T028).
Validates that all declared files in .meta/config.json:
- Resolve strictly inside the exercise directory without parent traversal.
- Exist on disk.
- Categorizes files by role (solution, test, example).
"""

import json
import os
import sys

def validate_exercise_config(exercise_dir, config_override=None):
    exercise_dir = os.path.abspath(exercise_dir)
    config_path = os.path.join(exercise_dir, ".meta", "config.json")

    if config_override is not None:
        if isinstance(config_override, dict):
            config = config_override
        else:
            with open(config_override, "r", encoding="utf-8") as f:
                config = json.load(f)
    else:
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

    if "files" not in config or not isinstance(config["files"], dict):
        raise ValueError("Missing or invalid 'files' object in config.json")

    roles = ["solution", "test", "example"]
    for role in roles:
        if role not in config["files"]:
            raise ValueError(f"Required file role '{role}' missing from config.json")

    verified_files = {}
    for role, file_list in config["files"].items():
        if not isinstance(file_list, list):
            raise ValueError(f"Role '{role}' must map to a list of file paths")
        verified_files[role] = []
        for rel_path in file_list:
            # Reject parent directory traversal
            normalized = os.path.normpath(rel_path)
            if normalized.startswith("..") or os.path.isabs(rel_path):
                raise PermissionError(f"Path traversal detected in role '{role}': '{rel_path}' escapes exercise root")

            abs_path = os.path.abspath(os.path.join(exercise_dir, rel_path))
            # Ensure strictly within exercise_dir
            if not abs_path.startswith(exercise_dir + os.sep) and abs_path != exercise_dir:
                raise PermissionError(f"File '{rel_path}' resolves outside exercise root: {abs_path}")

            if not os.path.isfile(abs_path):
                raise FileNotFoundError(f"Declared file for role '{role}' does not exist: {rel_path}")

            verified_files[role].append(abs_path)

    return verified_files

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    exercise_dir = os.path.join(repo_root, "exercises", "practice", "raindrops")
    if len(sys.argv) > 1:
        exercise_dir = sys.argv[1]

    try:
        results = validate_exercise_config(exercise_dir)
        print(f"Validation SUCCESS for exercise at {exercise_dir}:")
        for role, paths in results.items():
            print(f"  [{role}]: {len(paths)} file(s)")
            for p in paths:
                print(f"    - {os.path.relpath(p, exercise_dir)}")
        sys.exit(0)
    except Exception as e:
        print(f"Validation FAILED: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
