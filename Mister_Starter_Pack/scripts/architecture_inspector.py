import os, sys, ast, argparse

DEFAULT_FORBIDDEN_IMPORTS = {
    "core": ["bot", "data", "services"],
    "bot": [], # Interaction layer can coordinate between core and data
    "data": ["services", "bot"],
    "services": ["bot"]
}

def check_file_integrity(file_path, folder_name, rules, max_lines=200):
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            if len(lines) > max_lines: return [f"File too long ({len(lines)} > {max_lines})"]
            tree = ast.parse("".join(lines))
    except Exception as e: return [f"Analysis Error: {e}"]
    
    errors = []
    forbidden = rules.get(folder_name, [])
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.ImportFrom):
                if node.module: names.append(node.module)
            else:
                names.extend([n.name for n in node.names])
            
            for name in names:
                if name:
                    for f in forbidden:
                        if name == f or name.startswith(f"{f}."):
                            errors.append(f"Illegal import: {name}")
                            break
    return errors

def scan_organism(base_dir=".", max_lines=200):
    has_issues = False
    for layer in DEFAULT_FORBIDDEN_IMPORTS.keys():
        path = os.path.join(base_dir, layer)
        if not os.path.exists(path): continue
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    errs = check_file_integrity(os.path.join(root, file), layer, DEFAULT_FORBIDDEN_IMPORTS, max_lines)
                    for e in errs: 
                        print(f"[!] {os.path.join(root, file)}: {e}")
                        has_issues = True
    return not has_issues

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default=".", help="Base directory to scan")
    args = parser.parse_args()
    if not scan_organism(args.dir):
        sys.exit(1)
    else:
        print("[OK] Architecture inspection passed.")
