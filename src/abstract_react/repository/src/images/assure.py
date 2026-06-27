from .imports import *
def correct_json_urls(file_path,image_path):
    image_url = image_path.replace('/srv/media/thedailydialectics','https://thedailydialectics.com')

    data = safe_load_from_json(file_path)
    key_vals = [["schema","url"],["schema","contentUrl"],["social_meta","og:image"],["social_meta","twitter:image"]]
    for keys in key_vals:
        if keys[0] not in data:
            data[keys[0]] = {}
        data[keys[0]][keys[1]] = image_url
    
    safe_dump_to_json(data=data,file_path=file_path)
    return data
def correct_urls(file,resized=False):
    directory = os.path.dirname(file)
    best_image = get_best_image(directory,resized=resized)
    if best_image:
        return correct_json_urls(file,best_image)
def correct_all_urls():
    dirs,files = get_files_and_dirs(IMAGE_DIR,allowed_exts=['.json'])
    info_paths = [item for item in files if item.endswith('info.json')]
    for info_path in info_paths:
        correct_urls(info_path,resized=True)
def assure_image_dir(image_path):
    file_parts = get_file_parts(image_path)
    dirname = file_parts.get('dirname')
    basename = file_parts.get('basename')
    filename = file_parts.get('filename')
    dirbase = file_parts.get('dirbase')
    if dirbase != filename:
        nu_dir = os.path.join(dirname,filename)
        if not os.path.isdir(nu_dir):
            os.makedirs(nu_dir,exist_ok=True)
            nu_image_path = os.path.join(nu_dir,basename)
            shutil.move(image_path,nu_image_path)
            image_path = nu_image_path
            file_parts = get_file_parts(image_path)
            dirname = file_parts.get('dirname')
            basename = file_parts.get('basename')
            filename = file_parts.get('filename')
            dirbase = file_parts.get('dirbase')
    info_path = os.path.join(dirname,'info.json')

def correct_resized_image(image_path):
    file_parts = get_file_parts(image_path)
    nu_dirname = file_parts.get('parent_dirname')
    nu_dirbase = file_parts.get('parent_dirbase')
    dirname = file_parts.get('dirname')
    dirbase = file_parts.get('dirbase')
    filename = file_parts.get('filename')
    if dirbase == filename:
        actual_file_name = filename.replace('resized_','')
        if nu_dirbase != actual_file_name:
            nu_dirnames = [os.path.join(nu_dirname,item) for item in os.listdir(nu_dirname) if item == actual_file_name]
            if nu_dirnames:
                nu_dirname = nu_dirnames[0]
        ext = file_parts.get('ext')
        nu_filename = f"{actual_file_name}_resized"
        nu_basename = f"{nu_filename}{ext}"
        nu_filepath = os.path.join(nu_dirname,nu_basename)
        shutil.move(image_path,nu_filepath)
        info_path = os.path.join(nu_dirname,'info.json')
        return correct_urls(info_path,resized=True)
def correct_resized_images(image_paths):
    for image_path in image_paths:
        correct_resized_image(image_path)
def correct_all_resized_images():
    dirs,files = get_files_and_dirs(IMAGE_DIR,allowed_exts=get_image_exts())
    image_paths = [file for file in files if os.path.basename(file).startswith('resized_')]
    correct_resized_images(image_paths)
