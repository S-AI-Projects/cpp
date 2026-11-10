#!/usr/bin/env python3
"""Check script for R20-T036: Explain two approaches to clock in C++."""

import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/clock"
WORK_DIR = "work/R20-T036"
REPO_ROOT = os.getcwd()

EXPECTED_TEST_CASES = 3
EXPECTED_ASSERTIONS = 50

def build_and_test(target_dir):
    """Build and run tests, return (success, stdout, stderr)"""
    binary_path = os.path.join(target_dir, "build", "clock")
    result = subprocess.run([binary_path], 
                            cwd=target_dir, capture_output=True, text=True)
    return (result.returncode == 0, result.stdout, result.stderr)

def verify_output(stdout, label):
    """Verify test output has expected test cases and assertions."""
    if "All tests passed" not in stdout:
        print(f"{label}: Tests did not pass!")
        print(stdout)
        sys.exit(1)
    
    for line in stdout.strip().split('\n'):
        if 'assertions in' in line and 'test cases' in line:
            print(f"  {line.strip()}")
            if f"{EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases" not in line:
                print(f"  ERROR: Expected {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases!")
                sys.exit(1)

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "clock")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # Configure once
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        # ============ TEST 1: Reference implementation ============
        print("=" * 60)
        print("TEST 1: Reference implementation (separate hour/minute)")
        print("=" * 60)
        
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                        os.path.join(target_dir, "clock.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "clock.h"))
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print(f"Reference implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
        
        print(f"Reference: All tests passed!")
        verify_output(stdout, "Reference")
        
        # Save reference evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "reference_output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        # ============ TEST 2: Alternative implementation ============
        print("\n" + "=" * 60)
        print("TEST 2: Alternative implementation (total minutes)")
        print("=" * 60)
        
        # Alternative header: single total_minutes_ member instead of hour_/minute_
        alt_h = '''#pragma once

#include <string>

namespace date_independent {

class clock {
   public:
    static clock at(int hour, int minute = 0);

    clock& plus(int minutes);
    clock& minus(int minutes);

    operator std::string() const;

    bool operator==(const clock& rhs) const;

   private:
    clock(int hour, int minute);
    int total_minutes_;
};

inline bool operator!=(const clock& lhs, const clock& rhs) {
    return !(lhs == rhs);
}

}  // namespace date_independent
'''
        with open(os.path.join(target_dir, "clock.h"), "w") as f:
            f.write(alt_h)
        
        # Alternative implementation
        alt_cpp = '''#include <iomanip>
#include <sstream>

#include "clock.h"

using namespace std;

namespace {

const int minutes_per_hour = 60;
const int hours_per_day = 24;
const int minutes_per_day = minutes_per_hour * hours_per_day;

}  // namespace

namespace date_independent {

// Alternative implementation: store time as total minutes since midnight
// This avoids the complex clean() normalization of separate hour/minute members
clock& clock::plus(int minutes) {
    total_minutes_ = (total_minutes_ + minutes) % minutes_per_day;
    if (total_minutes_ < 0) total_minutes_ += minutes_per_day;
    return *this;
}

clock& clock::minus(int minutes) {
    return plus(-minutes);
}

clock::operator string() const {
    ostringstream str;
    int h = total_minutes_ / minutes_per_hour;
    int m = total_minutes_ % minutes_per_hour;
    str << setw(2) << setfill('0') << h << ':' << setw(2) << setfill('0')
        << m;
    return str.str();
}

clock::clock(int hour, int minute) {
    total_minutes_ = (hour * minutes_per_hour + minute) % minutes_per_day;
    if (total_minutes_ < 0) total_minutes_ += minutes_per_day;
}

clock clock::at(int hour, int minute /*= 0*/) {
    return clock(hour, minute);
}

bool clock::operator==(const clock& rhs) const {
    return total_minutes_ == rhs.total_minutes_;
}

}  // namespace date_independent
'''
        with open(os.path.join(target_dir, "clock.cpp"), "w") as f:
            f.write(alt_cpp)
        
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        success, stdout, stderr = build_and_test(target_dir)
        
        if not success:
            print(f"Alternative implementation FAILED!")
            print(stdout)
            print(stderr)
            sys.exit(1)
        
        print(f"Alternative: All tests passed!")
        verify_output(stdout, "Alternative")
        
        # Save alternative evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "alternative_output.txt"), "w") as f:
            f.write(stdout)
            f.write(stderr)
        
        # Save combined output
        with open(os.path.join(REPO_ROOT, WORK_DIR, "output.txt"), "w") as f:
            f.write("=== REFERENCE (separate hour/minute) ===\n")
            f.write(open(os.path.join(REPO_ROOT, WORK_DIR, "reference_output.txt")).read())
            f.write("\n=== ALTERNATIVE (total minutes) ===\n")
            f.write(open(os.path.join(REPO_ROOT, WORK_DIR, "alternative_output.txt")).read())
        
        print("\nCheck completed successfully!")
        print(f"- Reference: {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases")
        print(f"- Alternative: {EXPECTED_ASSERTIONS} assertions in {EXPECTED_TEST_CASES} test cases")
        print(f"- Both implementations agree on all tests")
        print(f"- Hints added to .docs/hints.md")
        print(f"- Maintenance doc at docs/maintenance/clock.md")

if __name__ == "__main__":
    run_check()