from .funcs import get_ts_lines
from .schemas import *
# === CORE PARSING ===
def clean_string(string=None, chars=None, add=None):
    add = if_not_bool_default(add, True)
    chars = chars or []
    if add:
        chars += ['', ' ', '\n', '\t']
    return eatAll(string, chars)

def count_chars(string, char):
    return len(string.split(char)) - 1

def get_contents(contents=None, file_path=None):
    if contents:
        if os.path.isfile(contents):
            file_path = contents
            contents = None
    return contents or read_from_file(file_path)

def get_lines(contents=None, file_path=None, clean=False, chars=None, add=None):
    contents = get_contents(contents=contents, file_path=file_path) or ""
    if clean:
        contents = clean_string(contents, chars=chars, add=add)
    contents_spl = contents.split('\n') or []
    if clean:
        contents_spl = [clean_string(content, chars=chars, add=add) for content in contents_spl]
    return contents_spl

# === IMPORT PARSING ===
def parse_import_line(line: str, line_index: int) -> Optional[ImportStatement]:
    """Extract import statement components"""
    line = line.strip()
    if not line.startswith('import'):
        return None
    
    # Handle: import { MetaData, ProcessorConfig } from '../types/metadata'
    # Handle: import MetaData from '../types/metadata'
    # Handle: import * as MetaData from '../types/metadata'
    
    if ' from ' not in line:
        return None
    
    import_part, path_part = line.split(' from ', 1)
    from_path = path_part.strip().strip("';\"")
    
    # Extract imported symbols
    import_part = import_part.replace('import', '').strip()
    
    if import_part.startswith('{') and '}' in import_part:
        # Named imports: { MetaData, ProcessorConfig }
        imports_str = import_part[import_part.find('{')+1:import_part.find('}')]
        imports = [imp.strip() for imp in imports_str.split(',')]
    elif import_part.startswith('* as '):
        # Namespace import: * as MetaData
        imports = [import_part.replace('* as ', '').strip()]
    else:
        # Default import: MetaData
        imports = [import_part.strip()]
    
    is_relative = from_path.startswith('.') or from_path.startswith('..')
    
    return ImportStatement(
        raw_line=line,
        imports=imports,
        from_path=from_path,
        is_relative=is_relative,
        line_index=line_index
    )

def extract_imports(contents=None, file_path=None) -> List[ImportStatement]:
    """Extract all import statements from file"""
    lines = get_lines(contents=contents, file_path=file_path)
    imports = []
    
    for idx, line in enumerate(lines):
        import_stmt = parse_import_line(line, idx)
        if import_stmt:
            imports.append(import_stmt)
    
    return imports
# === PATH RESOLUTION ===
def get_import_path(relative_import, file_path=None, directory=None):
    """Resolve relative import to absolute path"""
    if not directory:
        if file_path:
            if os.path.isdir(file_path):
                directory = file_path
            elif os.path.isfile(file_path):
                directory = os.path.dirname(file_path)
    if not directory:
        return None
    
    parent_dir_count = count_chars(relative_import, '..')
    for _ in range(parent_dir_count):
        directory = os.path.dirname(directory)
    
    rel_path = relative_import.split('./')[-1]
    return os.path.join(directory, rel_path)

def normalize_path(path: str) -> str:
    """Normalize path for comparison"""
    return os.path.normpath(path).replace('\\', '/')

def resolve_absolute_import_path(import_path: str, file_directory: str, ts_root_dir: str) -> str:
    """Resolve import path to absolute filesystem path"""
    if import_path.startswith('.'):
        # Relative import
        return normalize_path(get_import_path(import_path, directory=file_directory))
    else:
        # Assume relative to ts root
        return normalize_path(os.path.join(ts_root_dir, import_path))

# === TSCONFIG HANDLING ===
def get_spec_file_path(filename, directory=None):
    file_paths = find_files(filename, directory=directory)
    return get_single_from_list(file_paths)

def get_ts_config_path(directory=None):
    return get_spec_file_path('tsconfig', directory=directory)

