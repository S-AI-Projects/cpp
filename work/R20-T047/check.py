#!/usr/bin/env python3
"""R20-T047 automated check for exercises/practice/trinary and hints.md micro-example."""

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
import xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


TASK_ID = "R20-T047"
SLUG = "trinary"
EXPECTED_CASES = 9
NAMED_CASES = [
    "_1_yields_decimal_1",
    "_2_yields_decimal_2",
    "_10_yields_decimal_3",
]
ALLOWED_PREFIXES = (
    "exercises/practice/trinary/.docs/hints.md",
    "work/R20-T047/",
    "work/R20-T047",
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


def verify_hints_micro_example(tmp_dir, hints_path):
    """Extract ```cpp micro-example and ```text output from hints.md, compile under -Werror, and verify stdout."""
    text = hints_path.read_text(encoding="utf-8")
    cpp_blocks = re.findall(r"```cpp\n(.*?)\n```", text, flags=re.S)
    text_blocks = re.findall(r"```text\n(.*?)\n```", text, flags=re.S)

    # Pick the executable micro-example (contains int main())
    main_blocks = [b for b in cpp_blocks if "int main(" in b]
    if len(main_blocks) != 1 or len(text_blocks) != 1:
        return False, f"Expected 1 executable cpp block and 1 text block in hints.md, found {len(main_blocks)}/{len(text_blocks)}", {}

    cpp_code = main_blocks[0] + "\n"
    expected_out = text_blocks[0].strip() + "\n"

    micro_dir = tmp_dir / "micro_example"
    micro_dir.mkdir(parents=True, exist_ok=True)
    (micro_dir / "micro.cpp").write_text(cpp_code, encoding="utf-8")
    comp_cmd = ["c++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "micro.cpp", "-o", "micro"]
    comp_res = run_cmd(comp_cmd, cwd=micro_dir)
    if comp_res.returncode != 0:
        return False, f"Micro-example compile failed: {comp_res.stderr}", {}
    run_res = run_cmd([str(micro_dir / "micro")], cwd=micro_dir)
    write_log("micro-example.log", [str(micro_dir / "micro")], run_res, tmp_dir)
    actual_out = run_res.stdout.strip() + "\n"
    ok = (
        run_res.returncode == 0
        and actual_out == expected_out
        and "numeric=1" in actual_out
        and "pitfall_without_minus_zero=49" in actual_out
        and "zero_copy_same_addr=1" in actual_out
        and "cppreference.com" in text
    )
    info = {
        "expected_output": expected_out.strip().splitlines(),
        "actual_output": actual_out.strip().splitlines(),
        "stdout_matches_published_text": actual_out == expected_out,
    }
    return ok, "stdout matches published ```text block exactly under -Werror" if ok else f"actual={actual_out!r} vs expected={expected_out!r}", info


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
    record("Working tree contains no changes outside ALLOWED FILES before check", len(pre_disallowed) == 0, "clean" if not pre_disallowed else "; ".join(pre_disallowed))

    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t047-"))
    executed_cases = 0

    try:
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
        record("All solution/test/example files exist and stay inside exercise directory", all_inside_ex, json.dumps(files_cfg))

        base_ref, base_sha, used_fallback_ref = resolve_base_ref()
        protected_rel = [
            "exercises/practice/trinary/trinary.cpp",
            "exercises/practice/trinary/trinary.h",
            "exercises/practice/trinary/trinary_test.cpp",
            "exercises/practice/trinary/.docs/instructions.md",
        ]
        diff_res = run_cmd(["git", "diff", "--quiet", base_ref, "--"] + protected_rel, cwd=REPO)
        record(f"Learner stub, test file, and instructions.md equal {base_ref}", diff_res.returncode == 0, f"base={base_ref} ({base_sha[:12]})")

        # Verify hints.md micro-example compiles and matches published output
        hints_path = EX / ".docs" / "hints.md"
        micro_ok, micro_detail, micro_info = verify_hints_micro_example(tmp_dir, hints_path)
        record("hints.md executable ```cpp micro-example and pitfall match ```text output", micro_ok, micro_detail)

        # Isolated copy & Catch2 run
        copy_dir = tmp_dir / SLUG
        shutil.copytree(EX, copy_dir)
        dotfiles_ok = (copy_dir / ".meta").is_dir() and (copy_dir / ".docs").is_dir() and (copy_dir / "test" / "catch.hpp").is_file()
        record("Isolated copy preserves dotfiles (.meta, .docs) and test/catch.hpp", dotfiles_ok, "<TMP>/trinary")

        sol_by_ext = {(copy_dir / r).suffix: (copy_dir / r) for r in files_cfg["solution"]}
        ex_by_ext = {(copy_dir / r).suffix: (copy_dir / r) for r in files_cfg["example"]}
        ext_matched = set(sol_by_ext.keys()) == set(ex_by_ext.keys()) and len(sol_by_ext) > 0
        for ext, src_p in ex_by_ext.items():
            shutil.copy2(src_p, sol_by_ext[ext])
        record("Reference substituted into temp copy by matching file extension", ext_matched, ", ".join(f".meta/example{ext} -> {sol_by_ext[ext].name}" for ext in sorted(sol_by_ext)))

        cfg_cmd = ["cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"]
        cfg_res = run_cmd(cfg_cmd, cwd=copy_dir)
        policy_minimum_used = None
        if cfg_res.returncode != 0:
            policy_minimum_used = "3.5"
            cfg_cmd.append("-DCMAKE_POLICY_VERSION_MINIMUM=3.5")
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
        record("Generated test executable located", exe_path is not None and exe_path.is_file(), "<TMP>/trinary/build/trinary")
        if exe_path is None:
            raise RuntimeError("Missing trinary executable")

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

        eval_failures, eval_details = evaluate(
            build_rc=bld_res.returncode,
            run_rc=run_xml_res.returncode,
            xml_content=norm_xml,
            expected_cases=EXPECTED_CASES,
            named_cases=NAMED_CASES,
            list_count=len(listed_names),
        )
        executed_cases = eval_details.get("total", 0)
        record(f"All {EXPECTED_CASES} cases (including 3 named cases) pass and equal list count", len(eval_failures) == 0, f"executed={executed_cases}/{EXPECTED_CASES}")

        # Negative Controls (Step G)
        orig_cpp = (EX / ".meta" / "example.cpp").read_text(encoding="utf-8")
        bad_cpp = orig_cpp.replace("result += digit - '0';", "result += digit;")
        sol_by_ext[".cpp"].write_text(bad_cpp, encoding="utf-8")
        for obj_p in (copy_dir / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_path.exists():
            exe_path.unlink()
        nc1_bld = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_dir)
        nc1_xml_path = tmp_dir / "neg_assert.xml"
        nc1_cmd = [str(exe_path), "-r", "xml", "-o", str(nc1_xml_path)]
        nc1_res = run_cmd(nc1_cmd, cwd=copy_dir)
        write_log("negative-assertion.log", nc1_cmd, nc1_res, tmp_dir)
        nc1_xml = normalise_xml(nc1_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir) if nc1_xml_path.is_file() else ""
        nc1_failures, nc1_details = evaluate(nc1_bld.returncode, nc1_res.returncode, nc1_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc1_ok = (
            nc1_bld.returncode == 0
            and nc1_res.returncode != 0
            and len(nc1_failures) > 0
            and not nc1_details.get("case_map", {}).get(NAMED_CASES[0], {}).get("passed", True)
        )
        record("Negative control 1 (forgetting - '0' fails '_1_yields_decimal_1') rejected", nc1_ok, f"run_rc={nc1_res.returncode}")

        sol_by_ext[".cpp"].write_text(orig_cpp, encoding="utf-8")
        for obj_p in (copy_dir / "build").rglob(f"{sol_by_ext['.cpp'].name}.o"):
            obj_p.unlink()
        if exe_path.exists():
            exe_path.unlink()
        restore_res = run_cmd(["cmake", "--build", "build", "--target", SLUG], cwd=copy_dir)
        if restore_res.returncode != 0:
            raise RuntimeError("Failed to restore working reference")

        nc2_xml_path = tmp_dir / "neg_zero.xml"
        nc2_cmd = [str(exe_path), "no-such-test-filter*", "-r", "xml", "-o", str(nc2_xml_path)]
        nc2_res = run_cmd(nc2_cmd, cwd=copy_dir)
        write_log("negative-zero-tests.log", nc2_cmd, nc2_res, tmp_dir)
        nc2_xml = normalise_xml(nc2_xml_path.read_text(encoding="utf-8"), tmp_dir=tmp_dir) if nc2_xml_path.is_file() else ""
        nc2_failures, nc2_details = evaluate(0, nc2_res.returncode, nc2_xml, EXPECTED_CASES, NAMED_CASES)
        nc2_ok = nc2_res.returncode == 0 and any("ZERO-TEST GUARD" in f for f in nc2_failures)
        record("Negative control 2 (unmatched filter -> 0 tests, Catch2 rc=0) rejected by ZERO-TEST GUARD", nc2_ok, f"catch2_rc={nc2_res.returncode}")

        nc3_run_f, _ = evaluate(0, 1, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_bld_f, _ = evaluate(2, 0, norm_xml, EXPECTED_CASES, NAMED_CASES, len(listed_names))
        nc3_ok = any("run_rc=1" in f for f in nc3_run_f) and any("build_rc=2" in f for f in nc3_bld_f)
        record("Negative control 3 (non-zero child return code with passing XML) rejected by evaluate()", nc3_ok, f"run={nc3_run_f}; bld={nc3_bld_f}")

        # Versions, counts, negative controls, expected-vs-actual JSONs
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
                "header": "exercises/practice/trinary/test/catch.hpp",
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

        test_cpp_text = (EX / "trinary_test.cpp").read_text(encoding="utf-8")
        static_names = re.findall(r'TEST_CASE\(\s*"([^"]+)"\s*\)', test_cpp_text)
        toml_data = parse_tests_toml((EX / ".meta" / "tests.toml").read_text(encoding="utf-8"))

        counts_payload = {
            "task_id": TASK_ID,
            "exercise": SLUG,
            "expected_cases": EXPECTED_CASES,
            "static_test_case_count": len(static_names),
            "xml_executed_case_count": executed_cases,
            "xml_passed_case_count": eval_details.get("successes", 0),
            "xml_failed_case_count": eval_details.get("failures", 0),
            "list_test_names_only_count": len(listed_names),
            "tests_toml_total": len(toml_data),
            "tests_toml_included": len([u for u, kv in toml_data.items() if kv.get("include", True) is True]),
            "tests_toml_excluded": len([u for u, kv in toml_data.items() if kv.get("include", True) is False]),
            "micro_example": micro_info,
        }
        (WORK_DIR / "counts.json").write_text(json.dumps(counts_payload, indent=2) + "\n", encoding="utf-8")

        neg_payload = {
            "task_id": TASK_ID,
            "all_controls_behaved_as_expected": bool(nc1_ok and nc2_ok and nc3_ok),
            "controls": {
                "assertion_failure": {
                    "target_named_case": NAMED_CASES[0],
                    "mutation": "result += digit; (omits - '0')",
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
        for idx, tc_name in enumerate(listed_names, start=1):
            xml_case = eval_details.get("case_map", {}).get(tc_name, {})
            cases_comparison.append(
                {
                    "index": idx,
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
            "note": "trinary_test.cpp has 9 hand-named TEST_CASE blocks while tests.toml has 11 entries.",
            "micro_example": micro_info,
            "cases": cases_comparison,
        }
        (WORK_DIR / "expected-vs-actual.json").write_text(json.dumps(expected_vs_actual, indent=2) + "\n", encoding="utf-8")

    except Exception as exc:
        record("Unexpected exception in check.py", False, f"{type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        record("Temporary directory removed in finally block", not tmp_dir.exists(), "<TMP>")

        post_ex_hashes = snapshot_directory_hashes(EX)
        learner_unchanged = all(
            post_ex_hashes.get(rel) == pre_ex_hashes.get(rel)
            for rel in ("trinary.cpp", "trinary.h", "trinary_test.cpp", ".docs/instructions.md", ".meta/example.cpp", ".meta/example.h")
        )
        record("Learner stub, test file, instructions.md, and .meta/example.* unchanged", learner_unchanged, f"hashed {len(post_ex_hashes)} files")

        _, post_outside_work, post_disallowed = git_status_snapshot()
        git_state_ok = (pre_outside_work == post_outside_work) and (len(post_disallowed) == 0)
        record("git status outside work/R20-T047/ unchanged and restricted to ALLOWED FILES", git_state_ok, "unchanged" if git_state_ok else f"disallowed={post_disallowed}")

        try:
            config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
            files_cfg = config_data.get("files", {})
            inputs_payload = {
                "task_id": TASK_ID,
                "exercise": SLUG,
                "exercise_dir": "<REPO>/exercises/practice/trinary",
                "config_files": files_cfg,
                "has_editor_key": "editor" in files_cfg,
                "resolved_paths": {
                    role: [normalise_text(str((EX / r).resolve())) for r in files_cfg.get(role, [])]
                    for role in ("solution", "test", "example")
                },
                "expected_cases": EXPECTED_CASES,
                "named_cases": NAMED_CASES,
                "exercise_file_sha256_before": pre_ex_hashes,
                "exercise_file_sha256_after": post_ex_hashes,
                "protected_files_unchanged_during_run": learner_unchanged,
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
