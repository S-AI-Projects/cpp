#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "tools/course_checks/r20-t022.py"
sys.exit(subprocess.run([sys.executable, str(CHECKER)] + sys.argv[1:]).returncode)
