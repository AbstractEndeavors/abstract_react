from .utils import *
def get_new_backup_dir(backup_dir=None):
    backup_dir = backup_dir or join_paths(os.getcwd(),'backups')
    os.makedirs(backup_dir,exist_ok=True)
    new_dirbase = f"backup_{str(int(time.time()))}"
    new_backup_dir = join_paths(backup_dir,new_dirbase)
    return new_backup_dir
def create_sub_directories(file_path,directory):
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    dirnames = dirname.split('/')
    full_path = directory
    for part in dirnames:
        full_path = join_paths(full_path,part)
        os.makedirs(full_path,exist_ok=True)
    return join_paths(full_path,basename)
def get_src_relative_path(file_path,src_dir):
    return file_path.split(src_dir)[-1]
def create_sub_backups_dir(backup_dir,file_path,src_dir):
    sub_path = get_src_relative_path(file_path,src_dir)
    file_path = create_sub_directories(sub_path,backup_dir)
    return file_path
def save_to_backup_file(backup_dir,file_path,src_dir):
    os.makedirs(backup_dir,exist_ok=True)
    contents = read_from_file(file_path)
    new_file_path = create_sub_backups_dir(backup_dir,file_path,src_dir)
    write_to_file(contents =contents,file_path=new_file_path)
def save_to_back_replace(raw_file_path,file_path,backup_dir,src_dir):
    contents = read_from_file(raw_file_path)
    save_to_backup_file(backup_dir,file_path,src_dir)
    write_to_file(contents =contents,file_path=file_path)
def replace_react_files(src_dir: str, paths,backup_dir=None):
    """
    For each path in `paths`, clean off any "(n)" suffix, then
    find all files under src_dir whose name starts with that clean base.
    """
    # allow either a single string or a list
    if isinstance(paths, str):
        paths = paths.splitlines()
    paths = make_list(paths)
    new_backup_dir = get_new_backup_dir(backup_dir=backup_dir)
    for raw in paths:
        p = raw.strip()
        if not p:
            continue
        base = clean_duplicate_filename(p)
        found_paths = glob_search(src_dir,base,'.tsx')

        input(f'\nLooking for "{base}" → found {len(found_paths)}:')
        for fp in found_paths:
            save_to_back_replace(raw,fp,new_backup_dir,src_dir)
            print('  ', fp)
