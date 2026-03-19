# Dev bootstrapper
import subprocess, sys, os

def run_inspector():
    print("[...] Running Architecture Inspector...")
    try:
        # Since this script is now in scripts/, it should look for inspector in the same folder
        inspector_path = os.path.join(os.path.dirname(__file__), "architecture_inspector.py")
        result = subprocess.run([sys.executable, inspector_path], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Architecture inspection passed.")
            return True
        else:
            print("[!] Architecture inspection failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[!] Error running inspector: {e}")
        return False

if __name__ == "__main__":
    # Ensure current scripts directory is in path for relative imports
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    if scripts_dir not in sys.path:
        sys.path.append(scripts_dir)
        
    from architecture_inspector import scan_organism
    
    if scan_organism():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_py = os.path.join(base_dir, "main.py")
        
        try:
            from watchfiles import run_process, DefaultFilter
            
            class WatcherShield(DefaultFilter):
                def __call__(self, change, path):
                    # Ignore database, logs, and data folder to prevent infinite restart loops
                    if "data" in path or path.endswith((".db", ".sqlite", ".log", ".git", ".tmp")):
                        return False
                    return super().__call__(change, path)

            print(f"[...] Starting bot with hot-reload (Watching: {base_dir})...")
            # The Master Architect way: Shield the watcher from the DB
            run_process(base_dir, target=f"{sys.executable} main.py", watch_filter=WatcherShield())
        except ImportError:
            print("[...] Installing 'watchfiles' dependency...")
            subprocess.run([sys.executable, "-m", "pip", "install", "watchfiles"])
            try:
                from watchfiles import run_process, DefaultFilter
                print(f"[...] Starting bot with hot-reload (Watching: {base_dir})...")
                run_process(base_dir, target=f"{sys.executable} main.py", watch_filter=DefaultFilter())
            except ImportError as e:
                print(f"[!] Failed to install or import watchfiles. Running without hot-reload. {e}")
                subprocess.run([sys.executable, main_py])
    else:
        print("[!] Architectural issues found. Attempting auto-fix with Debugger...")
        try:
            from architecture_debugger import debug_architecture
            debug_architecture()
            print("[OK] Debugger finished. Please review changes and run again.")
        except Exception as e:
            print(f"[!] Debugger failed: {e}")
        sys.exit(1)
