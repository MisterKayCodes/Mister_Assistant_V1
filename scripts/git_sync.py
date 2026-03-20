import os, re, subprocess, sys

def sync():
    # Use absolute path to the root since we are in scripts/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracking_path = os.path.join(base_dir, "docs/tracking.md")
    
    if not os.path.exists(os.path.join(base_dir, ".git")):
        print("[...] Git repository not found. Initializing...")
        subprocess.run("git init", shell=True, cwd=base_dir)

    if not os.path.exists(tracking_path):
        print(f"[!] {tracking_path} not found. Git sync aborted.")
        return

    try:
        with open(tracking_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return
                
            for line in reversed(lines):
                # Match git commit style: | `commit message` | 
                m = re.search(r'\|\s*`([^`]+)`\s*\|', line)
                if m:
                    msg = m.group(1)
                    print(f"[...] Syncing changes with commit: {msg}")
                    
                    # Get current branch
                    branch_res = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True, cwd=base_dir)
                    branch = branch_res.stdout.strip() or "master"
                    
                    # Run git commands in the root directory
                    subprocess.run("git add .", shell=True, cwd=base_dir)
                    subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=base_dir)
                    subprocess.run(f"git push origin {branch}", shell=True, cwd=base_dir)
                    print(f"[OK] Sync complete: {msg} on {branch}")
                    return
    except Exception as e:
        print(f"[!] Sync error: {e}")

if __name__ == "__main__":
    sync()
