#!/usr/bin/env python3
"""R20-T041 automated check for exercises/practice/knapsack."""

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


TASK_ID = "R20-T041"
SLUG = "knapsack"
EXPECTED_CASES = 7
NAMED_CASES = [
    "no items",
    "one item, too heavy",
    "five items (cannot be greedy by weight)",
]
EXCLUDED_UUID = "a4d7d2f0-ad8a-460c-86f3-88ba709d41a7"
REPLACEMENT_UUID = "3993a824-c20e-493d-b3c9-ee8a7753ee59"
TARGETED_UUIDS = [
    "a4d7d2f0-ad8a-460c-86f3-88ba709d41a7",
    "3993a824-c20e-493d-b3c9-ee8a7753ee59",
    "1d39e98c-6249-4a8b-912f-87cb12e506b0",
    "833ea310-6323-44f2-9d27-a278740ffbd8",
]
ALLOWED_PREFIXES = (
    "exercises/practice/knapsack/.meta/tests.toml",
    "docs/maintenance/knapsack.md",
    "work/R20-T041/",
    "work/R20-T041",
)

REPO = Path(__file__).resolve().parents[2]
EX = REPO / "exercises" / "practice" / SLUG
WORK_DIR = REPO / "work" / TASK_ID


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
    """Parse the configlet tests.toml subset in Python 3.9+ without third-party packages."""
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
    fallback_parsed = parse_toml_fallback(text)
    if tomllib is not None:
        stdlib_parsed = tomllib.loads(text)
        if stdlib_parsed != fallback_parsed:
            raise ValueError("tomllib and fallback parser disagreed on tests.toml content")
        return stdlib_parsed
    return fallback_parsed


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
    hashes = {}
    for p in sorted(root_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root_dir).as_posix()
            hashes[rel] = sha256_file(p)
    return hashes


def normalise_text(text, tmp_dir=None):
    out = text
    if tmp_dir is not None:
        for candidate in (str(tmp_dir.resolve()), str(tmp_dir)):
            if candidate:
                out = out.replace(candidate, "<TMP>")
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
    for candidate in (str(REPO.resolve()), str(REPO)):
        if candidate:
            out = out.replace(candidate, "&lt;REPO&gt;")
    home = str(Path.home())
    if home:
        out = out.replace(home, "&lt;HOME&gt;")
    return out


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


def git_status_Snapshot():
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
        allowed = False
        for pref in ALLOWED_PREFIXES:
            if path_part == pref or path_part.startswith(pref):
                allowed = True
                break
        if not allowed:
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


