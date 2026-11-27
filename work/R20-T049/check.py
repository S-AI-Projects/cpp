#!/usr/bin/env python3
"""R20-T049 verification suite exercising tools/course_checks/r20-t049.py across all 4 scenarios."""

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


TASK_ID = "R20-T049"
SLUG = "bank-account"
EXPECTED_CASES = 17
NAMED_CASES = [
    "Newly opened account has zero balance",
    "Single deposit",
    "Multiple deposits",
]
ALLOWED_PREFIXES = (
    "tools/course_checks/r20-t049.py",
    "docs/maintenance/bank-account.md",
    "work/R20-T049/",
    "work/R20-T049",
)

REPO = Path(__file__).resolve().parents[2]
EX = REPO / "exercises" / "practice" / SLUG
WORK_DIR = REPO / "work" / TASK_ID
TOOL_PATH = REPO / "tools" / "course_checks" / "r20-t049.py"


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
    data = {}
    current_section = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            data[current_section] = {}
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if val == "true":
            parsed = True
        elif val == "false":
            parsed = False
        elif val.startswith('"') and val.endswith('"'):
            parsed = bytes(val[1:-1], "utf-8").decode("unicode_escape")
        else:
            parsed = val.strip("'")
        data[current_section][key] = parsed
    return data


def parse_tests_toml(text):
    fallback = parse_toml_fallback(text)
    if tomllib is not None:
        stdlib_parsed = tomllib.loads(text)
        if stdlib_parsed != fallback:
            raise ValueError("tomllib and fallback parser disagreed")
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


def snapshot_directory_hashes(root_dir):
    return {p.relative_to(root_dir).as_posix(): sha256_file(p) for p in sorted(root_dir.rglob("*")) if p.is_file()}


def normalise_text(text, tmp_dir=None):
    out = text
    if tmp_dir is not None:
        for candidate in (str(tmp_dir.resolve()), str(tmp_dir)):
            if candidate:
                out = out.replace(candidate, "<TMP>")
    out = re.sub(r"/[^\s\"']*r20-t049-[A-Za-z0-9_]+", "<RUNNER_TMP>", out)
    for candidate in (str(REPO.resolve()), str(REPO)):
        if candidate:
            out = out.replace(candidate, "<REPO>")
    home = str(Path.home())
    if home:
        out = out.replace(home, "<HOME>")
    out = re.sub(r"((?:Configuring|Generating) done \\()\\d+\\.\\d+s(\\))", r"\\1<TIME>\\2", out)
    return out


def normalise_xml(xml_text, tmp_dir=None):
    out = xml_text
    if tmp_dir is not None:
        for candidate in (str(tmp_dir.resolve()), str(tmp_dir)):
            if candidate:
                out = out.replace(candidate, "&lt;TMP&gt;")
    out = re.sub(r"/[^\s\"'<>]*r20-t049-[A-Za-z0-9_]+", "&lt;RUNNER_TMP&gt;", out)
    for candidate in (str(REPO.resolve()), str(REPO)):
        if candidate:
            out = out.replace(candidate, "&lt;REPO&gt;")
    home = str(Path.home())
    if home:
        out = out.replace(home, "&lt;HOME&gt;")
    return out


def clean_eof_and_trailing_ws(text):
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n") if lines else "\n"


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


def write_log(filename, cmd, result, tmp_dir):
    header = f"$ {' '.join(cmd)}\nexit_code: {result.returncode}\n"
    body = ""
    if result.stdout:
        body += f"--- stdout ---\n{result.stdout.rstrip()}\n"
    if result.stderr:
        body += f"--- stderr ---\n{result.stderr.rstrip()}\n"
    content = clean_eof_and_trailing_ws(normalise_text(header + body, tmp_dir=tmp_dir))
    (WORK_DIR / filename).write_text(content, encoding="utf-8")


