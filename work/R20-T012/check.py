#!/usr/bin/env python3
"""Run the reusable grade-school course check from the repository root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/course_checks/r20-t012.py"


def main() -> int:
    result = subprocess.run([sys.executable, str(CHECKER)], cwd=ROOT, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