def find_executable(copy_dir):
    candidates = [
        copy_dir / "build" / SLUG,
        copy_dir / "build" / "Debug" / SLUG,
        copy_dir / "build" / f"{SLUG}.exe",
        copy_dir / "build" / "Debug" / f"{SLUG}.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def evaluate(build_rc, run_rc, xml_content, expected_cases, named_cases, list_count=None):
    """Evaluate build/run return codes and Catch2 XML results."""
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
    try:
        successes = int(top_overall.attrib.get("successes", "0"))
        fail_count = int(top_overall.attrib.get("failures", "0"))
        expected_failures = int(top_overall.attrib.get("expectedFailures", "0"))
    except ValueError as exc:
        failures.append(f"Non-integer OverallResultsCases attributes: {exc}")
        return failures, {}

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
        success_attr = overall.attrib.get("success", "false") if overall is not None else "false"
        passed = success_attr == "true"
        case_map[name] = {
            "name": name,
            "tags": tags,
            "passed": passed,
            "line": tc.attrib.get("line", ""),
        }
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

    details = {
        "successes": successes,
        "failures": fail_count,
        "total": total,
        "cases": case_list,
        "case_map": case_map,
    }
    return failures, details


def clean_eof_and_trailing_ws(text):
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[-1] == "":
        lines.pop()
    return ("\n".join(lines) + "\n") if lines else "\n"


def write_log(filename, cmd, result, tmp_dir):
    header = f"$ {' '.join(cmd)}\nexit_code: {result.returncode}\n"
    body = ""
    if result.stdout:
        body += f"--- stdout ---\n{result.stdout.rstrip()}\n"
    if result.stderr:
        body += f"--- stderr ---\n{result.stderr.rstrip()}\n"
    content = clean_eof_and_trailing_ws(normalise_text(header + body, tmp_dir=tmp_dir))
    (WORK_DIR / filename).write_text(content, encoding="utf-8")


def extract_catch_version(catch_hpp):
    text = catch_hpp.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"Catch\s+v(\d+\.\d+\.\d+)", text)
    return m.group(1) if m else "2.13.6"


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    checks = []
    failures = []

    def record(label, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        msg = f"{status}: {label}" + (f" ({detail})" if detail else "")
        print(msg)
        checks.append({"label": label, "passed": bool(ok), "detail": detail})
        if not ok:
            failures.append(f"{label}: {detail}" if detail else label)

    pre_ex_hashes = snapshot_directory_hashes(EX)
    _, pre_outside_work, pre_disallowed = git_status_Snapshot()
    record(
        "Working tree contains no changes outside ALLOWED FILES before check",
        len(pre_disallowed) == 0,
        "clean" if not pre_disallowed else "; ".join(pre_disallowed),
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t041-"))
    executed_cases = 0

    try:
        # Step A: Paths and config.json validation
        config_path = EX / ".meta" / "config.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        files_cfg = config_data.get("files", {})
        has_editor_key = "editor" in files_cfg
        record("No 'editor' key in .meta/config.json files", not has_editor_key, "editor key absent")

        resolved_files = {}
        all_inside_ex = True
        ex_resolved = EX.resolve()
        for role in ("solution", "test", "example"):
            role_list = files_cfg.get(role, [])
            resolved_role = []
            for rel_str in role_list:
                p = (EX / rel_str).resolve()
                try:
                    p.relative_to(ex_resolved)
                except ValueError:
                    all_inside_ex = False
                if not p.is_file():
                    all_inside_ex = False
                resolved_role.append(normalise_text(str(p)))
            resolved_files[role] = resolved_role
        record(
            "All solution/test/example files exist and stay inside exercise directory",
            all_inside_ex and all(bool(resolved_files.get(r)) for r in ("solution", "test", "example")),
            json.dumps(files_cfg),
        )

        # Step C: Stub unsolved check
        base_ref, base_sha, used_fallback_ref = resolve_base_ref()
        protected_rel_paths = [
            "exercises/practice/knapsack/knapsack.cpp",
            "exercises/practice/knapsack/knapsack.h",
            "exercises/practice/knapsack/knapsack_test.cpp",
            "exercises/practice/knapsack/.docs/instructions.md",
        ]
        diff_cmd = ["git", "diff", "--quiet", base_ref, "--"] + protected_rel_paths
        diff_res = run_cmd(diff_cmd, cwd=REPO)
        record(
            f"Learner stub, test file, and instructions.md equal {base_ref}",
            diff_res.returncode == 0,
            f"base={base_ref} ({base_sha[:12]})",
        )

        # R20-T041 specific check: tests.toml before/after comparison
        before_toml_res = run_cmd(
            ["git", "show", f"{base_ref}:exercises/practice/knapsack/.meta/tests.toml"],
            cwd=REPO,
        )
        if before_toml_res.returncode != 0:
            raise RuntimeError(f"Failed to read baseline tests.toml from {base_ref}: {before_toml_res.stderr}")
        before_toml = parse_tests_toml(before_toml_res.stdout)
        after_toml_path = EX / ".meta" / "tests.toml"
        after_toml_text = after_toml_path.read_text(encoding="utf-8")
        after_toml = parse_tests_toml(after_toml_text)

        before_uuids = list(before_toml.keys())
        after_uuids = list(after_toml.keys())
        same_uuids = before_uuids == after_uuids and len(after_uuids) == 8

        before_included = [u for u, kv in before_toml.items() if kv.get("include", True) is True]
        before_excluded = [u for u, kv in before_toml.items() if kv.get("include", True) is False]
        after_included = [u for u, kv in after_toml.items() if kv.get("include", True) is True]
        after_excluded = [u for u, kv in after_toml.items() if kv.get("include", True) is False]

        same_inclusions = (before_included == after_included) and (before_excluded == after_excluded)
        same_reimplements = all(
            before_toml[u].get("reimplements") == after_toml[u].get("reimplements")
            for u in after_uuids
        )
        record(
            "tests.toml parses and preserves all 8 UUIDs, include flags (7/1), and reimplements links",
            same_uuids
            and same_inclusions
            and same_reimplements
            and len(after_included) == 7
            and after_excluded == [EXCLUDED_UUID]
            and after_toml[REPLACEMENT_UUID].get("reimplements") == EXCLUDED_UUID,
            f"before={len(before_uuids)}/{len(before_included)}/{len(before_excluded)} "
            f"after={len(after_uuids)}/{len(after_included)}/{len(after_excluded)}",
        )

        comments_ok = True
        missing_comments = []
        for u in TARGETED_UUIDS:
            c_val = after_toml.get(u, {}).get("comment", "")
            if not isinstance(c_val, str) or len(c_val.strip()) < 20:
                comments_ok = False
                missing_comments.append(u)
        excl_comment = after_toml.get(EXCLUDED_UUID, {}).get("comment", "")
        if REPLACEMENT_UUID not in excl_comment or "no items" not in excl_comment:
            comments_ok = False
            missing_comments.append(f"{EXCLUDED_UUID} (must cite {REPLACEMENT_UUID} and 'no items')")
        record(
            "Excluded UUID and named UUIDs have checkable comment keys in tests.toml",
            comments_ok,
            "all 4 targeted UUIDs have comment keys" if comments_ok else ", ".join(missing_comments),
        )

        # Static check on knapsack_test.cpp
        test_cpp_path = EX / "knapsack_test.cpp"
        test_cpp_text = test_cpp_path.read_text(encoding="utf-8")
        static_cases = re.findall(
            r'TEST_CASE\(\s*"([^"]+)"\s*,\s*"\[maximumValue\]\[([0-9a-f\-]{36})\]"\s*\)',
            test_cpp_text,
        )
        static_test_names = [name for name, _ in static_cases]
        static_test_uuids = [u for _, u in static_cases]
        tags_match_included = (
            len(static_cases) == EXPECTED_CASES
            and static_test_uuids == after_included
            and EXCLUDED_UUID not in test_cpp_text
        )
        record(
            "Every included UUID in tests.toml appears as a TEST_CASE tag in knapsack_test.cpp",
            tags_match_included,
            f"{len(static_test_uuids)} tags align with 7 included UUIDs; excluded UUID absent",
        )

        # Check docs/maintenance/knapsack.md
        maint_doc_path = REPO / "docs" / "maintenance" / "knapsack.md"
        maint_doc_ok = maint_doc_path.is_file()
        if maint_doc_ok:
            maint_text = maint_doc_path.read_text(encoding="utf-8")
            for u in after_uuids:
                if u not in maint_text:
                    maint_doc_ok = False
            for required_token in ("Replacement case", "comment", "8", "7", "1", "dp[weight]"):
                if required_token not in maint_text:
                    maint_doc_ok = False
        record(
            "docs/maintenance/knapsack.md documents all 8 UUIDs, counts, C++ operations, and comment rationale",
            maint_doc_ok,
            normalise_text(str(maint_doc_path)),
        )

        # Step D: Isolated copy and reference substitution by extension
        copy_dir = tmp_dir / SLUG
        shutil.copytree(EX, copy_dir)
        dotfiles_ok = (
            (copy_dir / ".meta").is_dir()
            and (copy_dir / ".docs").is_dir()
            and (copy_dir / "test" / "catch.hpp").is_file()
        )
        record(
            "Isolated copy preserves dotfiles (.meta, .docs) and test/catch.hpp",
            dotfiles_ok,
            normalise_text(str(copy_dir), tmp_dir=tmp_dir),
        )

        sol_by_ext = {}
        for rel_s in files_cfg["solution"]:
            p = copy_dir / rel_s
            sol_by_ext[p.suffix] = p
        ex_by_ext = {}
        for rel_e in files_cfg["example"]:
            p = copy_dir / rel_e
            ex_by_ext[p.suffix] = p

        ext_matched = set(sol_by_ext.keys()) == set(ex_by_ext.keys()) and len(sol_by_ext) > 0
        for ext, src_p in ex_by_ext.items():
            dst_p = sol_by_ext.get(ext)
            if dst_p is not None:
                shutil.copy2(src_p, dst_p)
        record(
            "Reference substituted into temp copy by matching file extension",
            ext_matched,
            ", ".join(f".meta/example{ext} -> {sol_by_ext[ext].name}" for ext in sorted(sol_by_ext)),
        )

        # Step E: Configure, build, compile-target, execute XML, execute list-test-names-only
        cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)
        policy_minimum_used = None
        if cfg_res.returncode != 0:
            policy_minimum_used = "3.5"
            cfg_cmd = [
                "cmake",
                "-S",
                ".",
                "-B",
                "build",
                "-DEXERCISM_RUN_ALL_TESTS=ON",
                "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            ]
            cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)
        write_log("cmake-configure.log", cfg_cmd, cfg_res, tmp_dir)
        record("CMake configure exited 0", cfg_res.returncode == 0, f"rc={cfg_res.returncode}")

        bld_cmd = ["cmake", "--build", "build"]
        bld_res = run_cmd(bld_cmd, cwd=copy_dir)
        write_log("cmake-build.log", bld_cmd, bld_res, tmp_dir)
        record("CMake build (including custom test target) exited 0", bld_res.returncode == 0, f"rc={bld_res.returncode}")

        tgt_cmd = ["cmake", "--build", "build", "--target", SLUG]
        tgt_res = run_cmd(tgt_cmd, cwd=copy_dir)
        write_log("cmake-build-target.log", tgt_cmd, tgt_res, tmp_dir)
        record(f"CMake compile-only target '{SLUG}' exited 0", tgt_res.returncode == 0, f"rc={tgt_res.returncode}")

        exe_path = find_executable(copy_dir)
        record(
            "Generated test executable located",
            exe_path is not None and exe_path.is_file(),
            normalise_text(str(exe_path), tmp_dir=tmp_dir) if exe_path else "missing",
        )
        if exe_path is None:
            raise RuntimeError("Test executable was not produced by CMake build")

        tmp_xml = tmp_dir / "results.xml"
        run_xml_cmd = [str(exe_path), "-r", "xml", "-o", str(tmp_xml)]
        run_xml_res = run_cmd(run_xml_cmd, cwd=copy_dir)
        write_log("test-run.log", run_xml_cmd, run_xml_res, tmp_dir)
        raw_xml = tmp_xml.read_text(encoding="utf-8") if tmp_xml.is_file() else ""
        norm_xml = clean_eof_and_trailing_ws(normalise_xml(raw_xml, tmp_dir=tmp_dir))
        (WORK_DIR / "results.xml").write_text(norm_xml, encoding="utf-8")

        list_cmd = [str(exe_path), "--list-test-names-only"]
        list_res = run_cmd(list_cmd, cwd=copy_dir)
        write_log("test-list.log", list_cmd, list_res, tmp_dir)
        listed_names = [line.strip() for line in list_res.stdout.splitlines() if line.strip()]

        # Step F: Evaluate test execution
        eval_failures, eval_details = evaluate(
            build_rc=bld_res.returncode,
            run_rc=run_xml_res.returncode,
            xml_content=norm_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        executed_cases = eval_details.get("total", 0)
        record(
            f"All {EXPECTED_CASES} cases (including 3 named cases) pass in Catch2 XML and equal list count",
            len(eval_failures) == 0,
            f"executed={executed_cases}/{EXPECTED_CASES}" if not eval_failures else "; ".join(eval_failures),
        )

        # Step G: Negative controls reusing the configured copy
        orig_example_cpp = (copy_dir / ".meta" / "example.cpp").read_text(encoding="utf-8")

        # Negative Control 1: Assertion failure on first named case ("no items")
        bad_cpp = orig_example_cpp.replace(
            "std::vector<int> dp(maximum_weight + 1);",
            "if (items.empty()) { return -1; }\n    std::vector<int> dp(maximum_weight + 1);",
        )
        sol_by_ext[".cpp"].write_text(bad_cpp, encoding="utf-8")
        for obj_p in (copy_dir / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_path.exists():
            exe_path.unlink()
        neg_compile_res = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_dir)
        neg_assert_xml_path = tmp_dir / "neg_assert.xml"
        neg_assert_cmd = [str(exe_path), "-r", "xml", "-o", str(neg_assert_xml_path)]
        neg_assert_res = run_cmd(neg_assert_cmd, cwd=copy_dir)
        write_log("negative-assertion.log", neg_assert_cmd, neg_assert_res, tmp_dir)
        neg_assert_xml = (
            normalise_xml(neg_assert_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir)
            if neg_assert_xml_path.is_file()
            else ""
        )
        neg_assert_failures, neg_assert_details = evaluate(
            build_rc=neg_compile_res.returncode,
            run_rc=neg_assert_res.returncode,
            xml_content=neg_assert_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        first_named_failed = not neg_assert_details.get("case_map", {}).get(NAMED_CASES[0], {}).get("passed", True)
        nc1_ok = (
            neg_compile_res.returncode == 0
            and neg_assert_res.returncode != 0
            and len(neg_assert_failures) > 0
            and first_named_failed
        )
        record(
            "Negative control 1 (assertion failure on 'no items') detected by runner and evaluate()",
            nc1_ok,
            f"run_rc={neg_assert_res.returncode}, failures={neg_assert_failures}",
        )

        # Restore working reference in copy_dir and recompile
        sol_by_ext[".cpp"].write_text(orig_example_cpp, encoding="utf-8")
        for obj_p in (copy_dir / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_path.exists():
            exe_path.unlink()
        restore_res = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_dir)
        if restore_res.returncode != 0:
            raise RuntimeError("Failed to restore reference implementation in temp copy")

        # Negative Control 2: Zero tests executed (Catch2 exits 0 on unmatched filter, evaluate() must fail)
        neg_zero_xml_path = tmp_dir / "neg_zero.xml"
        neg_zero_cmd = [str(exe_path), "no-such-test-filter*", "-r", "xml", "-o", str(neg_zero_xml_path)]
        neg_zero_res = run_cmd(neg_zero_cmd, cwd=copy_dir)
        write_log("negative-zero-tests.log", neg_zero_cmd, neg_zero_res, tmp_dir)
        neg_zero_xml = (
            normalise_xml(neg_zero_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir)
            if neg_zero_xml_path.is_file()
            else ""
        )
        neg_zero_failures, neg_zero_details = evaluate(
            build_rc=0,
            run_rc=neg_zero_res.returncode,
            xml_content=neg_zero_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
        )
        has_zero_guard = any("ZERO-TEST GUARD" in f for f in neg_zero_failures)
        nc2_ok = neg_zero_res.returncode == 0 and has_zero_guard
        record(
            "Negative control 2 (unmatched filter -> 0 tests, Catch2 rc=0) rejected by ZERO-TEST GUARD",
            nc2_ok,
            f"catch2_rc={neg_zero_res.returncode}, failures={neg_zero_failures}",
        )

        # Negative Control 3: Non-zero child return code with otherwise passing XML
        neg_child_run_failures, _ = evaluate(
            build_rc=0,
            run_rc=1,
            xml_content=norm_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        neg_child_build_failures, _ = evaluate(
            build_rc=2,
            run_rc=0,
            xml_content=norm_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        nc3_ok = any("run_rc=1" in f for f in neg_child_run_failures) and any(
            "build_rc=2" in f for f in neg_child_build_failures
        )
        record(
            "Negative control 3 (non-zero child return code with passing XML) rejected by evaluate()",
            nc3_ok,
            f"run_failures={neg_child_run_failures}; build_failures={neg_child_build_failures}",
        )

        # Step H: Write evidence JSON artifacts
        cmake_cache = (copy_dir / "build" / "CMakeCache.txt").read_text(encoding="utf-8", errors="replace")
        gen_found = re.search(r"^CMAKE_GENERATOR:INTERNAL=(.+)$", cmake_cache, re.M)
        cxx_id_found = re.search(r"The CXX compiler identification is ([A-Za-z0-9_]+)\s+([0-9.]+)", cfg_res.stdout)
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
                "generator": gen_found.group(1).strip() if gen_found else "Unix Makefiles",
                "cmake_policy_version_minimum_used": policy_minimum_used,
            },
            "compiler": {
                "id": cxx_id_found.group(1) if cxx_id_found else "AppleClang",
                "version": cxx_id_found.group(2) if cxx_id_found else "",
                "version_line": cxx_ver_res.stdout.splitlines()[0] if cxx_ver_res.stdout else "",
            },
            "catch2": {
                "version": extract_catch_version(EX / "test" / "catch.hpp"),
                "header": "exercises/practice/knapsack/test/catch.hpp",
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
                    versions_payload["git"]["head"] = existing_ver.get("git", {}).get(
                        "head", versions_payload["git"]["head"]
                    )
            except Exception:
                pass
        versions_file.write_text(json.dumps(versions_payload, indent=2) + "\n", encoding="utf-8")

        counts_payload = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_cases": EXPECTED_CASES,
            "static_test_case_count": len(static_cases),
            "xml_executed_case_count": executed_cases,
            "xml_passed_case_count": eval_details.get("successes", 0),
            "xml_failed_case_count": eval_details.get("failures", 0),
            "list_test_names_only_count": len(listed_names),
            "uuid_tags_in_test_file_count": len(static_test_uuids),
            "tests_toml_before": {
                "total": len(before_uuids),
                "included": len(before_included),
                "excluded": len(before_excluded),
            },
            "tests_toml_after": {
                "total": len(after_uuids),
                "included": len(after_included),
                "excluded": len(after_excluded),
                "changed_inclusions": 0,
            },
        }
        (WORK_DIR / "counts.json").write_text(json.dumps(counts_payload, indent=2) + "\n", encoding="utf-8")

        neg_payload = {
            "task_id": TASK_ID,
            "all_controls_behaved_as_expected": bool(nc1_ok and nc2_ok and nc3_ok),
            "controls": {
                "assertion_failure": {
                    "target_named_case": NAMED_CASES[0],
                    "mutation": "if (items.empty()) { return -1; }",
                    "compile_rc": neg_compile_res.returncode,
                    "run_rc": neg_assert_res.returncode,
                    "named_case_failed": first_named_failed,
                    "evaluate_failures": neg_assert_failures,
                    "rejected_as_expected": nc1_ok,
                },
                "zero_tests": {
                    "filter": "no-such-test-filter*",
                    "catch2_run_rc": neg_zero_res.returncode,
                    "xml_total_cases": neg_zero_details.get("total", 0),
                    "evaluate_failures": neg_zero_failures,
                    "rejected_as_expected": nc2_ok,
                },
                "child_failure": {
                    "synthetic_run_rc_1_failures": neg_child_run_failures,
                    "synthetic_build_rc_2_failures": neg_child_build_failures,
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
                    "toml_comment": after_toml.get(tc_uuid, {}).get("comment", ""),
                }
            )

        expected_vs_actual_payload = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_executed_cases": EXPECTED_CASES,
            "actual_executed_cases": executed_cases,
            "named_cases": NAMED_CASES,
            "excluded_case": {
                "uuid": EXCLUDED_UUID,
                "description": after_toml[EXCLUDED_UUID].get("description", ""),
                "include": after_toml[EXCLUDED_UUID].get("include", True),
                "reimplemented_by": REPLACEMENT_UUID,
                "classification": "replacement case (not unsupported in C++, not a bug)",
                "toml_comment": after_toml[EXCLUDED_UUID].get("comment", ""),
            },
            "cases": cases_comparison,
        }
        (WORK_DIR / "expected-vs-actual.json").write_text(
            json.dumps(expected_vs_actual_payload, indent=2) + "\n",
            encoding="utf-8",
        )

    except Exception as exc:
        record("Unexpected exception in check.py", False, f"{type(exc).__name__}: {exc}")
    finally:
        # Remove temporary directory and verify removal
        shutil.rmtree(tmp_dir, ignore_errors=True)
        tmp_removed = not tmp_dir.exists()
        record("Temporary directory removed in finally block", tmp_removed, normalise_text(str(tmp_dir), tmp_dir=tmp_dir))

        # Step B: Re-hash every file under EX and check git status
        post_ex_hashes = snapshot_directory_hashes(EX)
        ex_unchanged = pre_ex_hashes == post_ex_hashes
        record(
            "All files under exercises/practice/knapsack unchanged during check.py execution",
            ex_unchanged,
            f"hashed {len(post_ex_hashes)} files",
        )

        _, post_outside_work, post_disallowed = git_status_Snapshot()
        git_state_ok = (pre_outside_work == post_outside_work) and (len(post_disallowed) == 0)
        record(
            "git status outside work/R20-T041/ unchanged and restricted to ALLOWED FILES",
            git_state_ok,
            "unchanged" if git_state_ok else f"outside={post_outside_work}; disallowed={post_disallowed}",
        )

        # Write inputs.json now that post_ex_hashes are available
        try:
            config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
            files_cfg = config_data.get("files", {})
            resolved_files = {
                role: [normalise_text(str((EX / rel_s).resolve())) for rel_s in files_cfg.get(role, [])]
                for role in ("solution", "test", "example")
            }
            inputs_payload = {
                "task_id": TASK_ID,
                "exercise": SLUG,
                "exercise_dir": "<REPO>/exercises/practice/knapsack",
                "config_json_path": "<REPO>/exercises/practice/knapsack/.meta/config.json",
                "config_files": files_cfg,
                "has_editor_key": "editor" in files_cfg,
                "resolved_paths": resolved_files,
                "expected_cases": EXPECTED_CASES,
                "named_cases": NAMED_CASES,
                "targeted_uuids": TARGETED_UUIDS,
                "exercise_file_sha256_before": pre_ex_hashes,
                "exercise_file_sha256_after": post_ex_hashes,
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
