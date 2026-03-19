import os
import shutil
import sys
import ast
from scripts.architecture_debugger import debug_architecture

TEST_DIR = "tests/stress_test"

def setup_test_environment():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(f"{TEST_DIR}/core", exist_ok=True)
    os.makedirs(f"{TEST_DIR}/bot", exist_ok=True)
    os.makedirs(f"{TEST_DIR}/data", exist_ok=True)

def create_test_file(path, content):
    full_path = os.path.join(TEST_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    return full_path

def run_stress_tests():
    setup_test_environment()
    
    test_cases = [
        # 1. Simple direct import
        ("core/case1.py", "import data\nprint(data)"),
        
        # 2. From ... import ...
        ("core/case2.py", "from data.repository import Repository\nrepo = Repository()"),
        
        # 3. Sub-module import
        ("core/case3.py", "import data.repository\nrepo = data.repository.Repository()"),
        
        # 4. Import inside function
        ("core/case4.py", "def leak():\n    import data\n    return data"),
        
        # 5. Import inside class
        ("core/case5.py", "class DirtyClass:\n    import data\n    def __init__(self):\n        self.d = data"),
        
        # 6. Nested function leak
        ("core/case6.py", "def outer():\n    def inner():\n        import data\n    inner()"),
        
        # 7. Alias import
        ("core/case7.py", "import data as d\nprint(d)"),
        
        # 8. Multiple imports one line
        ("core/case8.py", "import os, data, sys\nprint(data)"),
        
        # 9. Class method leak
        ("core/case9.py", "class MyClass:\n    def get_data(self):\n        import data\n        return data"),
        
        # 10. Global variable init
        ("core/case10.py", "import data\nGLOBAL_DATA = data.Repository()"),
        
        # 11. Forbidden import in decorator (complex)
        ("core/case11.py", "import data\n@data.some_decorator\ndef func(): pass"),
        
        # 12. Commented import (Valid - should NOT be fixed)
        ("core/case12.py", "# import data\nprint('safe')"),
        
        # 13. String contains name (Valid - should NOT be fixed)
        ("core/case13.py", "name = 'data.repository'\nprint(name)"),
        
        # 14. Valid import that looks similar
        ("core/case14.py", "import database_utils\nprint(database_utils)"),
        
        # 15. Multi-layer complex file
        ("core/case15.py", """
import os
from data.repository import Repository
import services.external_api as api

def process():
    repo = Repository()
    return api.call()
""")
    ]

    print(f"--- 🧪 Running 15 Stress Test Cases ---")
    results = []
    
    for path, content in test_cases:
        full_path = create_test_file(path, content)
        print(f"Testing {path}...")
        
    debug_architecture(TEST_DIR)
    
    print("\n--- 📊 Stress Test Results Summary ---")
    for path, _ in test_cases:
        full_path = os.path.join(TEST_DIR, path)
        with open(full_path, "r", encoding="utf-8") as f:
            final_content = f.read()
            
        case_num = path.split("/")[-1].replace(".py", "")
        # Check if it was supposed to be fixed (all cases except 12, 13, 14)
        should_be_fixed = case_num not in ["case12", "case13", "case14"]
        is_fixed = "FIX" in final_content
        
        status = "✅ PASS" if is_fixed == should_be_fixed else "❌ FAIL"
        results.append((path, status))
        print(f"{path}: {status}")

    print("\n--- 🧠 Analysis of Weaknesses ---")
    # Identify failures
    failures = [r for r in results if "FAIL" in r[1]]
    if not failures:
        print("Excellent! The debugger passed all 15 scenarios.")
    else:
        print(f"Found {len(failures)} failures. Areas for improvement:")
        for f in failures:
            print(f"- {f[0]}")

if __name__ == "__main__":
    run_stress_tests()
