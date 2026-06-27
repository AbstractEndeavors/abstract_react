from abstract_utilities import *
abs_dir = get_caller_dir()
PUBLIC_DIR = os.path.dirname(abs_dir)
media_map_path = os.path.join(PUBLIC_DIR,'media_map.json')
# Load lazily and defensively: doing this at import time crashed any consumer
# (e.g. `import abstract_pdfs`) whenever media_map.json was absent or PUBLIC_DIR
# resolved somewhere without one. Now it loads on first use and degrades to {}.
_DATA = None
def get_data():
    global _DATA
    if _DATA is None:
        try:
            _DATA = safe_load_from_json(media_map_path) or {}
        except Exception:
            _DATA = {}
    return _DATA
def print_item(item):
    item_keys = ['kind', 'title', 'dir_path', 'dir_url', 'pdf_path', 'pdf_url', 'html_path', 'html_url', 'metadata_path', 'thumbnail_url', 'canonical', 'page_count', 'pages']
    for item_key in item_keys:
        print(item_key)
        print(item.get(item_key))
def print_items(items):
    for item in items:
        print_item(item)
def get_item_vars(item_type=None,search_string=None):
    matching = []
    data = get_data()
    
    items = data.get(str(item_type))
    if not item_type or not items:
        images = data.get('images')
        pdfs = data.get('pdfs')
        items = pdfs+images
    for item in items:
        if search_string and search_string in str(item):
            matching.append(item)
    print_items(matching)
    return matching

def get_image_exts():
    return [ext.lower() for ext in list(MIME_TYPES.get('image').keys())]
def elim_ext(item):
    ext = get_img_ext(item)
    if ext:
        print(item)
        dirname = os.path.dirname(item)
        filename = get_filename(item)
        return os.path.join(dirname,filename)
        
def assure_single_ext(item):
    exts = get_image_exts()
    og_ext = get_img_ext(item)
    
    if og_ext:
        item = elim_ext(item)
        while True:
            nu_item = elim_ext(item)
            if not nu_item:
                item = f"{item}{og_ext}"
                break
            item = nu_item
    return item
def get_ext(item):
    if item:
        item_spl = os.path.splitext(item)
        if item_spl:
            return item_spl[-1]
def get_img_ext(item):
    if item and is_image(item):
        return get_ext(item)
def get_filename(item):
    if item and is_image(item):
        item_spl = os.path.splitext(item)
        if item_spl:
            return item_spl[0]
def is_image(item):
    IMAGE_EXTS = get_image_exts()
    ext = get_ext(item)
    ext_lower = ext.lower()
    return ext_lower in IMAGE_EXTS
def assure_and_save_single_ext(item):
    nu_item = assure_single_ext(item)
    if not os.path.isfile(nu_item):
        shutil.move(item,nu_item)
    return nu_item
def get_images_from_dir(directory):
    dirlist = os.listdir(directory)
    return [assure_and_save_single_ext(os.path.join(directory,image)) for image in dirlist if is_image(os.path.join(directory,image))]
def get_best_image(directory):
    images = get_images_from_dir(directory)
    web_ps = [image for image in images if image.endswith('.webp')]
    if web_ps:
        return web_ps[0]
    jpgs = [image for image in images if image.endswith('.jpg')]
    if jpgs:
        return jpgs[0]
    jpegs = [image for image in images if image.endswith('.jpeg')]
    if jpegs:
        return jpegs[0]
    pngs = [image for image in images if image.endswith('.png')]
    if pngs:
        return pngs[0]
def correct_json_urls(file_path,image_path):
    image_url = image_path.replace('/srv/media/thedailydialectics','https://thedailydialectics.com')
    data = safe_load_from_json(file_path)
    key_vals = [["schema","url"],["schema","contentUrl"],["social_meta","og:image"],["social_meta","twitter:image"]]
    for keys in key_vals:
        if keys[0] not in data:
           data[keys[0]] = {}
        data[keys[0]][keys[1]] = image_url
    
    safe_dump_to_json(data=data,file_path=file_path)
def correct_urls(file):
    directory = os.path.dirname(file)
    best_image = get_best_image(directory)
    if best_image:
        correct_json_urls(file,best_image)
