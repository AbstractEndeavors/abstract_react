from .imports import *
from .schemas import *
def if_chars_in_line(string,chars=None):
    return_chars = []
    chars = chars or []
    for char in chars:
        if char in string:
            return_chars.append(char)
    return return_chars
def clean_string(string=None,chars=None,add=None):
    add = if_not_bool_default(add,True)
    chars = chars or []
    if add:
        chars += ['',' ','\n','\t']
    return eatAll(string,chars)
def count_chars(string,char):
    return len(string.split(char))
def get_contents(contents=None,file_path=None):
    if contents:
        if os.path.isfile(contents):
            file_path = contents
            contents=None
    return contents or read_from_file(file_path)
def get_lines(contents=None,file_path=None,clean=False,chars=None,add=None):
    contents = get_contents(contents=contents,file_path=file_path) or ""
    if clean:
        contents = clean_string(contents,chars=chars,add=add)
    contents_spl = contents.split('\n') or []
    if clean:
        contents_spl = [clean_string(content,chars=chars,add=add) for content in contents_spl]
    return contents_spl
def get_line_js():
    return {"content":[],"comments":[],"line_map":[]}
def get_first_in_string(string,chars=None):
    chars = chars or []
    shortest = [None,None]
    for char in chars:
        if char in string:
            init_length = len(string.split(char)[0])
            if init_length == 0:
                return char
            prev_shortest = shortest[0]
            if prev_shortest is None or prev_shortest > init_length:
                shortest=[init_length,char]
    return shortest[-1]
def get_shortest_char_length(chars_place):
    shortest = [None,None]
    for char,string_values in chars_place.items():
        length = None
        if string_values:
            length = len(string_values[0])
        prev_shortest = shortest[0]
        if length is not None and (prev_shortest is None or length < shortest):
            shortest = [length,char]
    return shortest[-1]
def is_chars_js_empty(chars_js):
    for key,value in chars_js.items():
        if value:
            return False
    return True
def popit(list_obj=None):
    list_obj = list_obj or []
    obj = None
    if list_obj:
        obj = list_obj[0]
        if len(list_obj) >1:
            list_obj = list_obj[1:]
        else:
            list_obj=[]
    return obj,list_obj
def get_ordered_chars(string,chars=None):
    chars = chars or []
    chars_place = {}
    placement = []
    for char in chars:
        if char in string:
            chars_place[char] = string.split(char)
    while True:
        if is_chars_js_empty(chars_place):
            return placement
        char = get_shortest_char_length(chars_place)
        placement.append(char)
        part,chars_place[char] = popit(chars_place[char])

    return placement
def get_comments(contents=None,file_path=None,clean=False,chars=None,add=None):
    contents = get_contents(contents=contents,file_path=file_path) or ""
    lines = get_lines(contents=contents,file_path=file_path,clean=clean,chars=chars,add=add)
    for line in lines:
        line_js = get_line_js()
        chars_in_line = if_chars_in_line(line,['//','/*','*/'])
        chars_in_line = get_ordered_chars(line,chars=chars_in_line)
        nuline = line
        for char in chars_in_line:
            if char == '//' or (char == '/*' and '*/' not in line):
                line_js['line_map'].append({"type":'content',"placement":len(line_js['content'])})
                line_spl = nuline.split(char)
                line_js['content'].append(line_spl[0])
                line_js['line_map'].append({"type":'comments',"placement":len(line_js['comments'])})
                line_js['comments'].append(char.join(line_spl[1:]))
                break
            elif char in ['/*','*/']:
                if char == '/*':
                    line_spl = nuline.split(char)
                    line_js['content'].append(line_spl[0])
                    line_js['line_map'].append({"type":'content',"placement":len(line_js['content'])})
                    nuline = char.join(line_spl[1:])
                      
                line_js['line_map'].append({"type":'content',"placement":len(line_js['content'])})
                line_spl = nuline.split(char)
def get_java_split(contents=None,file_path=None):
    contents = get_contents(contents=contents,file_path=file_path) or ""
    return contents.split(';') or []
def get_java_lines(contents=None,file_path=None,clean=False,chars=None,add=None):
    java_split = get_java_split(contents=contents,file_path=file_path)
    return [get_lines(contents=content,clean=clean,chars=chars,add=add) for content in java_split]
    
def gather_imports(contents=None,file_path=None):
    contents = get_contents(contents=contents,file_path=file_path)
def compile_script_from_parse(java_lines):
    lines = [' '.join(java_line) for java_line in java_lines if java_line]
    return ';'.join(lines)
    
def get_import_path(relative_import, file_path=None, directory=None):
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
def get_spec_file_path(filename,directory=None):
    file_paths = find_files(filename,directory=directory)
    return get_single_from_list(file_paths)
def get_ts_config_path(directory=None):
    return get_spec_file_path('tsconfig',directory=directory)
