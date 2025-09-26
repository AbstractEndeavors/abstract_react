from utils import *
# 1) Read tsconfig.json once
def load_tsconfig(tsconfig_path: str) -> Tuple[Path, Dict[str, List[str]]]:
    cfg = json.loads(Path(tsconfig_path).read_text())
    opts = cfg.get("compilerOptions", {})
    base_url = Path(cfg.get("compilerOptions", {})
                    .get("baseUrl", "."))
    paths = opts.get("paths", {})
    return base_url, paths

# 2) Given an import string, resolve to an actual file on disk
def resolve_import(
    imp: str,
    current_dir: Path,
    project_root: Path,
    base_url: Path,
    path_map: Dict[str, List[str]]
) -> Optional[Path]:
    # --- Relative imports ---
    if imp.startswith("."):
        candidate = (current_dir / imp)
        return find_actual_file(candidate)

    # --- Alias imports from tsconfig paths ---
    for alias_pattern, targets in path_map.items():
        # e.g. alias_pattern = "@components/*"
        if "*" in alias_pattern:
            prefix = alias_pattern.split("*")[0]
            if not imp.startswith(prefix):
                continue
            suffix = imp[len(prefix):]
            for t in targets:
                # e.g. t = "src/components/*"
                tpref = t.split("*")[0]
                candidate = project_root / (tpref + suffix)
                resolved = find_actual_file(candidate)
                if resolved:
                    return resolved
        else:
            # exact alias, no wildcard
            if imp == alias_pattern:
                for t in targets:
                    candidate = project_root / t
                    resolved = find_actual_file(candidate)
                    if resolved:
                        return resolved
    return None

# 3) Try extensions & index files
def find_actual_file(base: Path) -> Optional[Path]:
    exts = [".ts", ".tsx", ".js", ".jsx", ".json"]
    # try base + each ext
    for e in exts:
        p = base.with_suffix(e)
        if p.is_file():
            return p
    # maybe base already had extension
    if base.is_file():
        return base
    # directory → look for index.*
    if base.is_dir():
        for e in exts:
            idx = base / f"index{e}"
            if idx.is_file():
                return idx
    # fallback glob (will pick first match)
    matches = glob.glob(str(base) + "*")
    if matches:
        return Path(matches[0])
    return None

# 4) Walk imports recursively
def get_imports(
    file_path: Path,
    tsconfig_path: str,
    seen: Optional[Set[Path]] = None
) -> List[Path]:
    if seen is None:
        seen = set()
    if isinstance(file_path,str):
        file_path = Path(file_path)
    if isinstance(tsconfig_path,str):
        tsconfig_path = Path(tsconfig_path)
    if file_path in seen or not file_path.is_file():
        return []
    seen = set(seen or ())
    seen.add(file_path)
    project_root = 
    if tsconfig_path:
        project_root = Path(tsconfig_path).parent
        base_url, path_map = load_tsconfig(tsconfig_path)
    current_dir = file_path.parent
    imports: List[Path] = []
    for line in file_path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("import"):
            continue
        # crude split; for more robust parsing you'd use an AST parser
        if " from " in line:
            mod = line.split(" from ")[1].rstrip(";").strip().strip('"\'')
        elif line.startswith("import("):
            mod = line[line.find("(")+1:line.rfind(")")].strip().strip('"\'')
        else:
            continue

        resolved = resolve_import(mod, current_dir, project_root, base_url, path_map)
        if resolved and resolved not in seen:
            imports.append(resolved)
            # recurse into that file
            imports.extend(get_imports(resolved, tsconfig_path, seen))
    return list(set(imports))
