#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    checker = os.path.join(repo_root, "tools/course_checks/r20-t002.py")
    work_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(work_dir, "results.txt")

    print(f"[*] Running {checker}...")
    proc = subprocess.run([sys.executable, checker], capture_output=True, text=True)

    with open(results_path, "w", encoding="utf-8") as f:
        f.write("=== R20-T002 Execution Log ===\n")
        f.write(f"Return code: {proc.returncode}\n")
        f.write("STDOUT:\n")
        f.write(proc.stdout)
        if proc.stderr:
            f.write("STDERR:\n")
            f.write(proc.stderr)

    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    if proc.returncode != 0:
        print(f"[!] Check failed with code {proc.returncode}", file=sys.stderr)
        sys.exit(proc.returncode)

    print(f"[✓] Results written to {results_path}")

if __name__ == "__main__":
    main()