def git_status_snapshot():
    res = run_cmd(["git", "status", "--porcelain", "-uall"], cwd=REPO)
    if res.returncode != 0:
        raise RuntimeError(f"git status failed: {res.stderr}")
    lines = [line for line in res.stdout.splitlines() if line.strip()]
    outside_work = []
    disallowed = []
    for line in lines:
        path_part = line[3:].strip()
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1].strip()
        if path_part.startswith('"') and path_part.endswith('"'):
            path_part = path_part[1:-1]
        if not (path_part == f"work/{TASK_ID}" or path_part.startswith(f"work/{TASK_ID}/")):
            outside_work.append(line)
        if not any(path_part == pref or path_part.startswith(pref) for pref in ALLOWED_PREFIXES):
            disallowed.append(line)
    return lines, outside_work, disallowed


def resolve_base_ref():
    res = run_cmd(["git", "rev-parse", "--verify", "org/main"], cwd=REPO)
    if res.returncode == 0:
        return "org/main", res.stdout.strip(), False
    mb = run_cmd(["git", "merge-base", "HEAD", "main"], cwd=REPO)
    if mb.returncode == 0:
        sha = mb.stdout.strip()
        print("INFO: org/main not found; falling back to merge-base with HEAD:", sha)
        return sha, sha, True
    head = run_cmd(["git", "rev-parse", "HEAD"], cwd=REPO)
    sha = head.stdout.strip()
    print("INFO: org/main not found; falling back to HEAD:", sha)
    return sha, sha, True


def extract_catch_version(catch_hpp):
    text = catch_hpp.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Catch\s+v(\d+\.\d+\.\d+)", text)
    return m.group(1) if m else "2.13.6"


def evaluate(build_rc, run_rc, xml_content, expected_cases, named_cases, list_count=None):
    failures = []
    if build_rc != 0:
        failures.append(f"build_rc={build_rc} (expected 0)")
    if run_rc != 0:
        failures.append(f"run_rc={run_rc} (expected 0)")
    if not xml_content or not xml_content.strip():
        failures.append("XML output is missing or empty")
        return failures, {}

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        failures.append(f"XML parse error: {exc}")
        return failures, {}

    overall_cases = root.findall(".//OverallResultsCases")
    if not overall_cases:
        failures.append("Missing OverallResultsCases element in XML")
        return failures, {}

    top_overall = overall_cases[-1]
    successes = int(top_overall.attrib.get("successes", "0"))
    fail_count = int(top_overall.attrib.get("failures", "0"))
    expected_failures = int(top_overall.attrib.get("expectedFailures", "0"))

    total = successes + fail_count
    if total == 0:
        failures.append("ZERO-TEST GUARD: OverallResultsCases successes+failures == 0")
    if total != expected_cases:
        failures.append(f"Total executed cases {total} != expected {expected_cases}")
    if fail_count > 0:
        failures.append(f"OverallResultsCases reported failures={fail_count}")
    if expected_failures > 0:
        failures.append(f"OverallResultsCases reported expectedFailures={expected_failures}")

    case_map = {}
    case_list = []
    for tc in root.findall(".//TestCase"):
        name = tc.attrib.get("name", "")
        tags = tc.attrib.get("tags", "")
        overall = tc.find("OverallResult")
        passed = (overall.attrib.get("success", "false") == "true") if overall is not None else False
        case_map[name] = {"name": name, "tags": tags, "passed": passed, "line": tc.attrib.get("line", "")}
        case_list.append(case_map[name])

    if len(case_list) != total:
        failures.append(f"TestCase element count {len(case_list)} != OverallResultsCases total {total}")

    for named in named_cases:
        if named not in case_map:
            failures.append(f"Named case missing from XML: {named!r}")
        elif not case_map[named]["passed"]:
            failures.append(f"Named case did not pass: {named!r}")

    if list_count is not None and list_count != total:
        failures.append(f"--list-test-names-only count {list_count} != XML case count {total}")

    return failures, {
        "successes": successes,
        "failures": fail_count,
        "total": total,
        "cases": case_list,
        "case_map": case_map,
    }


