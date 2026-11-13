#!/usr/bin/env python3
"""Path and configuration checker for isbn-verifier exercise."""

import os
import json
import sys

EXERCISE_DIR = "exercises/practice/isbn-verifier"

def check_config(config_path, exercise_dir):
    """Validate the config.json file structure and paths."""
    errors = []
    
    with open(config_path) as f:
        config = json.load(f)
    
    if "files" not in config:
        errors.append("Missing 'files' key in config.json")
        return errors
    
    files = config["files"]
    
    for role, paths in files.items():
        if not isinstance(paths, list):
            errors.append(f"Files for '{role}' must be a list")
            continue
        
        for path in paths:
            # Check for parent traversal
            if ".." in path or path.startswith("/"):
                errors.append(f"Path '{path}' in '{role}' has parent traversal or absolute path")
                continue
            
            # Check file exists (relative to exercise directory)
            full_path = os.path.join(exercise_dir, path)
            if not os.path.exists(full_path):
                errors.append(f"File '{path}' in '{role}' does not exist at {full_path}")
            elif not os.path.isfile(full_path):
                errors.append(f"Path '{path}' in '{role}' is not a file")
    
    return errors

def main():
    exercise_dir = os.path.join(os.getcwd(), EXERCISE_DIR)
    config_path = os.path.join(exercise_dir, ".meta/config.json")
    
    if not os.path.exists(config_path):
        print(f"ERROR: config.json not found at {config_path}")
        sys.exit(1)
    
    errors = check_config(config_path, exercise_dir)
    
    if errors:
        print("Configuration errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("Configuration is valid!")
    print(f"  Exercise: {EXERCISE_DIR}")
    print(f"  Config: .meta/config.json")
    print(f"  All declared files exist and are valid")

if __name__ == "__main__":
    main()