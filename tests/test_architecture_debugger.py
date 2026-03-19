import os
import shutil
from scripts.architecture_debugger import debug_architecture

def setup_test_violation():
    """Create a file in 'core' that illegally imports 'data'."""
    test_file = "core/test_violation.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("from data.repository import Repository\n\n")
        f.write("def do_work():\n")
        f.write("    repo = Repository()\n")
        f.write("    return repo.get_active_activity('user1')\n")
    return test_file

def run_test():
    print("--- 🧪 Testing Architecture Debugger ---")
    test_file = setup_test_violation()
    
    print(f"Created violation in {test_file}")
    
    # Run the debugger
    debug_architecture()
    
    # Verify the result
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    print("\n--- 📄 Resulting File Content ---")
    print(content)
    
    if "# FIX: Illegal import removed" in content:
        print("\n✅ Debugger identified and commented out the illegal import.")
    else:
        print("\n❌ Debugger failed to handle the illegal import.")

if __name__ == "__main__":
    if not os.path.exists("core"):
        os.makedirs("core")
    run_test()
