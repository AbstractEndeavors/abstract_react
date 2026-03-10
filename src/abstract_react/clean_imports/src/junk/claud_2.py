from .claude import *


# === PARSE TS LINE TO SCHEMA ===
def parse_ts_line_to_schema(line_data: dict, line_index: int) -> ParsedLine:
    """Convert your existing line_map format to schema"""
    segments = []
    
    for map_entry in line_data.get('line_map', []):
        seg_type = map_entry['type']
        placement = map_entry['placement']
        text = line_data[seg_type][placement]
        
        segments.append(LineSegment(
            type=seg_type,
            text=text,
            placement=placement
        ))
    
    # Reconstruct raw strings
    raw_content = ''.join(line_data.get('content', []))
    raw_comments = ''.join(line_data.get('comments', []))
    
    return ParsedLine(
        segments=segments,
        raw_content=raw_content,
        raw_comments=raw_comments,
        line_index=line_index
    )

def parse_file_to_schema(file_path: str) -> List[ParsedLine]:
    """Parse entire file using your existing parser"""
    ts_lines = get_ts_lines(file_path=file_path)
    return [parse_ts_line_to_schema(line_data, i) for i, line_data in enumerate(ts_lines)]

# === IMPORT EXTRACTION WITH COMMENTS ===
def extract_import_from_parsed_line(parsed_line: ParsedLine) -> Optional[ImportStatement]:
    """Extract import statement from parsed line, preserving inline comments"""
    content = parsed_line.raw_content.strip()
    
    if not content.startswith('import'):
        return None
    
    # Check for inline comment
    trailing_comment = parsed_line.raw_comments if parsed_line.raw_comments else None
    
    # Parse import statement
    if ' from ' not in content:
        return None
    
    import_part, path_part = content.split(' from ', 1)
    from_path = path_part.strip().strip("';\"")
    
    # Extract imported symbols
    import_part = import_part.replace('import', '').strip()
    
    if import_part.startswith('{') and '}' in import_part:
        imports_str = import_part[import_part.find('{')+1:import_part.find('}')]
        imports = [imp.strip() for imp in imports_str.split(',')]
    elif import_part.startswith('* as '):
        imports = [import_part.replace('* as ', '').strip()]
    else:
        imports = [import_part.strip()]
    
    is_relative = from_path.startswith('.') or from_path.startswith('..')
    
    return ImportStatement(
        raw_line=content,
        imports=imports,
        from_path=from_path,
        is_relative=is_relative,
        line_index=parsed_line.line_index,
        trailing_comment=trailing_comment
    )

# === SECTION PARTITIONING ===
def partition_file_sections(parsed_lines: List[ParsedLine]) -> Tuple[FileSection, List[FileSection]]:
    """Partition file into import section and code sections
    
    Returns: (import_section, code_sections)
    """
    import_lines = []
    code_lines = []
    in_import_section = False
    import_start = None
    import_end = None
    
    for parsed_line in parsed_lines:
        content = parsed_line.raw_content.strip()
        
        # Check if this is an import line
        is_import = content.startswith('import')
        
        if is_import:
            if not in_import_section:
                in_import_section = True
                import_start = parsed_line.line_index
            import_lines.append(parsed_line)
            import_end = parsed_line.line_index
        else:
            # Check if we've left the import section
            if in_import_section and content:  # Non-empty, non-import line
                in_import_section = False
            
            if not in_import_section:
                code_lines.append(parsed_line)
    
    import_section = FileSection(
        type='import',
        lines=import_lines,
        start_index=import_start if import_start is not None else 0,
        end_index=import_end if import_end is not None else 0
    )
    
    code_section = FileSection(
        type='code',
        lines=code_lines,
        start_index=import_end + 1 if import_end is not None else 0,
        end_index=len(parsed_lines) - 1
    )
    
    return import_section, [code_section]