def get_ts_config_data(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return safe_load_from_file(ts_config_path)
def get_ts_config_root_dir(directory=None):
    ts_config_path = get_ts_config_path(directory=directory)
    if ts_config_path:
        return os.path.dirname(ts_config_path)
def get_ts_config_compilerOptions(data=None,directory=None):
    if not data:
        data = get_ts_config_data(directory=directory)
    data = data or {}
    return data.get('compilerOptions') or {}
def get_ts_config_paths(data=None,directory=None):
    data = get_ts_config_compilerOptions(data=data,directory=directory) or {}
    return data.get('paths') or {}
def if_stared(path_config):
    path_config= path_config or ''
    return path_config.endswith('*')
class TSState:
    CODE = "code"
    LINE_COMMENT = "line_comment"
    BLOCK_COMMENT = "block_comment"
    STRING_SINGLE = "string_single"
    STRING_DOUBLE = "string_double"
    TEMPLATE = "template"
    REGEX = "regex"
def partition_ts_line(line, state=TSState.CODE):
    out = {"content": [], "comments": [], "line_map": []}
    buf = ""
    i = 0

    def flush(kind):
        nonlocal buf
        if buf:
            out[kind].append(buf)
            out["line_map"].append({
                "type": kind,
                "placement": len(out[kind]) - 1
            })
            buf = ""

    while i < len(line):
        c = line[i]
        n = line[i + 1] if i + 1 < len(line) else ""

        if state == TSState.CODE:
            if c == "/" and n == "/":
                flush("content")
                state = TSState.LINE_COMMENT
                buf = "//"
                i += 2
                continue
            if c == "/" and n == "*":
                flush("content")
                state = TSState.BLOCK_COMMENT
                buf = "/*"
                i += 2
                continue
            if c == '"':
                buf += c
                state = TSState.STRING_DOUBLE
            elif c == "'":
                buf += c
                state = TSState.STRING_SINGLE
            elif c == "`":
                buf += c
                state = TSState.TEMPLATE
            else:
                buf += c

        elif state == TSState.LINE_COMMENT:
            buf += c

        elif state == TSState.BLOCK_COMMENT:
            buf += c
            if c == "*" and n == "/":
                buf += "/"
                i += 1
                flush("comments")
                state = TSState.CODE

        elif state == TSState.STRING_DOUBLE:
            buf += c
            if c == '"' and line[i - 1] != "\\":
                state = TSState.CODE

        elif state == TSState.STRING_SINGLE:
            buf += c
            if c == "'" and line[i - 1] != "\\":
                state = TSState.CODE

        elif state == TSState.TEMPLATE:
            buf += c
            if c == "`" and line[i - 1] != "\\":
                state = TSState.CODE

        i += 1

    # finalize
    if state == TSState.LINE_COMMENT:
        flush("comments")
        state = TSState.CODE
    else:
        flush("content" if state == TSState.CODE else "comments")

    return out, state
def get_ts_lines(contents=None,file_path=None):
    contents = get_contents(contents=contents,file_path=file_path)
    lines = get_lines(contents)
    return partition_ts_file(lines)

def partition_ts_file(lines):
    state = TSState.CODE
    result = []

    for line in lines:
        parsed, state = partition_ts_line(line, state)
        result.append(parsed)

    return result
def get_ts_line(ts_lines,ts_line=None,i=None):
    line = None
    if ts_line or (i is not None and len(ts_lines)>i):
        return ts_line or ts_lines[i]
def get_line_map(ts_lines,ts_line=None,i=None):
    ts_line = ts_line or get_ts_line(ts_lines,ts_line=None,i=None)
    return ts_line.get('line_map')
def get_line_contents(ts_lines,ts_line=None,line_map=None,line_contents=None,i=None,j=None,spec=None):
    line_map = line_map or get_line_map(ts_lines,ts_line=ts_line,i=i)
    if line_contents or (j is not None and len(line_map)>j):
        return line_contents or line_map[j]
def get_line_content(ts_lines,ts_line=None,line_map=None,line_contents=None,type_content=None,i=None,j=None,k=None,spec=None):
    ts_line = get_ts_line(ts_lines,ts_line=ts_line,i=i)
    line_contents = line_contents or get_line_contents(ts_lines,ts_line=ts_line,line_map=line_map,line_content=line_content,i=i,j=j)
    typ = line_contents.get('type')
    k = k or line_contents.get('placement')
    type_contents = ts_line.get(typ)
    if (type_content or (k is not None and len(type_contents)>k)) and (not spec or (spec and typ == spec)):
        type_content = type_content or type_contents[k]
        return type_content

def get_specless_lines(script_path,spec=None):
    lines = []
    ts_lines = get_ts_lines(script_path)
    for i,ts_line in enumerate(ts_lines):
        line_map = ts_line.get('line_map')
        line=''
        for j,line_contents in enumerate(line_map):
            typ = line_contents.get('type')
            if not spec or (spec and typ != spec) :
                k = line_contents.get('placement')
                line += ts_line.get(typ)[k]
        lines.append(line)
    return lines
def is_header(string,headers=None):
    headers = make_list(headers or ['import','export','async','function'])
    cleaned_string = clean_string(string)
    cleaned_string.startswith(headers)
def get_spec_line(line_content):
    line_map = line_content.get('line_map')
    line=''
    for line_content in line_map:
        typ = line_content.get('type')
        if not spec or (spec and typ != spec) :
            i = line_content.get('placement')
            line += ts_line.get(typ)[i]
def get_imports(script_path=None,data=None,spec=None):
    spec = 'content'
    
    return_contents = []
    ts_lines = get_ts_lines(script_path) or {}
    for i,ts_line in enumerate(ts_lines):
        import_string = False
        line_map = ts_line.get('line_map')
        for j,line_contents in enumerate(line_map):
            line = get_line_content(ts_lines,ts_line=ts_line,line_map=line_map,line_contents=line_contents,i=i,j=j,spec='content')
         
            if import_string == False and cleaned_string:
                if is_header(line,headers='import'):
                    import_string=True
            if import_string:
                return_content.append(line_content)
    return return_content
        
            
def get_commentless_lines(script_path):
    lines = get_specless_lines(script_path,spec="comments")
    return '\n'.join(lines)
def get_contentless_lines(script_path):
    lines = get_specless_lines(script_path,spec="content")
    return '\n'.join(lines)
