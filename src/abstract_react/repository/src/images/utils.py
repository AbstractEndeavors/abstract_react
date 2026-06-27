from .imports import *
def get_item_vars(item_type=None,search_strings=None):
    matching = []
    data = get_data()
    if search_strings != None:
        search_strings = make_list(search_strings)
    items = data.get(str(item_type))#[item for item in data if item.get('kind') == str(item_type)]
    if not item_type or not items:
        images = data.get('images')
        pdfs = data.get('pdfs')
        items = pdfs+images
    for item in items:
        
        if search_strings:
            
            if is_search_strings(item,search_strings):
                matching.append(item)
        else:
            matching.append(item)
    
    return matching
def fix_jsons():
    dirs,files = get_files_and_dirs(IMGS_DIR,allowed_exts=['.json'])
    files = [file for file in files if file.endswith('info.json')]
    for file in files:
        
        directory = os.path.dirname(file)
        get_images_from_dir(directory)
        index_path = os.path.join(directory,'index.html')
def write_image_htmls(fix_paths = False):
    site = SiteConfig(
    )
    env  = make_env(IMAGE_HTML_TEMPLATES)
    reg  = build_registry(MEDIA_DIR)
    for rel_dir, entry in reg.items():
        directory = os.path.join(MEDIA_DIR, rel_dir)
        info_path = os.path.join(directory,'info.json')
        if fix_paths:
            directory = fix_path(info_path)
            info_path = os.path.join(directory,'info.json')
        rel_dir = str(directory).replace(MEDIA_DIR,"")

        get_images_from_dir(directory)
        data = correct_urls(info_path) or entry
        out_dir = create_out_path(rel_dir)
        
        out_path = render_to_image_file(entry = entry, rel_dir = rel_dir, site=site, env=env,
                       out_dir=out_dir)
        if out_path:
            print(path_to_url(out_path))
