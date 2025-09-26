from abstract_utilities import *
from typing import *
import json,glob
from pathlib import Path
def join_paths(*paths):
    if not paths:
        return ''
    cleaned_paths = [path for path in paths if path]
    if not cleaned_paths:
        return ''
    base_path = Path(cleaned_paths[0])
    for path in cleaned_paths[1:]:
        base_path = base_path / path
    return str(base_path)
def clean_duplicate_filename(file_path):
    basename = os.path.basename(file_path)
    filename,ext = os.path.splitext(basename)
    if filename.endswith(')') and '(' in filename:
        potential_number = filename.split('(')[-1][:-1]
        new_filename = filename[:-len(str(potential_number))+2]
        for char in potential_number:
            if not is_number(char):
                new_filename = filename
                break
    return new_filename
# 1) Extract “base” name (e.g. VideoDetails) and keep the extension
def get_base_name(path: str):
    basename = os.path.basename(path)
    name, ext = os.path.splitext(basename)
    # remove trailing “(123)” if present
    name = re.sub(r'\(\d+\)$', '', name)
    return name, ext

# 2) Find all files under `directory` whose filename is:
#    base + optional “(number)” + same extension.
def find_same_filenames(directory: str, file_path: str):
    base, ext = get_base_name(file_path)
    pattern = re.compile(rf'^{re.escape(base)}(?:\(\d+\))?{re.escape(ext)}$')
    matches = []
    for f in Path(directory).rglob(f'*{ext}'):
        if pattern.match(f.name):
            matches.append(str(f))
    return matches

# 3) Your “replace” routine just becomes:

def clean_duplicate_filename(file_path: str) -> str:
    """
    Given "/…/VideoDetails(2).ts" or "/…/VideoDetails.ts",
    return "VideoDetails" in either case.
    """
    basename = os.path.basename(file_path)
    name, _ext = os.path.splitext(basename)
    # if it ends with "(digits)", strip that off
    if name.endswith(')') and '(' in name:
        num = name[name.rfind('(')+1:-1]
        if num.isdigit():
            name = name[:name.rfind('(')]
    return name
def glob_search(directory,basename,ext=None):
    basenames = make_list(basename)
    found_paths = []
    exts = make_list(ext or [])
    for basename in basenames:
        split_filename,split_ext =os.path.splitext(basename)
        filename = split_filename or '*'
        exts = make_list(exts or split_ext or '*')
        for ext in exts:
            pattern = join_paths(directory, '**', f'{filename}{ext}')
            found_paths+=glob.glob(pattern, recursive=True)
    return found_paths
def convert_to_Server_doc(path,server_dir=None,local_server_dir=None):
    if isinstance(path,str):
        if server_dir and local_server_dir:
            path = path.replace(local_server_dir,server_dir)
    return path
def bulk_convert_to_server_docs(paths,server_dir=None,local_server_dir=None):
    if isinstance(paths,str):
        paths = paths.split('\n')
        for i,path in enumerate(paths):
           paths[i]= convert_to_Server_doc(path,server_dir=server_dir,local_server_dir=local_server_dir)
    return paths
def get_doc_content(file_path,server_dir=None,local_server_dir=None):
    server_doc = convert_to_Server_doc(file_path,server_dir=server_dir,local_server_dir=local_server_dir)
    if os.path.isfile(file_path):
        data = read_from_file(file_path)
        content = f"//{server_doc}\n{data}\n\n"
        return content
