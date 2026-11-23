#!/usr/bin/env python3
"""R20-T043 automated check and mutation verification for exercises/practice/dnd-character."""

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


TASK_ID = "R20-T043"
SLUG = "dnd-character"
EXPECTED_CASES = 18
NAMED_CASES = [
    "ability modifier for score 3 is -4",
    "ability modifier for score 4 is -3",
    "ability modifier for score 5 is -3",
]
EXPECTED_MUTANT_FAILURES = [
    "ability modifier for score 3 is -4",
    "ability modifier for score 5 is -3",
    "ability modifier for score 7 is -2",
    "ability modifier for score 9 is -1",
]
ALLOWED_PREFIXES = (
    "exercises/practice/dnd-character/.docs/hints.md",
    "docs/maintenance/dnd-character.md",
    "work/R20-T043/",
    "work/R20-T043",
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


def find_executable(copy_dir):
    for c in (
        copy_dir / "build" / SLUG,
        copy_dir / "build" / "Debug" / SLUG,
        copy_dir / "build" / f"{SLUG}.exe",
        copy_dir / "build" / "Debug" / f"{SLUG}.exe",
    ):
        if c.is_file():
            return c
    return None


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
        passed = (overall.attrib.get("success", "false") == "true") if overall is not None else False
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


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    failures = []

    def record(label, ok, detail=""):
        status = "PASS" if ok else "FAIL"
        print(f"{status}: {label}" + (f" ({detail})" if detail else ""))
        if not ok:
            failures.append(f"{label}: {detail}" if detail else label)

    pre_ex_hashes = snapshot_directory_hashes(EX)
    _, pre_outside_work, pre_disallowed = git_status_snapshot()
    record(
        "Working tree contains no changes outside ALLOWED FILES before check",
        len(pre_disallowed) == 0,
        "clean" if not pre_disallowed else "; ".join(pre_disallowed),
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t043-"))
    executed_cases = 0

    try:
        # Step A: Config paths
        config_path = EX / ".meta" / "config.json"
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        files_cfg = config_data.get("files", {})
        record("No 'editor' key in .meta/config.json files", "editor" not in files_cfg, "editor key absent")

        ex_resolved = EX.resolve()
        all_inside_ex = True
        for role in ("solution", "test", "example"):
            for rel_str in files_cfg.get(role, []):
                p = (EX / rel_str).resolve()
                try:
                    p.relative_to(ex_resolved)
                except ValueError:
                    all_inside_ex = False
                if not p.is_file():
                    all_inside_ex = False
        record(
            "All solution/test/example files exist and stay inside exercise directory",
            all_inside_ex and all(bool(files_cfg.get(r)) for r in ("solution", "test", "example")),
            json.dumps(files_cfg),
        )

        # Step C: Stub unsolved
        base_ref, base_sha, used_fallback_ref = resolve_base_ref()
        protected_rel = [
            "exercises/practice/dnd-character/dnd_character.cpp",
            "exercises/practice/dnd-character/dnd_character.h",
            "exercises/practice/dnd-character/dnd_character_test.cpp",
            "exercises/practice/dnd-character/.docs/instructions.md",
        ]
        diff_res = run_cmd(["git", "diff", "--quiet", base_ref, "--"] + protected_rel, cwd=REPO)
        record(
            f"Learner stub, test file, and instructions.md equal {base_ref}",
            diff_res.returncode == 0,
            f"base={base_ref} ({base_sha[:12]})",
        )

        # Validate mutant.cpp differs from .meta/example.cpp by more than whitespace
        orig_example_cpp = (EX / ".meta" / "example.cpp").read_text(encoding="utf-8")
        mutant_path = WORK_DIR / "mutant.cpp"
        mutant_cpp = mutant_path.read_text(encoding="utf-8")
        non_ws_diff = re.sub(r"\s+", "", orig_example_cpp) != re.sub(r"\s+", "", mutant_cpp)
        record(
            "work/R20-T043/mutant.cpp differs from .meta/example.cpp by more than whitespace",
            non_ws_diff and "(score - 10) / 2" in mutant_cpp,
            "substitutes '(score - 10) / 2' for std::floor expression",
        )

        # Check hints.md and maintenance doc exist with expected required sections
        hints_path = EX / ".docs" / "hints.md"
        hints_ok = hints_path.is_file()
        if hints_ok:
            ht = hints_path.read_text(encoding="utf-8")
            for required in ("# Hints", "## General", "truncates toward zero", "score = 3", "-4"):
                if required not in ht:
                    hints_ok = False
        record("exercises/practice/dnd-character/.docs/hints.md documents floor contract and diagnostic score 3", hints_ok, "hints.md")

        maint_path = REPO / "docs" / "maintenance" / "dnd-character.md"
        maint_ok = maint_path.is_file()
        if maint_ok:
            mt = maint_path.read_text(encoding="utf-8")
            for required in ("1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37", "ability modifier for score 3 is -4", "work/R20-T043/mutant.cpp"):
                if required not in mt:
                    maint_ok = False
        record("docs/maintenance/dnd-character.md records mutant, rejecting test ID, and 3..18 outputs", maint_ok, "dnd-character.md")

        # Step D & E (Original reference in copy_orig)
        copy_orig = tmp_dir / "orig" / SLUG
        shutil.copytree(EX, copy_orig)
        dotfiles_ok = (
            (copy_orig / ".meta").is_dir()
            and (copy_orig / ".docs").is_dir()
            and (copy_orig / "test" / "catch.hpp").is_file()
        )
        record("Isolated copy preserves dotfiles (.meta, .docs) and test/catch.hpp", dotfiles_ok, "<TMP>/orig/dnd-character")

        sol_by_ext = {(copy_orig / rel_s).suffix: (copy_orig / rel_s) for rel_s in files_cfg["solution"]}
        ex_by_ext = {(copy_orig / rel_e).suffix: (copy_orig / rel_e) for rel_e in files_cfg["example"]}
        ext_matched = set(sol_by_ext.keys()) == set(ex_by_ext.keys()) and len(sol_by_ext) > 0
        for ext, src_p in ex_by_ext.items():
            shutil.copy2(src_p, sol_by_ext[ext])
        record(
            "Reference substituted into temp copy by matching file extension",
            ext_matched,
            ", ".join(f".meta/example{ext} -> {sol_by_ext[ext].name}" for ext in sorted(sol_by_ext)),
        )

        cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        cfg_res = run_cmd(cfg_cmd, cwd=copy_orig)
        policy_minimum_used = None
        if cfg_res.returncode != 0:
            policy_minimum_used = "3.5"
            cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON", "-DCMAKE_POLICY_VERSION_MINIMUM=3.5"]
            cfg_res = run_cmd(cfg_cmd, cwd=copy_orig)
        write_log("cmake-configure.log", cfg_cmd, cfg_res, tmp_dir)
        record("CMake configure exited 0 (original)", cfg_res.returncode == 0, f"rc={cfg_res.returncode}")

        bld_cmd = ["cmake", "--build", "build"]
        bld_res = run_cmd(bld_cmd, cwd=copy_orig)
        write_log("cmake-build.log", bld_cmd, bld_res, tmp_dir)
        record("CMake build (including custom test target) exited 0 (original)", bld_res.returncode == 0, f"rc={bld_res.returncode}")

        tgt_cmd = ["cmake", "--build", "build", "--target", SLUG]
        tgt_res = run_cmd(tgt_cmd, cwd=copy_orig)
        write_log("cmake-build-target.log", tgt_cmd, tgt_res, tmp_dir)
        record(f"CMake compile-only target '{SLUG}' exited 0 (original)", tgt_res.returncode == 0, f"rc={tgt_res.returncode}")

        exe_orig = find_executable(copy_orig)
        record("Generated test executable located (original)", exe_orig is not None and exe_orig.is_file(), "<TMP>/orig/dnd-character/build/dnd-character")
        if exe_orig is None:
            raise RuntimeError("Original test executable missing")

        tmp_xml = tmp_dir / "results.xml"
        run_xml_cmd = [str(exe_orig), "-r", "xml", "-o", str(tmp_xml)]
        run_xml_res = run_cmd(run_xml_cmd, cwd=copy_orig)
        write_log("test-run.log", run_xml_cmd, run_xml_res, tmp_dir)
        raw_xml = tmp_xml.read_text(encoding="utf-8") if tmp_xml.is_file() else ""
        norm_xml = clean_eof_and_trailing_ws(normalise_xml(raw_xml, tmp_dir=tmp_dir))
        (WORK_DIR / "results.xml").write_text(norm_xml, encoding="utf-8")

        list_cmd = [str(exe_orig), "--list-test-names-only"]
        list_res = run_cmd(list_cmd, cwd=copy_orig)
        write_log("test-list.log", list_cmd, list_res, tmp_dir)
        listed_names = [line.strip() for line in list_res.stdout.splitlines() if line.strip()]

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
            f"Original passes all {EXPECTED_CASES} cases (including 3 named cases) and matches list count",
            len(eval_failures) == 0,
            f"executed={executed_cases}/{EXPECTED_CASES}" if not eval_failures else "; ".join(eval_failures),
        )

        # Build and run MUTANT in a separate isolated copy (copy_mut)
        copy_mut = tmp_dir / "mutant" / SLUG
        shutil.copytree(EX, copy_mut)
        mut_sol_by_ext = {(copy_mut / rel_s).suffix: (copy_mut / rel_s) for rel_s in files_cfg["solution"]}
        mut_ex_by_ext = {(copy_mut / rel_e).suffix: (copy_mut / rel_e) for rel_e in files_cfg["example"]}
        shutil.copy2(mut_ex_by_ext[".h"], mut_sol_by_ext[".h"])
        shutil.copy2(mutant_path, mut_sol_by_ext[".cpp"])

        mut_cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        if policy_minimum_used:
            mut_cfg_cmd.append(f"-DCMAKE_POLICY_VERSION_MINIMUM={policy_minimum_used}")
        mut_cfg_res = run_cmd(mut_cfg_cmd, cwd=copy_mut)
        mut_tgt_res = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_mut)
        exe_mut = find_executable(copy_mut)
        if mut_cfg_res.returncode != 0 or mut_tgt_res.returncode != 0 or exe_mut is None:
            raise RuntimeError(f"Mutant failed to compile: cfg={mut_cfg_res.returncode}, bld={mut_tgt_res.returncode}")

        mut_xml_path = tmp_dir / "mutant-results.xml"
        mut_run_cmd = [str(exe_mut), "-r", "xml", "-o", str(mut_xml_path)]
        mut_run_res = run_cmd(mut_run_cmd, cwd=copy_mut)
        write_log("mutant-run.log", mut_run_cmd, mut_run_res, tmp_dir)
        mut_xml = clean_eof_and_trailing_ws(normalise_xml(mut_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir))
        (WORK_DIR / "mutant-results.xml").write_text(mut_xml, encoding="utf-8")

        mut_eval_failures, mut_eval_details = evaluate(
            build_rc=0,
            run_rc=mut_run_res.returncode,
            xml_content=mut_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        mut_failed_names = sorted(name for name, info in mut_eval_details.get("case_map", {}).items() if not info["passed"])
        mutant_rejects_correctly = (
            mut_run_res.returncode != 0
            and mut_eval_details.get("failures", 0) == 4
            and mut_failed_names == sorted(EXPECTED_MUTANT_FAILURES)
            and not mut_eval_details.get("case_map", {}).get(NAMED_CASES[0], {}).get("passed", True)
            and mut_eval_details.get("case_map", {}).get(NAMED_CASES[1], {}).get("passed", False)
            and not mut_eval_details.get("case_map", {}).get(NAMED_CASES[2], {}).get("passed", True)
        )
        record(
            "Mutant in separate temp copy fails expected 4 cases including named 'ability modifier for score 3 is -4'",
            mutant_rejects_correctly,
            f"mut_rc={mut_run_res.returncode}, failed={mut_failed_names}",
        )

        # Direct scratch C++ comparison across domain 3..18
        harness_dir = tmp_dir / "domain_probe"
        harness_dir.mkdir(parents=True, exist_ok=True)
        (harness_dir / "probe.cpp").write_text(
            '#include <cmath>\n#include <iostream>\n'
            'int orig_mod(int score) { return std::floor((static_cast<double>(score) - 10) / 2); }\n'
            'int mut_mod(int score) { return (score - 10) / 2; }\n'
            'int main() {\n'
            '  for (int s = 3; s <= 18; ++s) {\n'
            '    std::cout << s << " " << orig_mod(s) << " " << mut_mod(s) << "\\n";\n'
            '  }\n'
            '  return 0;\n'
            '}\n',
            encoding="utf-8",
        )
        probe_comp = run_cmd(["c++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "probe.cpp", "-o", "probe"], cwd=harness_dir)
        probe_run = run_cmd([str(harness_dir / "probe")], cwd=harness_dir)
        domain_rows = []
        discrepant_scores = []
        for line in probe_run.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3:
                sc, orig_v, mut_v = int(parts[0]), int(parts[1]), int(parts[2])
                domain_rows.append({"score": sc, "original": orig_v, "mutant": mut_v, "matches": orig_v == mut_v})
                if orig_v != mut_v:
                    discrepant_scores.append(sc)
        domain_ok = probe_comp.returncode == 0 and probe_run.returncode == 0 and discrepant_scores == [3, 5, 7, 9]
        record(
            "Domain 3..18 probe confirms smallest rejecting input is score 3 (discrepancies at [3, 5, 7, 9])",
            domain_ok,
            f"discrepant_scores={discrepant_scores}",
        )

        # Negative Controls (Step G)
        # 1. Assertion failure (reuse copy_orig by writing mutant.cpp into copy_orig with bumped mtime)
        sol_by_ext[".cpp"].write_text(mutant_cpp, encoding="utf-8")
        for obj_p in (copy_orig / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_orig.exists():
            exe_orig.unlink()
        nc1_bld = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_orig)
        nc1_xml_path = tmp_dir / "neg_assert.xml"
        nc1_cmd = [str(exe_orig), "-r", "xml", "-o", str(nc1_xml_path)]
        nc1_res = run_cmd(nc1_cmd, cwd=copy_orig)
        write_log("negative-assertion.log", nc1_cmd, nc1_res, tmp_dir)
        nc1_xml = normalise_xml(nc1_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir) if nc1_xml_path.is_file() else ""
        nc1_failures, nc1_details = evaluate(nc1_bld.returncode, nc1_res.returncode, nc1_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc1_ok = (
            nc1_bld.returncode == 0
            and nc1_res.returncode != 0
            and len(nc1_failures) > 0
            and not nc1_details.get("case_map", {}).get(NAMED_CASES[0], {}).get("passed", True)
        )
        record(
            "Negative control 1 (mutant assertion failure on 'ability modifier for score 3 is -4') rejected",
            nc1_ok,
            f"run_rc={nc1_res.returncode}, failures={nc1_failures}",
        )

        # Restore working reference in copy_orig
        sol_by_ext[".cpp"].write_text(orig_example_cpp, encoding="utf-8")
        for obj_p in (copy_orig / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_orig.exists():
            exe_orig.unlink()
        restore_res = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_orig)
        if restore_res.returncode != 0:
            raise RuntimeError("Failed to restore original reference in copy_orig")

        # 2. Zero tests
        nc2_xml_path = tmp_dir / "neg_zero.xml"
        nc2_cmd = [str(exe_orig), "no-such-test-filter*", "-r", "xml", "-o", str(nc2_xml_path)]
        nc2_res = run_cmd(nc2_cmd, cwd=copy_orig)
        write_log("negative-zero-tests.log", nc2_cmd, nc2_res, tmp_dir)
        nc2_xml = normalise_xml(nc2_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir) if nc2_xml_path.is_file() else ""
        nc2_failures, nc2_details = evaluate(0, nc2_res.returncode, nc2_xml, EXPECTED_CASES, NAMED_CASES)
        nc2_ok = nc2_res.returncode == 0 and any("ZERO-TEST GUARD" in f for f in nc2_failures)
        record(
            "Negative control 2 (unmatched filter -> 0 tests, Catch2 rc=0) rejected by ZERO-TEST GUARD",
            nc2_ok,
            f"catch2_rc={nc2_res.returncode}, failures={nc2_failures}",
        )

        # 3. Child failure
        nc3_run_f, _ = evaluate(0, 1, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_bld_f, _ = evaluate(2, 0, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_ok = any("run_rc=1" in f for f in nc3_run_f) and any("build_rc=2" in f for f in nc3_bld_f)
        record("Negative control 3 (non-zero child return code with passing XML) rejected by evaluate()", nc3_ok, f"run={nc3_run_f}; bld={nc3_bld_f}")

        # Evidence JSON files
        cmake_cache = (copy_orig / "build" / "CMakeCache.txt").read_text(encoding="utf-8", errors="replace")
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
                "header": "exercises/practice/dnd-character/test/catch.hpp",
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

        test_cpp_text = (EX / "dnd_character_test.cpp").read_text(encoding="utf-8")
        static_cases = re.findall(r'TEST_CASE\(\s*"([^"]+)"\s*,\s*"\[([0-9a-f\-]{36})\]"\s*\)', test_cpp_text)
        toml_data = parse_tests_toml((EX / ".meta" / "tests.toml").read_text(encoding="utf-8"))
        included_uuids = [u for u, kv in toml_data.items() if kv.get("include", True) is True]
        excluded_uuids = [u for u, kv in toml_data.items() if kv.get("include", True) is False]

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
            "tests_toml_included": len(included_uuids),
            "tests_toml_excluded": len(excluded_uuids),
            "mutant_passed_case_count": mut_eval_details.get("successes", 0),
            "mutant_failed_case_count": mut_eval_details.get("failures", 0),
            "mutant_failed_case_names": mut_failed_names,
            "smallest_rejecting_score": min(discrepant_scores) if discrepant_scores else None,
        }
        (WORK_DIR / "counts.json").write_text(json.dumps(counts_payload, indent=2) + "\n", encoding="utf-8")

        neg_payload = {
            "task_id": TASK_ID,
            "all_controls_behaved_as_expected": bool(nc1_ok and nc2_ok and nc3_ok),
            "controls": {
                "assertion_failure": {
                    "target_named_case": NAMED_CASES[0],
                    "mutant_file": "work/R20-T043/mutant.cpp",
                    "compile_rc": nc1_bld.returncode,
                    "run_rc": nc1_res.returncode,
                    "named_case_failed": not nc1_details.get("case_map", {}).get(NAMED_CASES[0], {}).get("passed", True),
                    "evaluate_failures": nc1_failures,
                    "rejected_as_expected": nc1_ok,
                },
                "zero_tests": {
                    "filter": "no-such-test-filter*",
                    "catch2_run_rc": nc2_res.returncode,
                    "xml_total_cases": nc2_details.get("total", 0),
                    "evaluate_failures": nc2_failures,
                    "rejected_as_expected": nc2_ok,
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
            mut_case = mut_eval_details.get("case_map", {}).get(tc_name, {})
            cases_comparison.append(
                {
                    "index": idx,
                    "uuid": tc_uuid,
                    "name": tc_name,
                    "is_named_case": tc_name in NAMED_CASES,
                    "expected_original_pass": True,
                    "actual_original_pass": bool(xml_case.get("passed", False)),
                    "mutant_pass": bool(mut_case.get("passed", False)),
                    "test_file_line": xml_case.get("line", ""),
                }
            )
        expected_vs_actual = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_executed_cases": EXPECTED_CASES,
            "actual_executed_cases": executed_cases,
            "named_cases": NAMED_CASES,
            "smallest_rejecting_input": {"score": 3, "expected": -4, "mutant": -3, "uuid": "1e9ae1dc-35bd-43ba-aa08-e4b94c20fa37"},
            "domain_3_to_18_comparison": domain_rows,
            "cases": cases_comparison,
        }
        (WORK_DIR / "expected-vs-actual.json").write_text(json.dumps(expected_vs_actual, indent=2) + "\n", encoding="utf-8")

    except Exception as exc:
        record("Unexpected exception in check.py", False, f"{type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        record("Temporary directory removed in finally block", not tmp_dir.exists(), "<TMP>")

        post_ex_hashes = snapshot_directory_hashes(EX)
        # Note: hints.md is an allowed addition in EX/.docs/hints.md, so all files present before check must retain identical hashes
        pre_files_unchanged = all(post_ex_hashes.get(k) == v for k, v in pre_ex_hashes.items()) and set(pre_ex_hashes.keys()) == set(post_ex_hashes.keys())
        record("All files under exercises/practice/dnd-character unchanged during check.py execution", pre_files_unchanged, f"hashed {len(post_ex_hashes)} files")

        _, post_outside_work, post_disallowed = git_status_snapshot()
        git_state_ok = (pre_outside_work == post_outside_work) and (len(post_disallowed) == 0)
        record("git status outside work/R20-T043/ unchanged and restricted to ALLOWED FILES", git_state_ok, "unchanged" if git_state_ok else f"disallowed={post_disallowed}")

        try:
            config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
            files_cfg = config_data.get("files", {})
            inputs_payload = {
                "task_id": TASK_ID,
                "exercise": SLUG,
                "exercise_dir": "<REPO>/exercises/practice/dnd-character",
                "config_files": files_cfg,
                "has_editor_key": "editor" in files_cfg,
                "resolved_paths": {
                    role: [normalise_text(str((EX / r).resolve())) for r in files_cfg.get(role, [])]
                    for role in ("solution", "test", "example")
                },
                "expected_cases": EXPECTED_CASES,
                "named_cases": NAMED_CASES,
                "mutant_file": "work/R20-T043/mutant.cpp",
                "exercise_file_sha256_before": pre_ex_hashes,
                "exercise_file_sha256_after": post_ex_hashes,
                "exercise_files_unchanged_during_run": pre_files_unchanged,
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
