

# === FIXED MULTI-LINE IMPORT ACCUMULATOR ===
def get_complete_import_text(lines: List[str], start_idx: int) -> Tuple[int, str]:
    """Extract complete import statement starting at start_idx
    
    Returns: (end_idx, complete_import_text)
    """
    import_parts = []
    
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        import_parts.append(line)
        
        # Check if this line completes the import (has semicolon)
        if ';' in line:
            complete_import = ' '.join(import_parts)
            return idx, complete_import
    
    # If we reach here, import wasn't closed properly
    # Return what we have
    return len(lines) - 1, ' '.join(import_parts)

def extract_imports_from_lines(lines: List[str]) -> List[Tuple[int, int, str]]:
    """Extract all import statements from raw text lines
    
    Returns: [(start_idx, end_idx, complete_import_text)]
    """
    imports = []
    idx = 0
    
    while idx < len(lines):
        line = lines[idx].strip()
        
        # Check if line starts an import
        if line.startswith('import'):
            end_idx, complete_import = get_complete_import_text(lines, idx)
            imports.append((idx, end_idx, complete_import))
            idx = end_idx + 1  # Skip to line after import ends
        else:
            idx += 1
    
    return imports

# === IMPORT SYMBOL PARSING ===
def parse_import_symbols(import_text: str) -> List[str]:
    """Extract all imported symbols from import text"""
    # Remove 'import' keyword and normalize whitespace
    import_text = import_text.replace('import', '', 1)
    import_text = re.sub(r'\s+', ' ', import_text)  # Collapse all whitespace
    import_text = import_text.strip()
    
    # Split by 'from'
    if ' from ' not in import_text:
        return []
    
    import_part, _ = import_text.split(' from ', 1)
    import_part = import_part.strip()
    
    # Handle different import types
    if '{' in import_part and '}' in import_part:
        # Named imports: { A, B, C }
        inside_braces = import_part[import_part.find('{')+1:import_part.rfind('}')]
        inside_braces = inside_braces.strip().rstrip(',')
        
        # Split by comma and clean
        symbols = []
        for s in inside_braces.split(','):
            s = s.strip()
            if s:
                symbols.append(s)
        return symbols
        
    elif import_part.startswith('* as '):
        # Namespace import
        return [import_part.replace('* as ', '').strip()]
    
    else:
        # Default import
        return [import_part.strip()]

def extract_from_path(import_text: str) -> str:
    """Extract the 'from' path from import text"""
    if ' from ' not in import_text:
        return ''
    
    _, path_part = import_text.split(' from ', 1)
    
    # Remove semicolon, quotes, whitespace
    from_path = path_part.strip()
    from_path = from_path.rstrip(';').strip()
    from_path = from_path.strip('"\'')
    
    return from_path

# === COMPLETE IMPORT EXTRACTION ===
def extract_all_imports_robust(file_path: str) -> List[ImportStatement]:
    """Extract all imports using simple line-based approach"""
    # Read raw lines (not using the complex parser initially)
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    
    # Strip only trailing newlines, preserve indentation
    lines = [line.rstrip('\n\r') for line in raw_lines]
    
    # Extract imports
    import_blocks = extract_imports_from_lines(lines)
    
    imports = []
    for start_idx, end_idx, import_text in import_blocks:
        # Parse symbols
        symbols = parse_import_symbols(import_text)
        if not symbols:
            continue
        
        # Extract path
        from_path = extract_from_path(import_text)
        if not from_path:
            continue
        
        is_relative = from_path.startswith('.') or from_path.startswith('..')
        
        # Extract trailing comment
        trailing_comment = None
        if '//' in import_text:
            # Find comment after the semicolon (if any)
            parts = import_text.split(';', 1)
            if len(parts) > 1 and '//' in parts[1]:
                comment_part = parts[1].split('//', 1)[1]
                trailing_comment = '//' + comment_part.strip()
        
        imports.append(ImportStatement(
            raw_lines=lines[start_idx:end_idx+1],
            imports=symbols,
            from_path=from_path,
            is_relative=is_relative,
            start_line_index=start_idx,
            end_line_index=end_idx,
            trailing_comment=trailing_comment
        ))
    
    return imports

# === PATH ALIAS REGISTRY (from previous code) ===
def check_has_wildcard(path_config: str) -> bool:
    return path_config.endswith('/*')

def build_path_alias_registry(directory=None) -> Dict[str, PathAlias]:
    """Build registry of path aliases from tsconfig"""
    paths = get_ts_config_paths(directory=directory)
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    
    registry = {}
    for alias, path_configs in paths.items():
        if not path_configs:
            continue
        
        path_config = path_configs[0]
        has_wildcard = check_has_wildcard(path_config) and check_has_wildcard(alias)
        
        clean_alias = alias.rstrip('/*')
        clean_path = path_config.rstrip('/*')
        
        resolved = normalize_path(os.path.join(ts_root_dir, clean_path))
        
        registry[clean_alias] = PathAlias(
            alias=clean_alias,
            resolved_path=resolved,
            base_dir=ts_root_dir,
            has_wildcard=has_wildcard
        )
    
    return registry

def normalize_path(path: str) -> str:
    return os.path.normpath(path).replace('\\', '/')

# === PATH CONVERSION ===
def resolve_absolute_import_path(import_path: str, file_directory: str, ts_root_dir: str) -> str:
    """Resolve import path to absolute filesystem path"""
    if import_path.startswith('.'):
        # Relative import - resolve from file directory
        abs_path = os.path.abspath(os.path.join(file_directory, import_path))
        return normalize_path(abs_path)
    else:
        # Assume relative to ts root
        return normalize_path(os.path.join(ts_root_dir, import_path))