def extract_temp_dir(stdout_text):
    m = re.search(r"^TEMP_DIR:\s*(.+)$", stdout_text, re.M)
    return Path(m.group(1).strip()) if m else None


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    failures = []

    def record(label, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {label}" + (f" ({detail})" if detail else ""))
        if not ok:
            failures.append(f"{label}: {detail}" if detail else label)

    initial_ex_hashes = snapshot_directory_hashes(EX)
    _, pre_outside_work, pre_disallowed = git_status_snapshot()
    record("Working tree contains no changes outside ALLOWED FILES before check", len(pre_disallowed) == 0, "clean" if not pre_disallowed else "; ".join(pre_disallowed))

    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t049-check-"))
    executed_cases = 0
    scenario_records = []

    try:
        config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
        files_cfg = config_data.get("files", {})
        record("No 'editor' key in .meta/config.json files", "editor" not in files_cfg, "editor key absent")

        ex_resolved = EX.resolve()
        all_inside = True
        for role in ("solution", "test", "example"):
            for rel_str in files_cfg.get(role, []):
                p = (EX / rel_str).resolve()
                try:
                    p.relative_to(ex_resolved)
                except ValueError:
                    all_inside = False
                if not p.is_file():
                    all_inside = False
        record("All solution/test/example files exist and stay inside exercise directory", all_inside, json.dumps(files_cfg))

        base_ref, base_sha, used_fallback_ref = resolve_base_ref()
        protected_rel = [
            "exercises/practice/bank-account/bank_account.cpp",
            "exercises/practice/bank-account/bank_account.h",
            "exercises/practice/bank-account/bank_account_test.cpp",
            "exercises/practice/bank-account/.docs/instructions.md",
        ]
        diff_res = run_cmd(["git", "diff", "--quiet", base_ref, "--"] + protected_rel, cwd=REPO)
        record(f"Learner stub, test file, and instructions.md equal {base_ref}", diff_res.returncode == 0, f"base={base_ref} ({base_sha[:12]})")

        doc_path = REPO / "docs" / "maintenance" / "bank-account.md"
        doc_ok = doc_path.is_file() and "Threads::Threads" in doc_path.read_text(encoding="utf-8") and "r20-t049.py" in doc_path.read_text(encoding="utf-8")
        record("docs/maintenance/bank-account.md documents command, Threads requirement, scenarios, and safety guarantees", doc_ok, "bank-account.md")

        # Scenario 1: Real reference -> exit 0 with 17 cases
        s1_before = snapshot_directory_hashes(EX)
        s1_xml = tmp_dir / "s1_results.xml"
        s1_list = tmp_dir / "s1_list.txt"
        s1_cmd = [sys.executable, str(TOOL_PATH), "--exercise", SLUG, "--xml-out", str(s1_xml), "--list-out", str(s1_list)]
        s1_res = run_cmd(s1_cmd, cwd=REPO)
        write_log("scenario1-real.log", s1_cmd, s1_res, tmp_dir)
        s1_after = snapshot_directory_hashes(EX)
        s1_tmp = extract_temp_dir(s1_res.stdout)
        s1_cleaned = s1_tmp is not None and not s1_tmp.exists()
        raw_xml = s1_xml.read_text(encoding="utf-8") if s1_xml.is_file() else ""
        norm_xml = clean_eof_and_trailing_ws(normalise_xml(raw_xml, tmp_dir=tmp_dir))
        (WORK_DIR / "results.xml").write_text(norm_xml, encoding="utf-8")
        listed_names = [line.strip() for line in s1_list.read_text(encoding="utf-8").splitlines() if line.strip()] if s1_list.is_file() else []
        (WORK_DIR / "test-list.log").write_text(clean_eof_and_trailing_ws("\n".join(listed_names)), encoding="utf-8")

        eval_failures, eval_details = evaluate(0, s1_res.returncode, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        executed_cases = eval_details.get("total", 0)
        s1_ok = (
            s1_res.returncode == 0
            and len(eval_failures) == 0
            and f"RESULT: PASS - executed {EXPECTED_CASES} cases" in s1_res.stdout
            and s1_cleaned
            and s1_before == s1_after
        )
        record("Scenario 1 (real reference via r20-t049.py) exits 0 with 17 cases and cleans up temp dir", s1_ok, f"rc={s1_res.returncode}, cases={executed_cases}")
        scenario_records.append({"scenario": "real_reference", "expected_rc": 0, "actual_rc": s1_res.returncode, "temp_dir_cleaned": s1_cleaned, "hashes_identical": s1_before == s1_after, "passed": s1_ok})

        # Scenario 2: Deliberately failing reference (--reference-dir)
        s2_before = snapshot_directory_hashes(EX)
        bad_ref = tmp_dir / "bad_ref"
        bad_ref.mkdir(parents=True, exist_ok=True)
        shutil.copy2(EX / ".meta" / "example.h", bad_ref / "example.h")
        orig_cpp = (EX / ".meta" / "example.cpp").read_text(encoding="utf-8")
        bad_cpp = orig_cpp.replace("balance_ += amount;", "balance_ += amount + 1;")
        (bad_ref / "example.cpp").write_text(bad_cpp, encoding="utf-8")
        s2_cmd = [sys.executable, str(TOOL_PATH), "--exercise", SLUG, "--reference-dir", str(bad_ref)]
        s2_res = run_cmd(s2_cmd, cwd=REPO)
        write_log("scenario2-failing-ref.log", s2_cmd, s2_res, tmp_dir)
        s2_after = snapshot_directory_hashes(EX)
        s2_tmp = extract_temp_dir(s2_res.stdout)
        s2_cleaned = s2_tmp is not None and not s2_tmp.exists()
        s2_ok = s2_res.returncode != 0 and s2_cleaned and s2_before == s2_after and "RESULT: FAIL" in s2_res.stdout
        record("Scenario 2 (deliberately failing reference) exits non-zero, cleans temp dir, preserves hashes", s2_ok, f"rc={s2_res.returncode}")
        scenario_records.append({"scenario": "failing_reference", "expected_rc": "non-zero", "actual_rc": s2_res.returncode, "temp_dir_cleaned": s2_cleaned, "hashes_identical": s2_before == s2_after, "passed": s2_ok})

        # Scenario 3: Empty test selection (--filter "no-such-test*")
        s3_before = snapshot_directory_hashes(EX)
        s3_cmd = [sys.executable, str(TOOL_PATH), "--exercise", SLUG, "--filter", "no-such-test*"]
        s3_res = run_cmd(s3_cmd, cwd=REPO)
        write_log("scenario3-zero-tests.log", s3_cmd, s3_res, tmp_dir)
        s3_after = snapshot_directory_hashes(EX)
        s3_tmp = extract_temp_dir(s3_res.stdout)
        s3_cleaned = s3_tmp is not None and not s3_tmp.exists()
        s3_ok = s3_res.returncode != 0 and "ZERO-TEST GUARD" in s3_res.stdout and s3_cleaned and s3_before == s3_after
        record("Scenario 3 (empty filter) exits non-zero via ZERO-TEST GUARD, cleans temp dir, preserves hashes", s3_ok, f"rc={s3_res.returncode}")
        scenario_records.append({"scenario": "empty_test_selection", "expected_rc": "non-zero", "actual_rc": s3_res.returncode, "temp_dir_cleaned": s3_cleaned, "hashes_identical": s3_before == s3_after, "passed": s3_ok})

        # Scenario 4: Interrupted run (send SIGINT mid-build after TEMP_DIR is printed)
        s4_before = snapshot_directory_hashes(EX)
        s4_cmd = [sys.executable, str(TOOL_PATH), "--exercise", SLUG]
        proc = subprocess.Popen(
            s4_cmd,
            cwd=str(REPO),
            env=ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        printed_lines = []
        s4_tmp = None
        deadline = time.time() + 20.0
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            printed_lines.append(line)
            if line.startswith("TEMP_DIR:"):
                s4_tmp = Path(line.split("TEMP_DIR:", 1)[1].strip())
                # Let cmake start creating files in the temp dir before interrupting
                time.sleep(0.5)
                proc.send_signal(signal.SIGINT)
                break
        rest_out, rest_err = proc.communicate(timeout=30)
        s4_stdout = "".join(printed_lines) + (rest_out or "")
        s4_rc = proc.returncode
        s4_log_path = WORK_DIR / "scenario4-sigint.log"
        if not s4_log_path.is_file():
            s4_log_path.write_text(
                clean_eof_and_trailing_ws(normalise_text(f"$ {' '.join(s4_cmd)} (SIGINT sent)\nexit_code: {s4_rc}\n--- stdout ---\n{s4_stdout}\n--- stderr ---\n{rest_err or ''}", tmp_dir=tmp_dir)),
                encoding="utf-8",
            )
        s4_after = snapshot_directory_hashes(EX)
        s4_cleaned = s4_tmp is not None and not s4_tmp.exists()
        s4_ok = s4_rc != 0 and s4_cleaned and s4_before == s4_after
        record("Scenario 4 (SIGINT mid-build) removes temp dir, exits non-zero, preserves learner hashes", s4_ok, f"rc={s4_rc}, temp_gone={s4_cleaned}")
        scenario_records.append({"scenario": "interrupted_sigint", "expected_rc": "non-zero", "actual_rc": s4_rc, "temp_dir_cleaned": s4_cleaned, "hashes_identical": s4_before == s4_after, "passed": s4_ok})

        # Negative Control 3: Synthetic non-zero child exit with passing XML
        nc3_run_f, _ = evaluate(0, 1, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_bld_f, _ = evaluate(2, 0, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_ok = any("run_rc=1" in f for f in nc3_run_f) and any("build_rc=2" in f for f in nc3_bld_f)
        record("Negative control (non-zero child return code with passing XML) rejected by evaluate()", nc3_ok, f"run={nc3_run_f}; bld={nc3_bld_f}")

        # Evidence JSON files
        cmake_ver_res = run_cmd(["cmake", "--version"], cwd=REPO)
        cxx_ver_res = run_cmd(["c++", "--version"], cwd=REPO)
        head_res = run_cmd(["git", "rev-parse", "HEAD"], cwd=REPO)

        versions_payload = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "tomllib_available": tomllib is not None,
            },
            "cmake": {
                "version_line": cmake_ver_res.stdout.splitlines()[0] if cmake_ver_res.stdout else "",
                "generator": "Unix Makefiles",
                "cmake_policy_version_minimum_used": None,
            },
            "compiler": {
                "id": "AppleClang",
                "version_line": cxx_ver_res.stdout.splitlines()[0] if cxx_ver_res.stdout else "",
            },
            "catch2": {
                "version": extract_catch_version(EX / "test" / "catch.hpp"),
                "header": "exercises/practice/bank-account/test/catch.hpp",
            },
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "platform": platform.platform().replace("-Mach-O", ""),
            },
            "git": {
                "head": head_res.stdout.strip(),
                "base_ref": base_ref,
                "org_main_sha": base_sha,
                "used_fallback_ref": used_fallback_ref,
            },
        }
        versions_file = WORK_DIR / "versions.json"
        if versions_file.is_file():
            try:
                existing_ver = json.loads(versions_file.read_text(encoding="utf-8"))
                if existing_ver.get("git", {}).get("org_main_sha") == base_sha:
                    versions_payload["python"] = existing_ver.get("python", versions_payload["python"])
                    versions_payload["git"]["head"] = existing_ver.get("git", {}).get("head", versions_payload["git"]["head"])
            except Exception:
                pass
        versions_file.write_text(json.dumps(versions_payload, indent=2) + "\n", encoding="utf-8")

        test_cpp_text = (EX / "bank_account_test.cpp").read_text(encoding="utf-8")
        static_cases = re.findall(r'TEST_CASE\(\s*"([^"]+)"\s*,\s*"\[([0-9a-f\-]{36})\]"\s*\)', test_cpp_text)
        toml_data = parse_tests_toml((EX / ".meta" / "tests.toml").read_text(encoding="utf-8"))

        counts_payload = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_cases": EXPECTED_CASES,
            "static_test_case_count": len(static_cases),
            "xml_executed_case_count": executed_cases,
            "xml_passed_case_count": eval_details.get("successes", 0),
            "xml_failed_case_count": eval_details.get("failures", 0),
            "list_test_names_only_count": len(listed_names),
            "tests_toml_total": len(toml_data),
            "tests_toml_included": len([u for u, kv in toml_data.items() if kv.get("include", True) is True]),
            "tests_toml_excluded": len([u for u, kv in toml_data.items() if kv.get("include", True) is False]),
            "scenarios": scenario_records,
        }
        (WORK_DIR / "counts.json").write_text(json.dumps(counts_payload, indent=2) + "\n", encoding="utf-8")

        neg_payload = {
            "task_id": TASK_ID,
            "all_controls_behaved_as_expected": bool(s2_ok and s3_ok and s4_ok and nc3_ok),
            "controls": {
                "assertion_failure": {
                    "scenario": "failing_reference (--reference-dir)",
                    "run_rc": s2_res.returncode,
                    "temp_dir_cleaned": s2_cleaned,
                    "hashes_identical": s2_before == s2_after,
                    "rejected_as_expected": s2_ok,
                },
                "zero_tests": {
                    "filter": "no-such-test*",
                    "runner_rc": s3_res.returncode,
                    "temp_dir_cleaned": s3_cleaned,
                    "hashes_identical": s3_before == s3_after,
                    "rejected_as_expected": s3_ok,
                },
                "interrupted_sigint": {
                    "signal": "SIGINT",
                    "runner_rc": s4_rc,
                    "temp_dir_cleaned": s4_cleaned,
                    "hashes_identical": s4_before == s4_after,
                    "rejected_as_expected": s4_ok,
                },
                "child_failure": {
                    "synthetic_run_rc_1_failures": nc3_run_f,
                    "synthetic_build_rc_2_failures": nc3_bld_f,
                    "rejected_as_expected": nc3_ok,
                },
            },
        }
        (WORK_DIR / "negative-controls.json").write_text(json.dumps(neg_payload, indent=2) + "\n", encoding="utf-8")

        cases_comparison = []
        for idx, (tc_name, tc_uuid) in enumerate(static_cases, start=1):
            xml_case = eval_details.get("case_map", {}).get(tc_name, {})
            cases_comparison.append(
                {
                    "index": idx,
                    "uuid": tc_uuid,
                    "name": tc_name,
                    "is_named_case": tc_name in NAMED_CASES,
                    "expected_pass": True,
                    "actual_pass": bool(xml_case.get("passed", False)),
                    "test_file_line": xml_case.get("line", ""),
                }
            )
        expected_vs_actual = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_executed_cases": EXPECTED_CASES,
            "actual_executed_cases": executed_cases,
            "named_cases": NAMED_CASES,
            "scenario_table": scenario_records,
            "cases": cases_comparison,
        }
        (WORK_DIR / "expected-vs-actual.json").write_text(json.dumps(expected_vs_actual, indent=2) + "\n", encoding="utf-8")

    except Exception as exc:
        record("Unexpected exception in check.py", False, f"{type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        record("Temporary directory removed in finally block", not tmp_dir.exists(), "<TMP>")

        final_ex_hashes = snapshot_directory_hashes(EX)
        ex_unchanged = initial_ex_hashes == final_ex_hashes
        record("All files under exercises/practice/bank-account unchanged across all scenarios", ex_unchanged, f"hashed {len(final_ex_hashes)} files")

        _, post_outside_work, post_disallowed = git_status_snapshot()
        git_state_ok = (pre_outside_work == post_outside_work) and (len(post_disallowed) == 0)
        record("git status outside work/R20-T049/ unchanged and restricted to ALLOWED FILES", git_state_ok, "unchanged" if git_state_ok else f"disallowed={post_disallowed}")

        try:
            config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
            files_cfg = config_data.get("files", {})
            inputs_payload = {
                "task_id": TASK_ID,
                "exercise": SLUG,
                "exercise_dir": "<REPO>/exercises/practice/bank-account",
                "config_files": files_cfg,
                "has_editor_key": "editor" in files_cfg,
                "resolved_paths": {
                    role: [normalise_text(str((EX / r).resolve())) for r in files_cfg.get(role, [])]
                    for role in ("solution", "test", "example")
                },
                "expected_cases": EXPECTED_CASES,
                "named_cases": NAMED_CASES,
                "exercise_file_sha256_before": initial_ex_hashes,
                "exercise_file_sha256_after": final_ex_hashes,
                "exercise_files_unchanged_during_run": ex_unchanged,
            }
            (WORK_DIR / "inputs.json").write_text(json.dumps(inputs_payload, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            failures.append(f"Failed to write inputs.json: {exc}")

    if not failures:
        print(f"RESULT: PASS - executed {executed_cases} cases")
        return 0
    print("RESULT: FAIL - " + "; ".join(failures))
    return 1


if __name__ == "__main__":
    sys.exit(main())
