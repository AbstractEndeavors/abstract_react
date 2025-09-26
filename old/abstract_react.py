from abstract_webserver import *
from .utils import *
from .import_utils import *
from .replace_utils import *
def is_in_excluded_exts(file_path,excluded_exts):
    basename = os.path.basename(file_path)
    filename,ext = os.path.splitext(basename)
    if ext in excluded_exts:
        return True
    return False
def get_general_layout(item_paths=None,excluded_exts=None,server_dir=None,local_server_dir=None,include_site_view=False):
    excluded_exts = excluded_exts or []
    item_paths = [str(item_path) for item_path in item_paths]
    server_paths = bulk_convert_to_server_docs(item_paths)
    contents = ['']
    paths = ['']
    for i,item_path in enumerate(item_paths):
        item_path = str(item_path)
        server_path = server_paths[i]
        if is_in_excluded_exts(server_path,excluded_exts):
            path_only=True
            paths.append(server_path)
        else:
            data = get_doc_content(item_path)
            if data:
                contents.append(data)
    paths = '\n'.join(paths)
    contents = '\n'.join(contents)
    return paths+contents
def get_imports_and_content(react_file,tsconfig_path=None,excluded_exts=None,desired_exts=None,server_dir=None,local_server_dir=None,include_site_view=False):
    react_files = make_list(react_file)
    src_dir = find_src_dir(react_files[0])
    server_mgr = serverManager(src_dir=src_dir)
    tsconfig_path = tsconfig_path or glob_search(server_mgr.main_dir,'tsconfig',ext='.json')
    if tsconfig_path and isinstance(tsconfig_path,list):
        tsconfig_path = tsconfig_path[0]
    desired_exts = desired_exts or []
    excluded_exts = excluded_exts or []
    item_paths = set()
    for react_file in react_files:
        if react_file and (os.path.isdir(react_file) or not os.path.exists(react_file)):
            sub_react_files=None
            if os.path.isdir(react_file):
                sub_react_files =glob_search(react_file,ext=desired_exts or ['.tsx','.ts'])
            elif not os.path.exists(react_file):
                sub_react_files =glob_search(react_file,basename=react_file,ext=desired_exts)
            if sub_react_files:
                sub_react_files =make_list(sub_react_files)
                for sub_react_file in sub_react_files:
                    item_paths = get_imports(sub_react_file,tsconfig_path=tsconfig_path,seen=item_paths)
        else:
            item_paths = get_imports(react_file,tsconfig_path=tsconfig_path,seen=item_paths)
    if include_site_view:
        docs = [os.path.join(server_mgr.main_dir,item) for item in os.listdir(server_mgr.main_dir)]
        item_paths = item_paths+docs
    general_layout = get_general_layout(item_paths=item_paths,excluded_exts=excluded_exts,include_site_view=include_site_view)
    return general_layout