def find_matching_alias(absolute_path: str, path_aliases: Dict[str, PathAlias]) -> Optional[Tuple[str, str, bool]]:
    """Find best matching path alias"""
    best_match = None
    best_match_len = 0
    
    for alias_key, path_alias in path_aliases.items():
        resolved = path_alias.resolved_path
        
        if absolute_path.startswith(resolved):
            match_len = len(resolved)
            remainder = absolute_path[match_len:].lstrip('/')
            
            # Validate wildcard support
            if remainder and not path_alias.has_wildcard:
                continue
            
            if match_len > best_match_len:
                best_match_len = match_len
                best_match = (alias_key, remainder, path_alias.has_wildcard)
    
    return best_match

def convert_to_alias_path(import_stmt: ImportStatement, file_directory: str, 
                          ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Optional[str]:
    """Convert import path to alias path if possible"""
    abs_path = resolve_absolute_import_path(import_stmt.from_path, file_directory, ts_root_dir)
    match = find_matching_alias(abs_path, path_aliases)
    
    if match:
        alias_key, remainder, has_wildcard = match
        if remainder and has_wildcard:
            return f"{alias_key}/{remainder}"
        elif not remainder:
            return alias_key
    
    return None

# === CONSOLIDATION ===
def consolidate_imports_with_comments(imports: List[ImportStatement], file_directory: str,
                                     ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Dict[str, dict]:
    """Consolidate imports preserving comments"""
    consolidated = defaultdict(lambda: {'symbols': set(), 'comments': []})
    
    for import_stmt in imports:
        alias_path = convert_to_alias_path(import_stmt, file_directory, ts_root_dir, path_aliases)
        target_path = alias_path if alias_path else import_stmt.from_path
        
        for symbol in import_stmt.imports:
            consolidated[target_path]['symbols'].add(symbol)
        
        if import_stmt.trailing_comment:
            comment = import_stmt.trailing_comment.strip()
            if comment and not comment.startswith('//'):
                comment = '// ' + comment
            consolidated[target_path]['comments'].append(comment)
    
    return consolidated

def generate_import_statements_with_comments(consolidated: Dict[str, dict]) -> List[str]:
    """Generate import statements with comments"""
    import_lines = []
    
    for path in sorted(consolidated.keys()):
        data = consolidated[path]
        symbols = sorted(data['symbols'])
        comments = data['comments']
        
        if len(symbols) == 1:
            import_line = f"import {{ {symbols[0]} }} from '{path}';"
        else:
            symbols_str = ', '.join(symbols)
            import_line = f"import {{ {symbols_str} }} from '{path}';"
        
        if comments:
            unique_comments = list(dict.fromkeys(comments))
            if len(unique_comments) == 1:
                import_line += f" {unique_comments[0]}"
            else:
                for comment in unique_comments:
                    import_lines.append(comment)
                import_lines.append(import_line)
                continue
        
        import_lines.append(import_line)
    
    return import_lines

# === FILE RECONSTRUCTION ===
def get_non_import_lines(file_path: str, imports: List[ImportStatement]) -> List[str]:
    """Get all lines that aren't part of imports"""
    import_line_indices = set()
    for import_stmt in imports:
        for idx in range(import_stmt.start_line_index, import_stmt.end_line_index + 1):
            import_line_indices.add(idx)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    non_import_lines = []
    for idx, line in enumerate(lines):
        if idx not in import_line_indices:
            non_import_lines.append(line.rstrip('\n\r'))
    
    return non_import_lines

def reconstruct_file(new_imports: List[str], non_import_lines: List[str]) -> str:
    """Reconstruct complete file"""
    output_lines = []
    
    # Add consolidated imports
    output_lines.extend(new_imports)
    output_lines.append('')  # Blank line
    
    # Add rest of file
    output_lines.extend(non_import_lines)
    
    return '\n'.join(output_lines)

# === MAIN WORKFLOW ===
def process_file_consolidate_imports(file_path: str, directory: str, 
                                     write_back: bool = False,
                                     show_debug: bool = False) -> dict:
    """Complete workflow for import consolidation"""
    
    # Setup environment
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    file_directory = os.path.dirname(file_path)
    path_aliases = build_path_alias_registry(directory=directory)
    
    # Extract all imports (handles multi-line)
    imports = extract_all_imports_robust(file_path)
    
    if show_debug:
        print("=== EXTRACTED IMPORTS ===")
        for i, imp in enumerate(imports):
            print(f"\n{i+1}. Lines {imp.start_line_index}-{imp.end_line_index}:")
            print(f"   From: {imp.from_path}")
            print(f"   Symbols ({len(imp.imports)}): {', '.join(imp.imports)}")
    
    # Consolidate
    consolidated = consolidate_imports_with_comments(
        imports, file_directory, ts_root_dir, path_aliases
    )
    
    # Generate new imports
    new_imports = generate_import_statements_with_comments(consolidated)
    
    # Get non-import lines
    non_import_lines = get_non_import_lines(file_path, imports)
    
    # Reconstruct
    processed = reconstruct_file(new_imports, non_import_lines)
    
    # Read original
    original = read_from_file(file_path)
    
    # Write if requested
    written = False
    if write_back:
        write_to_file(file_path, processed)
        written = True
    
    return {
        'original': original,
        'processed': processed,
        'imports': imports,
        'consolidated': consolidated,
        'new_imports': new_imports,
        'written': written,
        'stats': {
            'original_import_count': len(imports),
            'consolidated_import_count': len(new_imports),
            'total_symbols': sum(len(d['symbols']) for d in consolidated.values())
        }
    }