# === IMPORT CONSOLIDATION (from previous code) ===
def consolidate_imports_with_comments(imports: List[ImportStatement], file_directory: str,
                                     ts_root_dir: str, path_aliases: Dict[str, PathAlias]) -> Dict[str, dict]:
    """Consolidate imports preserving important comments
    
    Returns: {path: {'symbols': set(), 'comments': []}}
    """
    consolidated = defaultdict(lambda: {'symbols': set(), 'comments': []})
    
    for import_stmt in imports:
        # Try to convert to alias path
        alias_path = convert_to_alias_path(import_stmt, file_directory, ts_root_dir, path_aliases)
        target_path = alias_path if alias_path else import_stmt.from_path
        
        # Add symbols
        for symbol in import_stmt.imports:
            consolidated[target_path]['symbols'].add(symbol)
        
        # Preserve meaningful comments
        if import_stmt.trailing_comment:
            comment = import_stmt.trailing_comment.strip()
            if comment and not comment.startswith('//'):
                comment = '// ' + comment
            consolidated[target_path]['comments'].append(comment)
    
    return consolidated

def generate_import_statements_with_comments(consolidated: Dict[str, dict]) -> List[str]:
    """Generate import statements with preserved comments"""
    import_lines = []
    
    for path in sorted(consolidated.keys()):
        data = consolidated[path]
        symbols = sorted(data['symbols'])
        comments = data['comments']
        
        # Generate import statement
        if len(symbols) == 1:
            import_line = f"import {{ {symbols[0]} }} from '{path}';"
        else:
            symbols_str = ', '.join(symbols)
            import_line = f"import {{ {symbols_str} }} from '{path}';"
        
        # Add consolidated comment if exists
        if comments:
            unique_comments = list(dict.fromkeys(comments))  # Preserve order, remove dupes
            if len(unique_comments) == 1:
                import_line += f" {unique_comments[0]}"
            else:
                # Multiple comments - add them above
                for comment in unique_comments:
                    import_lines.append(comment)
                import_lines.append(import_line)
                continue
        
        import_lines.append(import_line)
    
    return import_lines

# === RECONSTRUCTION QUEUE ===
def reconstruct_line(parsed_line: ParsedLine) -> str:
    """Reconstruct line from segments preserving comment positions"""
    return ''.join(segment.text for segment in parsed_line.segments)

def build_reconstruction_queue(file_path: str, directory: str) -> ReconstructionQueue:
    """Build queue for file reconstruction"""
    # Parse file
    parsed_lines = parse_file_to_schema(file_path)
    
    # Partition sections
    import_section, code_sections = partition_file_sections(parsed_lines)
    
    # Setup environment
    ts_root_dir = get_ts_config_root_dir(directory=directory)
    file_directory = os.path.dirname(file_path)
    path_aliases = build_path_alias_registry(directory=directory)
    
    # Extract imports
    imports = []
    for parsed_line in import_section.lines:
        import_stmt = extract_import_from_parsed_line(parsed_line)
        if import_stmt:
            imports.append(import_stmt)
    
    # Consolidate
    consolidated = consolidate_imports_with_comments(
        imports, file_directory, ts_root_dir, path_aliases
    )
    
    # Generate new imports
    new_imports = generate_import_statements_with_comments(consolidated)
    
    return ReconstructionQueue(
        import_section=import_section,
        code_sections=code_sections,
        new_imports=new_imports,
        file_path=file_path
    )

def execute_reconstruction(queue: ReconstructionQueue) -> str:
    """Execute reconstruction from queue"""
    output_lines = []
    
    # Add new consolidated imports
    output_lines.extend(queue.new_imports)
    output_lines.append('')  # Blank line after imports
    
    # Add all code sections, preserving comments
    for section in queue.code_sections:
        for parsed_line in section.lines:
            reconstructed = reconstruct_line(parsed_line)
            output_lines.append(reconstructed)
    
    return '\n'.join(output_lines)

# === MAIN WORKFLOW ===
def process_file_preserve_comments(file_path: str, directory: str, 
                                   write_back: bool = False) -> dict:
    """Main workflow: consolidate imports while preserving comments
    
    Args:
        file_path: Path to file
        directory: Project directory  
        write_back: If True, write changes back to file
    
    Returns:
        {
            'original': str,
            'processed': str,
            'queue': ReconstructionQueue,
            'written': bool
        }
    """
    # Read original
    original = read_from_file(file_path)
    
    # Build reconstruction queue
    queue = build_reconstruction_queue(file_path, directory)
    
    # Execute reconstruction
    processed = execute_reconstruction(queue)
    
    # Optionally write back
    written = False
    if write_back:
        write_to_file(file_path, processed)
        written = True
    
    return {
        'original': original,
        'processed': processed,
        'queue': queue,
        'written': written
    }