def get_ts_config_data(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return safe_load_from_file(ts_config_path)

def get_ts_config_root_dir(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return os.path.dirname(ts_config_path)

def get_ts_config_compilerOptions(data=None, directory=None):
    if not data:
        data = get_ts_config_data(directory=directory)
    data = data or {}
    return data.get('compilerOptions') or {}

def get_ts_config_paths(data=None, directory=None):
    data = get_ts_config_compilerOptions(data=data, directory=directory) or {}
    return data.get('paths') or {}

def build_path_alias_registry(directory=None) -> Dict[str, PathAlias]:
    """Build registry of path aliases from tsconfig"""
    paths = get_ts_config_paths(directory=directory)
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    
    registry = {}
    for alias, path_configs in paths.items():
        if not path_configs:
            continue
        
        # Take first path config
        path_config = path_configs[0]
        
        # Remove trailing /* from both alias and path
        clean_alias = alias.rstrip('/*')
        clean_path = path_config.rstrip('/*')
        
        resolved = normalize_path(os.path.join(ts_root_dir, clean_path))
        
        registry[clean_alias] = PathAlias(
            alias=clean_alias,
            resolved_path=resolved,
            base_dir=ts_root_dir
        )
    
    return registry
# === CONSOLIDATION ===
def consolidate_imports(imports: List[ImportStatement], file_directory: str,
                       ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Dict[str, Set[str]]:
    """Consolidate imports by target path
    Returns: {resolved_path: set(imported_symbols)}
    """
    consolidated = defaultdict(set)
    
    for import_stmt in imports:
        # Try to convert to alias path
        alias_path = convert_to_alias_path(import_stmt, file_directory, ts_root_dir, path_aliases)
        
        # Use alias if available, otherwise keep original
        target_path = alias_path if alias_path else import_stmt.from_path
        
        # Add all imported symbols
        for symbol in import_stmt.imports:
            consolidated[target_path].add(symbol)
    
    return consolidated

def generate_import_statements(consolidated: Dict[str, Set[str]]) -> List[str]:
    """Generate clean import statements from consolidated data"""
    import_lines = []
    
    for path in sorted(consolidated.keys()):
        symbols = sorted(consolidated[path])
        
        if len(symbols) == 1:
            import_line = f"import {{ {symbols[0]} }} from '{path}';"
        else:
            symbols_str = ', '.join(symbols)
            import_line = f"import {{ {symbols_str} }} from '{path}';"
        
        import_lines.append(import_line)
    
    return import_lines

# === MAIN WORKFLOW ===
def process_imports(file_path: str, directory: str) -> str:
    """Main workflow: parse, consolidate, and regenerate imports"""
    
    # Setup environment
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    file_directory = os.path.dirname(file_path)
    path_aliases = build_path_alias_registry(directory=directory)
    
    # Extract imports
    imports = extract_imports(file_path=file_path)
    
    # Consolidate
    consolidated = consolidate_imports(imports, file_directory, ts_root_dir, path_aliases)
    
    # Generate new import statements
    new_imports = generate_import_statements(consolidated)
    
    return '\n'.join(new_imports)

# === PATH ALIAS PROCESSING ===
def check_has_wildcard(path_config: str) -> bool:
    """Check if path configuration uses wildcard"""
    return path_config.endswith('/*')

def build_path_alias_registry(directory=None) -> Dict[str, PathAlias]:
    """Build registry of path aliases from tsconfig"""
    paths = get_ts_config_paths(directory=directory)
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    
    registry = {}
    for alias, path_configs in paths.items():
        if not path_configs:
            continue
        
        # Take first path config
        path_config = path_configs[0]
        
        # Check for wildcard BEFORE cleaning
        has_wildcard = check_has_wildcard(path_config) and check_has_wildcard(alias)
        
        # Remove trailing /* from both alias and path
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

# === PATH MATCHING WITH WILDCARD VALIDATION ===
def find_matching_alias(absolute_path: str, path_aliases: Dict[str, PathAlias]) -> Optional[tuple]:
    """Find best matching path alias for given absolute path
    Returns: (alias_key, relative_remainder) or None
    
    Rules:
    - If alias has wildcard: can match with remainder
    - If alias has NO wildcard: must be exact match (no remainder)
    """
    best_match = None
    best_match_len = 0
    
    for alias_key, path_alias in path_aliases.items():
        resolved = path_alias.resolved_path
        
        if absolute_path.startswith(resolved):
            match_len = len(resolved)
            remainder = absolute_path[match_len:].lstrip('/')
            
            # Validate based on wildcard support
            if remainder and not path_alias.has_wildcard:
                # Has remainder but alias doesn't support wildcards - skip
                continue
            
            if match_len > best_match_len:
                best_match_len = match_len
                best_match = (alias_key, remainder, path_alias.has_wildcard)
    
    return best_match

def convert_to_alias_path(import_stmt: ImportStatement, file_directory: str, 
                          ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Optional[str]:
    """Convert import path to alias path if possible"""
    
    # Resolve to absolute path
    abs_path = resolve_absolute_import_path(import_stmt.from_path, file_directory, ts_root_dir)
    
    # Find matching alias
    match = find_matching_alias(abs_path, path_aliases)
    
    if match:
        alias_key, remainder, has_wildcard = match
        
        if remainder:
            # Only append remainder if wildcard is supported
            if has_wildcard:
                return f"{alias_key}/{remainder}"
            else:
                # Shouldn't happen due to validation, but be safe
                return None
        else:
            # Exact match
            return alias_key
    
    return None

# === VALIDATION QUEUE ===
def validate_import_processing(imports: List[ImportStatement], path_aliases: Dict[str, PathAlias],
                               file_directory: str, ts_root_dir: str) -> Dict[str, any]:
    """Validate which imports can be processed with available aliases
    
    Returns queue of: {
        'processable': [(import_stmt, alias_path)],
        'unprocessable': [(import_stmt, reason)],
        'stats': {...}
    }
    """
    processable = []
    unprocessable = []
    
    for import_stmt in imports:
        if not import_stmt.is_relative:
            # Already using alias or absolute import
            unprocessable.append((import_stmt, 'not_relative'))
            continue
        
        alias_path = convert_to_alias_path(import_stmt, file_directory, ts_root_dir, path_aliases)
        
        if alias_path:
            processable.append((import_stmt, alias_path))
        else:
            # Couldn't find matching alias
            abs_path = resolve_absolute_import_path(import_stmt.from_path, file_directory, ts_root_dir)
            
            # Determine why
            reason = 'no_matching_alias'
            for alias_key, path_alias in path_aliases.items():
                if abs_path.startswith(path_alias.resolved_path):
                    remainder = abs_path[len(path_alias.resolved_path):].lstrip('/')
                    if remainder and not path_alias.has_wildcard:
                        reason = f'needs_wildcard (alias: {alias_key})'
                        break
            
            unprocessable.append((import_stmt, reason))
    
    stats = {
        'total': len(imports),
        'processable': len(processable),
        'unprocessable': len(unprocessable),
        'success_rate': len(processable) / len(imports) if imports else 0
    }
    
    return {
        'processable': processable,
        'unprocessable': unprocessable,
        'stats': stats
    }

# === UPDATED MAIN WORKFLOW ===
def process_imports(file_path: str, directory: str, validate_only=False) -> dict:
    """Main workflow: parse, validate, consolidate, and regenerate imports
    
    Args:
        file_path: Path to file to process
        directory: Project directory
        validate_only: If True, only return validation results without generating output
    
    Returns:
        {
            'imports': str,  # Generated import statements
            'validation': dict,  # Validation results
            'registry': ImportRegistry  # Full registry for inspection
        }
    """
    
    # Setup environment
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    file_directory = os.path.dirname(file_path)
    path_aliases = build_path_alias_registry(directory=directory)
    
    # Extract imports
    imports = extract_imports(file_path=file_path)
    
    # Validate
    validation = validate_import_processing(imports, path_aliases, file_directory, ts_root_dir)
    
    if validate_only:
        return {
            'imports': None,
            'validation': validation,
            'registry': ImportRegistry(
                imports=imports,
                path_aliases=path_aliases,
                file_directory=file_directory,
                ts_root_dir=ts_root_dir
            )
        }
    
    # Consolidate (only processable imports)
    consolidated = defaultdict(set)
    
    for import_stmt, alias_path in validation['processable']:
        for symbol in import_stmt.imports:
            consolidated[alias_path].add(symbol)
    
    # Keep unprocessable imports as-is
    for import_stmt, reason in validation['unprocessable']:
        for symbol in import_stmt.imports:
            consolidated[import_stmt.from_path].add(symbol)
    
    # Generate new import statements
    new_imports = generate_import_statements(consolidated)
    
    return {
        'imports': '\n'.join(new_imports),
        'validation': validation,
        'registry': ImportRegistry(
            imports=imports,
            path_aliases=path_aliases,
            file_directory=file_directory,
            ts_root_dir=ts_root_dir
        )
    }
