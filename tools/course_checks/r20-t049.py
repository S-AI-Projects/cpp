#!/usr/bin/env python3
"""Isolated test runner protecting learner files for Exercism C++ exercises (R20-T049)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
_ACTIVE_PROC = None


def build_env():
    env = os.environ.copy()
    extra = ["/opt/homebrew/bin", "/usr/local/bin"]
    current = env.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    for p in reversed(extra):
        if p not in parts:
            parts.insert(0, p)
    env["PATH"] = os.pathsep.join(parts)
    return env


ENV = build_env()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def snapshot_directory_hashes(root_dir):
    return {p.relative_to(root_dir).as_posix(): sha256_file(p) for p in sorted(root_dir.rglob("*")) if p.is_file()}


def run_managed(cmd, cwd, timeout=900):
    """Run subprocess via Popen so signal handlers can terminate child cleanly before temp cleanup."""
    global _ACTIVE_PROC
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    _ACTIVE_PROC = proc
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise
    finally:
        _ACTIVE_PROC = None
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def find_executable(copy_dir, slug):
    for c in (
        copy_dir / "build" / slug,
        copy_dir / "build" / "Debug" / slug,
        copy_dir / "build" / f"{slug}.exe",
        copy_dir / "build" / "Debug" / f"{slug}.exe",
    ):
        if c.is_file():
            return c
    return None


def resolve_base_ref():
    res = subprocess.run(["git", "rev-parse", "--verify", "org/main"], cwd=str(REPO), env=ENV, capture_output=True, text=True)
    if res.returncode == 0:
        return "org/main", res.stdout.strip()
    mb = subprocess.run(["git", "merge-base", "HEAD", "main"], cwd=str(REPO), env=ENV, capture_output=True, text=True)
    if mb.returncode == 0:
        return mb.stdout.strip(), mb.stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO), env=ENV, capture_output=True, text=True)
    return head.stdout.strip(), head.stdout.strip()


def evaluate_results(build_rc, run_rc, xml_content, list_count, expected_cases=None):
    failures = []
    if build_rc != 0:
        failures.append(f"build_rc={build_rc} (expected 0)")
    if run_rc != 0:
        failures.append(f"run_rc={run_rc} (expected 0)")
    if not xml_content or not xml_content.strip():
        failures.append("XML output missing or empty")
        return failures, 0

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        failures.append(f"XML parse error: {exc}")
        return failures, 0

    overall_cases = root.findall(".//OverallResultsCases")
    if not overall_cases:
        failures.append("Missing OverallResultsCases in XML")
        return failures, 0

    top = overall_cases[-1]
    successes = int(top.attrib.get("successes", "0"))
    fail_count = int(top.attrib.get("failures", "0"))
    total = successes + fail_count

    if total == 0:
        failures.append("ZERO-TEST GUARD: OverallResultsCases successes+failures == 0")
    if expected_cases is not None and total != expected_cases:
        failures.append(f"Total executed cases {total} != expected {expected_cases}")
    if fail_count > 0:
        failures.append(f"OverallResultsCases failures={fail_count}")
    if list_count != total:
        failures.append(f"--list-test-names-only count {list_count} != XML case count {total}")
    return failures, total


def substitute_reference(copy_dir, files_cfg, ref_dir_override):
    sol_by_ext = {(copy_dir / r).suffix: (copy_dir / r) for r in files_cfg["solution"]}
    if ref_dir_override:
        ref_root = Path(ref_dir_override).resolve()
        if not ref_root.is_dir():
            raise RuntimeError(f"Reference directory does not exist: {ref_root}")
        # Support either example.* or <file>.* inside reference-dir
        for ext, dst in sol_by_ext.items():
            cand_example = ref_root / f"example{ext}"
            cand_named = ref_root / dst.name
            src = cand_example if cand_example.is_file() else cand_named
            if not src.is_file():
                raise RuntimeError(f"Missing reference file for {ext} in {ref_root}")
            shutil.copy2(src, dst)
        return

    ex_by_ext = {(copy_dir / r).suffix: (copy_dir / r) for r in files_cfg["example"]}
    for ext, src in ex_by_ext.items():
        if ext in sol_by_ext:
            shutil.copy2(src, sol_by_ext[ext])


def main():
    parser = argparse.ArgumentParser(description="Isolated Exercism C++ runner protecting learner files.")
    parser.add_argument("--exercise", default="bank-account", help="Exercise slug (default: bank-account)")
    parser.add_argument("--reference-dir", default="", help="Optional directory overriding .meta/example.*")
    parser.add_argument("--filter", default="", help="Optional Catch2 test filter expression")
    parser.add_argument("--xml-out", default="", help="Optional output path for Catch2 XML results")
    parser.add_argument("--list-out", default="", help="Optional output path for --list-test-names-only")
    args = parser.parse_args()

    slug = args.exercise
    ex_dir = (REPO / "exercises" / "practice" / slug).resolve()
    if not ex_dir.is_dir():
        print(f"FAIL: Exercise directory not found: {ex_dir}", file=sys.stderr)
        return 2

    # Signal handler ensures SIGINT/SIGTERM triggers normal finally cleanup
    def handle_signal(signum, _frame):
        global _ACTIVE_PROC
        if _ACTIVE_PROC is not None and _ACTIVE_PROC.poll() is None:
            _ACTIVE_PROC.terminate()
            try:
                _ACTIVE_PROC.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _ACTIVE_PROC.kill()
                _ACTIVE_PROC.wait()
        raise KeyboardInterrupt(f"Interrupted by signal {signum}")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    pre_hashes = snapshot_directory_hashes(ex_dir)
    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t049-"))
    print(f"TEMP_DIR: {tmp_dir}", flush=True)

    failures = []
    executed_cases = 0

    try:
        # Step A: Config validation
        cfg_path = ex_dir / ".meta" / "config.json"
        cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))
        files_cfg = cfg_data.get("files", {})
        for role in ("solution", "test", "example"):
            entries = files_cfg.get(role, [])
            if not entries:
                raise RuntimeError(f"Missing role '{role}' in .meta/config.json")
            for rel in entries:
                p = (ex_dir / rel).resolve()
                p.relative_to(ex_dir)
                if not p.is_file():
                    raise RuntimeError(f"Declared file missing: {p}")

        # Step C: Stub unsolved vs org/main
        base_ref, _ = resolve_base_ref()
        protected_rel = [f"exercises/practice/{slug}/{r}" for r in files_cfg["solution"] + files_cfg["test"]]
        diff_res = run_managed(["git", "diff", "--quiet", base_ref, "--"] + protected_rel, cwd=REPO)
        if diff_res.returncode != 0:
            failures.append(f"Learner/test files differ from {base_ref}")
        else:
            print(f"PASS: Learner stub and test files equal {base_ref}", flush=True)

        # Step D: Isolated copy
        copy_dir = tmp_dir / slug
        shutil.copytree(ex_dir, copy_dir)
        if not ((copy_dir / ".meta").is_dir() and (copy_dir / ".docs").is_dir() and (copy_dir / "test" / "catch.hpp").is_file()):
            raise RuntimeError("Isolated copy missing .meta, .docs, or test/catch.hpp")
        substitute_reference(copy_dir, files_cfg, args.reference_dir)

        # Static TEST_CASE count in test file
        test_file = copy_dir / files_cfg["test"][0]
        static_count = len(re.findall(r'TEST_CASE\s*\(', test_file.read_text(encoding="utf-8")))

        # Step E: Configure and compile
        cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        cfg_res = run_managed(cfg_cmd, cwd=copy_dir)
        if cfg_res.returncode != 0:
            cfg_cmd.append("-DCMAKE_POLICY_VERSION_MINIMUM=3.5")
            cfg_res = run_managed(cfg_cmd, cwd=copy_dir)
        if cfg_res.returncode != 0:
            failures.append(f"CMake configure failed (rc={cfg_res.returncode}): {cfg_res.stderr}")
            raise RuntimeError("CMake configure failed")

        compile_res = run_managed(["cmake", "--build", "build", "--target", slug], cwd=copy_dir)
        if compile_res.returncode != 0:
            failures.append(f"CMake compile target '{slug}' failed (rc={compile_res.returncode}): {compile_res.stderr}")
            raise RuntimeError("Compile failed")

        build_all_rc = 0
        if not args.filter:
            bld_all_res = run_managed(["cmake", "--build", "build"], cwd=copy_dir)
            build_all_rc = bld_all_res.returncode

        exe_path = find_executable(copy_dir, slug)
        if exe_path is None:
            raise RuntimeError(f"Generated executable for {slug} not found")

        xml_file = tmp_dir / "results.xml"
        run_cmd_args = [str(exe_path)]
        if args.filter:
            run_cmd_args.append(args.filter)
        run_cmd_args.extend(["-r", "xml", "-o", str(xml_file)])
        run_res = run_managed(run_cmd_args, cwd=copy_dir)
        xml_text = xml_file.read_text(encoding="utf-8") if xml_file.is_file() else ""

        list_cmd_args = [str(exe_path)]
        if args.filter:
            list_cmd_args.append(args.filter)
        list_cmd_args.append("--list-test-names-only")
        list_res = run_managed(list_cmd_args, cwd=copy_dir)
        listed_names = [line.strip() for line in list_res.stdout.splitlines() if line.strip()]

        if args.xml_out and xml_text:
            Path(args.xml_out).write_text(xml_text, encoding="utf-8")
        if args.list_out:
            Path(args.list_out).write_text(list_res.stdout, encoding="utf-8")

        eval_failures, executed_cases = evaluate_results(
            build_rc=build_all_rc,
            run_rc=run_res.returncode,
            xml_content=xml_text,
            list_count=len(listed_names),
            expected_cases=None if args.filter else static_count,
        )
        failures.extend(eval_failures)

    except KeyboardInterrupt as exc:
        failures.append(str(exc))
    except Exception as exc:
        failures.append(f"{type(exc).__name__}: {exc}")
    finally:
        if _ACTIVE_PROC is not None and _ACTIVE_PROC.poll() is None:
            _ACTIVE_PROC.kill()
            _ACTIVE_PROC.wait()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if tmp_dir.exists():
            failures.append(f"Temp directory still exists after cleanup: {tmp_dir}")
        else:
            print(f"PASS: Temp directory cleaned up ({tmp_dir})", flush=True)

        post_hashes = snapshot_directory_hashes(ex_dir)
        if pre_hashes != post_hashes:
            failures.append("CRITICAL: Exercise files changed during run!")
        else:
            print(f"PASS: All {len(post_hashes)} exercise files unchanged (SHA-256 verified)", flush=True)

    if not failures:
        print(f"RESULT: PASS - executed {executed_cases} cases", flush=True)
        return 0
    print(f"RESULT: FAIL - executed {executed_cases} cases - " + "; ".join(failures), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
