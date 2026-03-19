import os, sys, ast, argparse, re, shutil

def get_inspector():
    """Robustly import architecture_inspector."""
    try:
        from architecture_inspector import DEFAULT_FORBIDDEN_IMPORTS, check_file_integrity
        return DEFAULT_FORBIDDEN_IMPORTS, check_file_integrity
    except ImportError:
        scripts_path = os.path.dirname(os.path.abspath(__file__))
        if scripts_path not in sys.path:
            sys.path.append(scripts_path)
        try:
            from architecture_inspector import DEFAULT_FORBIDDEN_IMPORTS, check_file_integrity
            return DEFAULT_FORBIDDEN_IMPORTS, check_file_integrity
        except ImportError as e:
            print(f"[!] Critical Error: Could not find architecture_inspector.py: {e}")
            sys.exit(1)

DEFAULT_FORBIDDEN_IMPORTS, check_file_integrity = get_inspector()

def safe_write(file_path, new_lines):
    """Writes lines to file with a backup and error handling."""
    try:
        # Create backup
        backup_path = file_path + ".bak"
        shutil.copy2(file_path, backup_path)
        
        with open(file_path, "w", encoding="utf-8", errors="replace") as f:
            f.writelines(new_lines)
        print(f"[OK] Fixed with backup created at {backup_path}")
    except PermissionError:
        print(f"[!] Permission Denied: Cannot write to {file_path}")
    except Exception as e:
        print(f"[!] Error writing to {file_path}: {e}")

def auto_fix_imports(file_path, errors):
    print(f"\n[🔍] Smart Analysis: {file_path}")
    if not os.path.exists(file_path): return
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        print(f"[!] Could not parse/read {file_path}: {e}. Skipping smart fix.")
        return

    offenders = [err.split(": ")[1] for err in errors if isinstance(err, str) and ": " in err]
    violations = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom):
                if node.module: names.append(node.module)
            else:
                names.extend([n.name for n in node.names if n.name])
            
            for name in names:
                for off in offenders:
                    if off and (name == off or name.startswith(f"{off}.")):
                        violations.append(name)

    suggestions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Name) and subnode.id in violations:
                    suggestions.append(f"Function '{node.name}' uses illegal import '{subnode.id}'.")
                    break
        elif isinstance(node, ast.ClassDef):
             for subnode in ast.walk(node):
                if isinstance(subnode, ast.Name) and subnode.id in violations:
                    suggestions.append(f"Class '{node.name}' uses illegal import '{subnode.id}'.")
                    break

    if suggestions:
        for s in suggestions: print(f"[💡] {s}")
        apply_smart_fix(file_path, offenders, suggestions)
    else:
        simple_fix(file_path, offenders)

def simple_fix(file_path, offenders):
    print(f"[...] Applying simple fix to {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    
    new_lines = []
    processed_lines = set()

    for i, line in enumerate(lines):
        if i in processed_lines: continue
        
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
            
        matched = False
        for off in offenders:
            # Only match if it looks like an actual import statement
            if re.search(rf"^\s*(import\s+.*?\b{re.escape(off)}\b|from\s+{re.escape(off)}\b)", line):
                new_lines.append(f"# FIX: Illegal import removed\n# {line}")
                matched = True
                break
        if not matched:
            new_lines.append(line)
            
    safe_write(file_path, new_lines)

def apply_smart_fix(file_path, offenders, suggestions):
    print(f"[...] Applying smart fix to {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    
    context = suggestions[0] if suggestions else "Manual refactor needed"
    new_lines = []
    for line in lines:
        if line.strip().startswith("#"):
            new_lines.append(line)
            continue

        matched = False
        for off in offenders:
            if re.search(rf"^\s*(import\s+.*?\b{re.escape(off)}\b|from\s+{re.escape(off)}\b)", line):
                new_lines.append(f"# FIX (Smart): Illegal import found.\n# Context: {context}\n# {line}")
                matched = True
                break
        if not matched:
            new_lines.append(line)
            
    safe_write(file_path, new_lines)

def debug_architecture(base_dir="."):
    print("🔍 Starting Hardened Architecture Debugger...")
    has_issues = False
    for layer in DEFAULT_FORBIDDEN_IMPORTS.keys():
        path = os.path.join(base_dir, layer)
        if not os.path.exists(path): continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    errs = check_file_integrity(file_path, layer, DEFAULT_FORBIDDEN_IMPORTS)
                    if errs:
                        print(f"[!] Issues found in {file_path}")
                        auto_fix_imports(file_path, errs)
                        has_issues = True
    if not has_issues:
        print("[OK] No architectural issues found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Base directory to scan")
    args = parser.parse_args()
    debug_architecture(args.dir)
