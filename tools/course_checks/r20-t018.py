#!/usr/bin/env python3
"""Validate exercise file paths declared by a .meta/config.json files map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath


def validate_config(config: dict, exercise_dir: Path) -> dict:
    root = exercise_dir.resolve()
    errors: list[dict[str, str]] = []
    roles: dict[str, list[dict[str, str]]] = {}

    files = config.get("files")
    if not isinstance(files, dict):
        return {
            "valid": False,
            "roles": roles,
            "errors": [{"role": "files", "path": "", "reason": "missing or invalid files object"}],
        }

    for required_role in ("solution", "test", "example"):
        if required_role not in files:
            errors.append(
                {"role": required_role, "path": "", "reason": "required file role is missing"}
            )

    for role, configured_paths in files.items():
        role_results: list[dict[str, str]] = []
        roles[role] = role_results
        if not isinstance(configured_paths, list) or not configured_paths:
            errors.append(
                {"role": role, "path": "", "reason": "file role must contain a non-empty list"}
            )
            continue

        for raw_path in configured_paths:
            if not isinstance(raw_path, str) or not raw_path:
                errors.append(
                    {"role": role, "path": str(raw_path), "reason": "path must be a non-empty string"}
                )
                continue

            relative = Path(raw_path)
            windows_relative = PureWindowsPath(raw_path)
            if (
                relative.is_absolute()
                or windows_relative.is_absolute()
                or ".." in relative.parts
                or ".." in windows_relative.parts
            ):
                errors.append(
                    {
                        "role": role,
                        "path": raw_path,
                        "reason": "parent traversal or absolute path is not allowed",
                    }
                )
                continue

            resolved = (root / relative).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(
                    {"role": role, "path": raw_path, "reason": "resolved path escapes the exercise directory"}
                )
                continue

            if not resolved.is_file():
                errors.append(
                    {"role": role, "path": raw_path, "reason": "configured file does not exist"}
                )
                continue

            role_results.append({"configured": raw_path, "resolved": str(resolved)})

    return {"valid": not errors, "roles": roles, "errors": errors}


def main() -> int:
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exercise-dir",
        type=Path,
        default=repository_root / "exercises/practice/binary-search",
        help="exercise directory whose configured files should be checked",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="configuration file (default: <exercise-dir>/.meta/config.json)",
    )
    args = parser.parse_args()
    exercise_dir = args.exercise_dir.resolve()
    config_path = args.config.resolve() if args.config else exercise_dir / ".meta/config.json"

    try:
        config = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {
                    "valid": False,
                    "roles": {},
                    "errors": [
                        {"role": "config", "path": str(config_path), "reason": str(error)}
                    ],
                }
            )
        )
        return 2

    result = validate_config(config, exercise_dir)
    result["exercise_dir"] = str(exercise_dir)
    result["config_path"] = str(config_path)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
