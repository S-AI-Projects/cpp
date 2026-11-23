#!/usr/bin/env python3
"""Reusable reproducibility check for CMake exercise preparation (R20-T042)."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


REPO = Path(__file__).resolve().parents[2]
UUID_TAG_RE = re.compile(r"\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\]", re.I)


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


def parse_toml_fallback(text):
    """Parse configlet tests.toml subset in Python 3.9+ without external deps."""
    data = {}
    current_section = None
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].strip()
            if not sec:
                raise ValueError(f"Empty TOML section header at line {lineno}")
            current_section = sec
            data[current_section] = {}
            continue
        if current_section is None:
            raise ValueError(f"Key-value outside section at line {lineno}: {raw_line}")
        if "=" not in line:
            raise ValueError(f"Invalid TOML line {lineno}: {raw_line}")
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if val == "true":
            parsed_val = True
        elif val == "false":
            parsed_val = False
        elif val.startswith('"') and val.endswith('"') and len(val) >= 2:
            parsed_val = bytes(val[1:-1], "utf-8").decode("unicode_escape")
        elif val.startswith("'") and val.endswith("'") and len(val) >= 2:
            parsed_val = val[1:-1]
        else:
            raise ValueError(f"Unsupported TOML value at line {lineno}: {val}")
        data[current_section][key] = parsed_val
    return data


def parse_tests_toml(text):
    fallback = parse_toml_fallback(text)
    if tomllib is not None:
        stdlib_parsed = tomllib.loads(text)
        if stdlib_parsed != fallback:
            raise ValueError("tomllib and fallback parser disagreed on tests.toml")
        return stdlib_parsed
    return fallback


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def identity_normalise(text):
    """Track test files contain no generated timestamps; normalisation is the identity."""
    return text


def run_cmd(cmd, cwd, timeout=900):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=ENV,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def resolve_git_ref(requested_ref):
    res = run_cmd(["git", "rev-parse", "--verify", requested_ref], cwd=REPO)
    if res.returncode == 0:
        return requested_ref, res.stdout.strip()
    if requested_ref == "org/main":
        head = run_cmd(["git", "rev-parse", "--verify", "HEAD"], cwd=REPO)
        if head.returncode == 0:
            print("INFO: org/main not found; falling back to HEAD")
            return "HEAD", head.stdout.strip()
    raise RuntimeError(f"Could not resolve git ref {requested_ref!r}: {res.stderr.strip()}")


def extract_archive(ref, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive_proc = subprocess.Popen(
        ["git", "archive", ref],
        cwd=str(REPO),
        env=ENV,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tar_proc = subprocess.run(
        ["tar", "-x", "-C", str(dest_dir)],
        stdin=archive_proc.stdout,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if archive_proc.stdout is not None:
        archive_proc.stdout.close()
    arch_err = archive_proc.stderr.read().decode("utf-8", errors="replace") if archive_proc.stderr else ""
    arch_rc = archive_proc.wait()
    if arch_rc != 0 or tar_proc.returncode != 0:
        raise RuntimeError(f"git archive/tar failed: arch_rc={arch_rc} ({arch_err}), tar_rc={tar_proc.returncode} ({tar_proc.stderr})")


def find_built_executable(copy_root, slug):
    candidates = [
        copy_root / "b" / "build_exercises" / "practice" / slug / slug,
        copy_root / "b" / "build_exercises" / "practice" / slug / "Debug" / slug,
        copy_root / "b" / "build_exercises" / "practice" / slug / f"{slug}.exe",
        copy_root / "b" / "build_exercises" / "practice" / slug / "Debug" / f"{slug}.exe",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def prepare_and_build_copy(ref, slug, label, tmp_parent):
    copy_dir = tmp_parent / label
    extract_archive(ref, copy_dir)

    cfg_cmd = ["cmake", "-S", ".", "-B", "b"]
    cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)
    boost_pruned = False
    policy_used = False

    if cfg_res.returncode != 0 and "Could NOT find Boost" in cfg_res.stderr and slug not in ("gigasecond", "meetup"):
        # Mirror .github/workflows/ci.yml (Windows job lines 72-73) when host lacks Boost
        boost_pruned = True
        for boost_slug in ("gigasecond", "meetup"):
            boost_ex = copy_dir / "exercises" / "practice" / boost_slug
            if boost_ex.exists():
                shutil.rmtree(boost_ex)
        for stale in ("build_exercises", "b"):
            stale_p = copy_dir / stale
            if stale_p.exists():
                shutil.rmtree(stale_p)
        cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)

    if cfg_res.returncode != 0 and "cmake_minimum_required" in cfg_res.stderr:
        policy_used = True
        for stale in ("build_exercises", "b"):
            stale_p = copy_dir / stale
            if stale_p.exists():
                shutil.rmtree(stale_p)
        cfg_cmd = ["cmake", "-S", ".", "-B", "b", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"]
        cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)

    if cfg_res.returncode != 0:
        raise RuntimeError(f"{label}: root cmake configure failed (rc={cfg_res.returncode}):\n{cfg_res.stderr}")

    bld_cmd = ["cmake", "--build", "b", "--target", slug]
    bld_res = run_cmd(bld_cmd, cwd=copy_dir)
    if bld_res.returncode != 0:
        raise RuntimeError(f"{label}: cmake --build b --target {slug} failed:\n{bld_res.stderr}\n{bld_res.stdout}")

    exe_path = find_built_executable(copy_dir, slug)
    if exe_path is None:
        raise RuntimeError(f"{label}: built executable for {slug} not found under b/build_exercises/practice/{slug}")

    list_res = run_cmd([str(exe_path), "--list-test-names-only"], cwd=copy_dir)
    test_names = [line.strip() for line in list_res.stdout.splitlines() if line.strip()]
    # Catch2 v2 exits with the number of listed test cases (capped at 255) or 0 on --list-test-names-only
    if list_res.returncode not in (0, min(255, len(test_names))) or not test_names:
        raise RuntimeError(f"{label}: --list-test-names-only failed (rc={list_res.returncode}, count={len(test_names)}): {list_res.stderr}")

    prep_dir = copy_dir / "build_exercises" / "practice" / slug
    config_json = json.loads((prep_dir / ".meta" / "config.json").read_text(encoding="utf-8"))
    files_cfg = config_json.get("files", {})
    tracked_rel_paths = []
    for role in ("test", "solution"):
        for rel in files_cfg.get(role, []):
            tracked_rel_paths.append(rel)

    file_hashes = {}
    file_texts = {}
    for rel in tracked_rel_paths:
        p = (prep_dir / rel).resolve()
        p.relative_to(prep_dir.resolve())
        if not p.is_file():
            raise RuntimeError(f"{label}: prepared file missing: {p}")
        file_hashes[rel] = sha256_file(p)
        file_texts[rel] = identity_normalise(p.read_text(encoding="utf-8"))

    return {
        "copy_dir": copy_dir,
        "prep_dir": prep_dir,
        "boost_pruned": boost_pruned,
        "policy_used": policy_used,
        "file_hashes": file_hashes,
        "file_texts": file_texts,
        "test_names": test_names,
        "list_raw": list_res.stdout,
        "config_files": files_cfg,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify reproducible track preparation for an Exercism C++ exercise.")
    parser.add_argument("--exercise", default="pig-latin", help="Practice exercise slug (default: pig-latin)")
    parser.add_argument("--ref", default="org/main", help="Git ref to archive cleanly (default: org/main)")
    parser.add_argument("--json-out", default="", help="Optional path to write structured JSON report")
    args = parser.parse_args()

    slug = args.exercise
    ref_name, ref_sha = resolve_git_ref(args.ref)
    tmp_root = Path(tempfile.mkdtemp(prefix="r20-t042-repro-"))
    failures = []
    report = {}

    try:
        res_a = prepare_and_build_copy(ref_name, slug, "copy-a", tmp_root)
        res_b = prepare_and_build_copy(ref_name, slug, "copy-b", tmp_root)

        print(f"Prepared exercise: {slug} (ref={ref_name} {ref_sha[:12]})")
        print("Timestamp normalisation: identity (no timestamps embedded in track test sources or build_fixup)")
        if res_a["boost_pruned"] or res_b["boost_pruned"]:
            print("Note: Boost not installed locally; applied ci.yml workaround (removed gigasecond/meetup in temp copies)")

        # 1. Byte-for-byte SHA-256 comparison across both copies
        hashes_equal = res_a["file_hashes"] == res_b["file_hashes"]
        texts_equal = res_a["file_texts"] == res_b["file_texts"]
        if not hashes_equal or not texts_equal:
            failures.append(f"Prepared file disagreement between copy-a and copy-b: {res_a['file_hashes']} vs {res_b['file_hashes']}")
        for rel, h in sorted(res_a["file_hashes"].items()):
            print(f"PASS SHA-256 ({rel}): {h} == {res_b['file_hashes'].get(rel)}")

        # 2. Compare --list-test-names-only output across both copies
        lists_equal = res_a["list_raw"] == res_b["list_raw"] and len(res_a["test_names"]) > 0
        if not lists_equal:
            failures.append("--list-test-names-only output disagreed or was empty between copy-a and copy-b")
        else:
            print(f"PASS --list-test-names-only identical across both builds: {len(res_a['test_names'])} test cases")

        # 3. Compare tests.toml included UUIDs against UUID tags in the prepared test file
        ex_src = REPO / "exercises" / "practice" / slug
        toml_data = parse_tests_toml((ex_src / ".meta" / "tests.toml").read_text(encoding="utf-8"))
        included_uuids = {u for u, kv in toml_data.items() if kv.get("include", True) is True}
        test_rel = res_a["config_files"]["test"][0]
        test_text = res_a["file_texts"][test_rel]
        test_uuids_list = UUID_TAG_RE.findall(test_text)
        test_uuids_set = {u.lower() for u in test_uuids_list}
        included_set = {u.lower() for u in included_uuids}

        uuids_exact_bijection = (
            len(test_uuids_list) == len(included_set)
            and test_uuids_set == included_set
            and len(res_a["test_names"]) == len(included_set)
        )
        if not uuids_exact_bijection:
            missing = sorted(included_set - test_uuids_set)
            extra = sorted(test_uuids_set - included_set)
            failures.append(
                f"UUID mismatch: included={len(included_set)}, test_tags={len(test_uuids_list)}, "
                f"built_cases={len(res_a['test_names'])}, missing={missing}, extra={extra}"
            )
        else:
            print(f"PASS UUID bijection: {len(included_set)} included tests.toml UUIDs == {len(test_uuids_list)} test tags == {len(res_a['test_names'])} compiled Catch2 cases")

        # 4. Also confirm prepared test file matches working tree copy
        wt_test_hash = sha256_file(ex_src / test_rel)
        if wt_test_hash != res_a["file_hashes"][test_rel]:
            failures.append(f"Prepared {test_rel} SHA-256 ({res_a['file_hashes'][test_rel]}) != working tree ({wt_test_hash})")
        else:
            print(f"PASS working-tree {test_rel} equals prepared copy byte-for-byte ({wt_test_hash})")

        report = {
            "exercise": slug,
            "ref": ref_name,
            "ref_sha": ref_sha,
            "normalisation": "identity (no timestamps emitted)",
            "boost_pruned_in_temp_copy": bool(res_a["boost_pruned"] or res_b["boost_pruned"]),
            "copy_a_hashes": res_a["file_hashes"],
            "copy_b_hashes": res_b["file_hashes"],
            "working_tree_test_sha256": wt_test_hash,
            "hashes_identical": hashes_equal,
            "test_case_count": len(res_a["test_names"]),
            "test_names": res_a["test_names"],
            "included_toml_uuids_count": len(included_set),
            "test_file_uuid_tags_count": len(test_uuids_list),
            "uuid_bijection_exact": uuids_exact_bijection,
            "passed": len(failures) == 0,
            "failures": failures,
        }
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
        if tmp_root.exists():
            failures.append(f"Failed to clean up temp directory: {tmp_root}")

    if failures:
        print("FAIL:", "; ".join(failures), file=sys.stderr)
        return 1
    print(f"REPRODUCIBILITY CHECK PASS: {slug} ({report['test_case_count']} cases, identical across 2 clean archives)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
