#!/usr/bin/env python3
"""R20-T045 automated check, instrumentation, and scaling study for exercises/practice/beer-song."""

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


TASK_ID = "R20-T045"
SLUG = "beer-song"
EXPECTED_CASES = 5
NAMED_CASES = [
    "prints_an_arbitrary_verse",
    "handles_1_bottle",
    "handles_0_bottles",
]
ALLOWED_PREFIXES = (
    "exercises/practice/beer-song/.meta/example.cpp",
    "docs/maintenance/beer-song.md",
    "work/R20-T045/",
    "work/R20-T045",
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


def strip_cpp_comments(code):
    """Strip C/C++ comments while preserving string/char literals and normalising whitespace."""
    out = []
    i = 0
    n = len(code)
    in_str = False
    in_char = False
    in_line = False
    in_block = False
    while i < n:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < n else ""
        if in_line:
            if ch == "\n":
                in_line = False
                out.append(ch)
            i += 1
        elif in_block:
            if ch == "*" and nxt == "/":
                in_block = False
                i += 2
            else:
                i += 1
        elif in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(nxt)
                i += 2
            else:
                if ch == '"':
                    in_str = False
                i += 1
        elif in_char:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(nxt)
                i += 2
            else:
                if ch == "'":
                    in_char = False
                i += 1
        else:
            if ch == "/" and nxt == "/":
                in_line = True
                i += 2
            elif ch == "/" and nxt == "*":
                in_block = True
                i += 2
            else:
                if ch == '"':
                    in_str = True
                elif ch == "'":
                    in_char = True
                out.append(ch)
                i += 1
    return "\n".join(line.strip() for line in "".join(out).splitlines() if line.strip())


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

    return failures, {
        "successes": successes,
        "failures": fail_count,
        "total": total,
        "cases": case_list,
        "case_map": case_map,
    }


def run_instrumentation_and_benchmark(tmp_dir, example_h_text, example_cpp_text):
    """Count exact operations via instrumented copy and measure algorithm timings separately from compile/startup."""
    inst_dir = tmp_dir / "instrumented"
    inst_dir.mkdir(parents=True, exist_ok=True)
    (inst_dir / "beer_song.h").write_text(example_h_text, encoding="utf-8")

    inst_cpp = """\
#include <cassert>
#include <sstream>
#include "beer_song.h"

using namespace std;

struct OpCounters {
    long long wall_calls = 0;
    long long wall_bottles = 0;
    long long wall_top_ops = 0;
    long long wall_leaf_ops = 0;
    long long total_bottles = 0;
    long long total_leaf_ops = 0;
};
extern OpCounters g_counters;

namespace beer_song {
namespace {

struct bottles {
    bottles(unsigned num) : count(num), suffix(num > 1 ? "s" : "") {
        ++g_counters.total_bottles;
    }
    unsigned const count;
    string const suffix;
};

struct TrackedStream {
    ostringstream oss;
    TrackedStream& operator<<(unsigned v) {
        oss << v;
        ++g_counters.total_leaf_ops;
        return *this;
    }
    TrackedStream& operator<<(char c) {
        oss << c;
        ++g_counters.total_leaf_ops;
        return *this;
    }
    TrackedStream& operator<<(const char* s) {
        oss << s;
        ++g_counters.total_leaf_ops;
        return *this;
    }
    TrackedStream& operator<<(const string& s) {
        oss << s;
        ++g_counters.total_leaf_ops;
        return *this;
    }
    TrackedStream& operator<<(bottles const& b) {
        if (b.count) {
            (*this) << b.count << " bottle" << b.suffix;
        } else {
            (*this) << "no more bottles";
        }
        return (*this) << " of beer";
    }
};

void bottles_of_beer_on_the_wall(TrackedStream& stream, unsigned count) {
    ++g_counters.wall_calls;
    long long bottles_before = g_counters.total_bottles;
    long long leaf_before = g_counters.total_leaf_ops;
    if (count) {
        g_counters.wall_top_ops += 4;
        stream << bottles(count) << " on the wall, " << bottles(count) << ".\\n";
    } else {
        g_counters.wall_top_ops += 3;
        stream << "No more bottles of beer on the wall, " << bottles(count) << ".\\n";
    }
    g_counters.wall_bottles += (g_counters.total_bottles - bottles_before);
    g_counters.wall_leaf_ops += (g_counters.total_leaf_ops - leaf_before);
}

void take_one_down_and_pass_it_around(TrackedStream& stream, unsigned count) {
    if (count > 1) {
        stream << "Take one down and pass it around, " << bottles(count - 1) << " on the wall.\\n";
    } else if (count) {
        stream << "Take it down and pass it around, " << bottles(count - 1) << " on the wall.\\n";
    } else {
        stream << "Go to the store and buy some more, 99 bottles of beer on the wall.\\n";
    }
}

void verse(TrackedStream& stream, unsigned count) {
    bottles_of_beer_on_the_wall(stream, count);
    take_one_down_and_pass_it_around(stream, count);
}

}  // namespace

string verse(unsigned num) {
    TrackedStream stream;
    verse(stream, num);
    return stream.oss.str();
}

string sing(unsigned begin, unsigned end) {
    TrackedStream stream;
    for (unsigned num = begin; num > end; --num) {
        verse(stream, num);
        stream << '\\n';
    }
    verse(stream, end);
    return stream.oss.str();
}

string sing(unsigned num) { return sing(num, 0); }

}  // namespace beer_song
"""
    (inst_dir / "beer_song.cpp").write_text(inst_cpp, encoding="utf-8")

    inst_main = """\
#include <cassert>
#include <iostream>
#include "beer_song.h"

struct OpCounters {
    long long wall_calls = 0;
    long long wall_bottles = 0;
    long long wall_top_ops = 0;
    long long wall_leaf_ops = 0;
    long long total_bottles = 0;
    long long total_leaf_ops = 0;
};
OpCounters g_counters;

int main() {
    assert(beer_song::verse(8) ==
           "8 bottles of beer on the wall, 8 bottles of beer.\\n"
           "Take one down and pass it around, 7 bottles of beer on the wall.\\n");
    assert(beer_song::verse(1) ==
           "1 bottle of beer on the wall, 1 bottle of beer.\\n"
           "Take it down and pass it around, no more bottles of beer on the wall.\\n");
    assert(beer_song::verse(0) ==
           "No more bottles of beer on the wall, no more bottles of beer.\\n"
           "Go to the store and buy some more, 99 bottles of beer on the wall.\\n");

    auto report = [](const char* call_expr, unsigned verses, auto fn) {
        g_counters = OpCounters{};
        auto out = fn();
        std::cout << call_expr
                  << " verses=" << verses
                  << " chars=" << out.size()
                  << " wall_calls=" << g_counters.wall_calls
                  << " wall_bottles=" << g_counters.wall_bottles
                  << " wall_top_ops=" << g_counters.wall_top_ops
                  << " wall_leaf_ops=" << g_counters.wall_leaf_ops
                  << " total_bottles=" << g_counters.total_bottles
                  << " total_leaf_ops=" << g_counters.total_leaf_ops << "\\n";
    };

    report("verse(8)", 1, []() { return beer_song::verse(8); });
    report("sing(9,0)", 10, []() { return beer_song::sing(9, 0); });
    report("sing(99,0)", 100, []() { return beer_song::sing(99, 0); });
    return 0;
}
"""
    (inst_dir / "inst_main.cpp").write_text(inst_main, encoding="utf-8")
    inst_comp = run_cmd(
        ["c++", "-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "inst_main.cpp", "beer_song.cpp", "-o", "inst_runner"],
        cwd=inst_dir,
    )
    if inst_comp.returncode != 0:
        raise RuntimeError(f"Instrumentation compile failed: {inst_comp.stderr}")
    inst_run = run_cmd([str(inst_dir / "inst_runner")], cwd=inst_dir)
    if inst_run.returncode != 0:
        raise RuntimeError(f"Instrumentation run failed: {inst_run.stderr}")
    write_log("instrumentation.log", ["./inst_runner"], inst_run, tmp_dir)

    ops_rows = []
    for line in inst_run.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        kv = {"call": parts[0]}
        for item in parts[1:]:
            k, v = item.split("=", 1)
            kv[k] = int(v)
        ops_rows.append(kv)

    # Benchmark in separate dir using un-instrumented .meta/example.cpp
    bench_dir = tmp_dir / "benchmark"
    bench_dir.mkdir(parents=True, exist_ok=True)
    (bench_dir / "beer_song.h").write_text(example_h_text, encoding="utf-8")
    (bench_dir / "beer_song.cpp").write_text(example_cpp_text, encoding="utf-8")
    (bench_dir / "noop.cpp").write_text("int main() { return 0; }\n", encoding="utf-8")

    t0 = time.perf_counter()
    noop_comp = run_cmd(["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "noop.cpp", "-o", "noop"], cwd=bench_dir)
    noop_compile_ms = (time.perf_counter() - t0) * 1000.0
    if noop_comp.returncode != 0:
        raise RuntimeError(f"noop compile failed: {noop_comp.stderr}")

    startup_ms_samples = []
    for _ in range(9):
        ts = time.perf_counter()
        r = run_cmd([str(bench_dir / "noop")], cwd=bench_dir)
        if r.returncode != 0:
            raise RuntimeError("noop exited non-zero")
        startup_ms_samples.append((time.perf_counter() - ts) * 1000.0)

    bench_main = """\
#include <algorithm>
#include <cassert>
#include <chrono>
#include <iostream>
#include <string>
#include <vector>
#include "beer_song.h"

int main() {
    // Assert specification correctness before any timing
    assert(beer_song::verse(8) ==
           "8 bottles of beer on the wall, 8 bottles of beer.\\n"
           "Take one down and pass it around, 7 bottles of beer on the wall.\\n");
    assert(beer_song::verse(1) ==
           "1 bottle of beer on the wall, 1 bottle of beer.\\n"
           "Take it down and pass it around, no more bottles of beer on the wall.\\n");
    assert(beer_song::verse(0) ==
           "No more bottles of beer on the wall, no more bottles of beer.\\n"
           "Go to the store and buy some more, 99 bottles of beer on the wall.\\n");
    assert(beer_song::sing(8, 6) ==
           "8 bottles of beer on the wall, 8 bottles of beer.\\n"
           "Take one down and pass it around, 7 bottles of beer on the wall.\\n\\n"
           "7 bottles of beer on the wall, 7 bottles of beer.\\n"
           "Take one down and pass it around, 6 bottles of beer on the wall.\\n\\n"
           "6 bottles of beer on the wall, 6 bottles of beer.\\n"
           "Take one down and pass it around, 5 bottles of beer on the wall.\\n");

    volatile std::size_t sink = 0;
    // Warm-up
    for (int w = 0; w < 50; ++w) {
        sink += beer_song::verse(8).size();
        sink += beer_song::sing(9, 0).size();
        sink += beer_song::sing(99, 0).size();
    }

    auto measure = [&](const char* label, int verses, int batch, auto fn) {
        std::vector<double> samples_us;
        for (int rep = 0; rep < 9; ++rep) {
            auto t1 = std::chrono::steady_clock::now();
            for (int b = 0; b < batch; ++b) {
                sink += fn().size();
            }
            auto t2 = std::chrono::steady_clock::now();
            double per_call_us = std::chrono::duration<double, std::micro>(t2 - t1).count() / batch;
            samples_us.push_back(per_call_us);
        }
        std::sort(samples_us.begin(), samples_us.end());
        std::cout << label
                  << " verses=" << verses
                  << " reps=9"
                  << " batch=" << batch
                  << " median_us=" << samples_us[4]
                  << " min_us=" << samples_us.front()
                  << " max_us=" << samples_us.back() << "\\n";
    };

    measure("verse(8)", 1, 500, []() { return beer_song::verse(8); });
    measure("sing(9,0)", 10, 200, []() { return beer_song::sing(9, 0); });
    measure("sing(99,0)", 100, 50, []() { return beer_song::sing(99, 0); });
    return sink == 0 ? 1 : 0;
}
"""
    (bench_dir / "bench_main.cpp").write_text(bench_main, encoding="utf-8")
    t1 = time.perf_counter()
    bench_comp = run_cmd(
        ["c++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "bench_main.cpp", "beer_song.cpp", "-o", "bench_runner"],
        cwd=bench_dir,
    )
    bench_compile_ms = (time.perf_counter() - t1) * 1000.0
    if bench_comp.returncode != 0:
        raise RuntimeError(f"Benchmark compile failed: {bench_comp.stderr}")

    t2 = time.perf_counter()
    bench_run = run_cmd([str(bench_dir / "bench_runner")], cwd=bench_dir)
    bench_wall_ms = (time.perf_counter() - t2) * 1000.0
    if bench_run.returncode != 0:
        raise RuntimeError(f"Benchmark run failed: {bench_run.stderr}")
    if not (WORK_DIR / "benchmark.log").is_file():
        write_log("benchmark.log", ["./bench_runner"], bench_run, tmp_dir)

    timing_rows = []
    for line in bench_run.stdout.splitlines():
        parts = line.split()
        if not parts:
            continue
        kv = {"call": parts[0]}
        for item in parts[1:]:
            k, v = item.split("=", 1)
            kv[k] = float(v) if "us" in k else int(v)
        timing_rows.append(kv)

    return {
        "compiler_flags": "-std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror",
        "noop_compile_ms": round(noop_compile_ms, 2),
        "bench_compile_ms": round(bench_compile_ms, 2),
        "noop_startup_median_ms": round(statistics.median(startup_ms_samples), 2),
        "bench_total_wall_ms": round(bench_wall_ms, 2),
        "operations": ops_rows,
        "timings": timing_rows,
    }


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

    tmp_dir = Path(tempfile.mkdtemp(prefix="r20-t045-"))
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
            "exercises/practice/beer-song/beer_song.cpp",
            "exercises/practice/beer-song/beer_song.h",
            "exercises/practice/beer-song/beer_song_test.cpp",
            "exercises/practice/beer-song/.docs/instructions.md",
            "exercises/practice/beer-song/.meta/example.h",
        ]
        diff_res = run_cmd(["git", "diff", "--quiet", base_ref, "--"] + protected_rel, cwd=REPO)
        record(f"Learner stub, test file, instructions.md, and .meta/example.h equal {base_ref}", diff_res.returncode == 0, f"base={base_ref} ({base_sha[:12]})")

        # Comment-only diff check on .meta/example.cpp vs org/main
        before_res = run_cmd(["git", "show", f"{base_ref}:exercises/practice/beer-song/.meta/example.cpp"], cwd=REPO)
        if before_res.returncode != 0:
            raise RuntimeError(f"Failed to read baseline example.cpp: {before_res.stderr}")
        before_cpp = before_res.stdout
        after_cpp = (EX / ".meta" / "example.cpp").read_text(encoding="utf-8")
        example_h = (EX / ".meta" / "example.h").read_text(encoding="utf-8")
        comment_only_ok = (before_cpp != after_cpp) and (strip_cpp_comments(before_cpp) == strip_cpp_comments(after_cpp))
        record(
            "Only comments changed in exercises/practice/beer-song/.meta/example.cpp vs org/main",
            comment_only_ok,
            "strip_cpp_comments(before) == strip_cpp_comments(after)",
        )

        # Isolated copy & Catch2 test run (Steps D & E)
        copy_dir = tmp_dir / SLUG
        shutil.copytree(EX, copy_dir)
        dotfiles_ok = (copy_dir / ".meta").is_dir() and (copy_dir / ".docs").is_dir() and (copy_dir / "test" / "catch.hpp").is_file()
        record("Isolated copy preserves dotfiles (.meta, .docs) and test/catch.hpp", dotfiles_ok, "<TMP>/beer-song")

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
        record("Generated test executable located", exe_path is not None and exe_path.is_file(), "<TMP>/beer-song/build/beer-song")
        if exe_path is None:
            raise RuntimeError("Missing test executable")

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
        record(f"All {EXPECTED_CASES} cases (including 3 named cases) pass and match list count", len(eval_failures) == 0, f"executed={executed_cases}/{EXPECTED_CASES}")

        # Instrumentation & benchmark
        cost_data = run_instrumentation_and_benchmark(tmp_dir, example_h, after_cpp)
        cost_file = WORK_DIR / "cost-study.json"
        if not cost_file.is_file():
            cost_file.write_text(json.dumps(cost_data, indent=2) + "\n", encoding="utf-8")
        else:
            existing_cost = json.loads(cost_file.read_text(encoding="utf-8"))
            if existing_cost.get("operations") != cost_data.get("operations"):
                cost_file.write_text(json.dumps(cost_data, indent=2) + "\n", encoding="utf-8")
        record("Instrumented operation count and multi-repetition benchmark completed", len(cost_data["operations"]) == 3 and len(cost_data["timings"]) == 3, f"sizes={[r['verses'] for r in cost_data['operations']]}")

        # Verify docs/maintenance/beer-song.md operation counts equal instrumented counts
        doc_path = REPO / "docs" / "maintenance" / "beer-song.md"
        doc_ok = False
        doc_detail = "docs/maintenance/beer-song.md missing"
        if doc_path.is_file():
            doc_text = doc_path.read_text(encoding="utf-8")
            # Parse table rows starting with `| ` containing call name like `verse(8)`, `sing(9, 0)` / `sing(9,0)`, `sing(99, 0)`
            parsed_rows = {}
            for row_line in doc_text.splitlines():
                if not row_line.strip().startswith("|"):
                    continue
                cols = [c.strip().strip("`") for c in row_line.strip().strip("|").split("|")]
                if len(cols) >= 8 and cols[1].isdigit():
                    # cols: [call, verses, wall_calls, wall_bottles, wall_top_ops, wall_leaf_ops, total_bottles, total_leaf_ops]
                    verses_key = int(cols[1])
                    parsed_rows[verses_key] = [int(cols[i]) for i in range(1, 8)]
            expected_rows = {
                r["verses"]: [
                    r["verses"],
                    r["wall_calls"],
                    r["wall_bottles"],
                    r["wall_top_ops"],
                    r["wall_leaf_ops"],
                    r["total_bottles"],
                    r["total_leaf_ops"],
                ]
                for r in cost_data["operations"]
            }
            doc_ok = (parsed_rows == expected_rows) and ("0..99" in doc_text) and ("startup" in doc_text.lower())
            doc_detail = f"parsed_verses={sorted(parsed_rows.keys())} vs instrumented={sorted(expected_rows.keys())}"
        record("docs/maintenance/beer-song.md operation table matches instrumented C++ counts", doc_ok, doc_detail)

        # Negative Controls (Step G)
        bad_cpp = after_cpp.replace(
            "string verse(unsigned num) {",
            'string verse(unsigned num) {\n    if (num == 8) return "wrong";',
        )
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
        record("Negative control 1 (assertion failure on 'prints_an_arbitrary_verse') rejected", nc1_ok, f"run_rc={nc1_res.returncode}")

        sol_by_ext[".cpp"].write_text(after_cpp, encoding="utf-8")
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
                "header": "exercises/practice/beer-song/test/catch.hpp",
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

        test_cpp_text = (EX / "beer_song_test.cpp").read_text(encoding="utf-8")
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
            "comment_only_change_in_example_cpp": comment_only_ok,
        }
        (WORK_DIR / "counts.json").write_text(json.dumps(counts_payload, indent=2) + "\n", encoding="utf-8")

        neg_payload = {
            "task_id": TASK_ID,
            "all_controls_behaved_as_expected": bool(nc1_ok and nc2_ok and nc3_ok),
            "controls": {
                "assertion_failure": {
                    "target_named_case": NAMED_CASES[0],
                    "mutation": 'if (num == 8) return "wrong";',
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
            "note": "beer_song_test.cpp defines 5 hand-named TEST_CASE blocks (no UUID tags), while .meta/tests.toml lists 8 canonical entries.",
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
            for rel in ("beer_song.cpp", "beer_song.h", "beer_song_test.cpp", ".docs/instructions.md", ".meta/example.h")
        )
        record("Learner stub, test file, instructions.md, and .meta/example.h unchanged", learner_unchanged, f"hashed {len(post_ex_hashes)} files")

        _, post_outside_work, post_disallowed = git_status_snapshot()
        git_state_ok = (pre_outside_work == post_outside_work) and (len(post_disallowed) == 0)
        record("git status outside work/R20-T045/ unchanged and restricted to ALLOWED FILES", git_state_ok, "unchanged" if git_state_ok else f"disallowed={post_disallowed}")

        try:
            config_data = json.loads((EX / ".meta" / "config.json").read_text(encoding="utf-8"))
            files_cfg = config_data.get("files", {})
            inputs_payload = {
                "task_id": TASK_ID,
                "exercise": SLUG,
                "exercise_dir": "<REPO>/exercises/practice/beer-song",
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
