import os
import subprocess
import shutil
import tempfile
import sys
import json

EXERCISE_DIR = "exercises/practice/flower-field"
WORK_DIR = "work/R20-T031"
REPO_ROOT = os.getcwd()

def run_check():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = os.path.join(tmp_dir, "flower-field")
        shutil.copytree(EXERCISE_DIR, target_dir, dirs_exist_ok=True)
        
        # Substitute reference
        shutil.copyfile(os.path.join(target_dir, ".meta/example.cpp"), 
                        os.path.join(target_dir, "flower_field.cpp"))
        shutil.copyfile(os.path.join(target_dir, ".meta/example.h"), 
                        os.path.join(target_dir, "flower_field.h"))
        
        # Run cmake with ALL_TESTS
        print("Configuring...")
        subprocess.run(["/opt/homebrew/bin/cmake", "-S", ".", "-B", "build", "-DEXERCISM_RUN_ALL_TESTS=ON"], 
                       cwd=target_dir, check=True)
        
        print("Building...")
        subprocess.run(["/opt/homebrew/bin/cmake", "--build", "build"], 
                       cwd=target_dir, check=True)
        
        # Run tests - execute the binary directly to ensure tests run
        print("Running tests...")
        binary_path = os.path.join(target_dir, "build", "flower-field")
        result = subprocess.run([binary_path], 
                                cwd=target_dir, capture_output=True, text=True)
        
        # Save evidence
        with open(os.path.join(REPO_ROOT, WORK_DIR, "output.txt"), "w") as f:
            f.write(result.stdout)
            f.write(result.stderr)
            
        if result.returncode != 0:
            print(f"Tests failed with return code {result.returncode}!")
            sys.exit(1)
            
        if "All tests passed" not in result.stdout:
            print("Tests did not pass!")
            sys.exit(1)
            
        print("Check passed successfully!")

if __name__ == "__main__":
    run_check()
