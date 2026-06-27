from .images import is_image
from abstract_utilities import is_number,os,shutil
def unresize(item):
    if '_resize' in item:
        if not is_image(item):
            return item.replace('_resized','')
        while True:
            if '_resized_resized' not in item:
                break
            item = item.replace('_resized_resized','_resized')
    return item
def parse_dates(item):
    nu_item= item
    parts = item.split('-')
    for i,part in enumerate(parts):
        if i == 0:
            nu_item = part
        else:
            if is_number(nu_item[-1]) and is_number(part[0]):
                nu_item = f"{nu_item}_{part}"
            else:
                nu_item = f"{nu_item}-{part}"
    return nu_item
def clean_item(item):
    unresized_item = unresize(item)
    nu_item = unresized_item.replace(',','-').replace(' ','-').replace('--','-').replace('.-','_')
    clean_item = parse_dates(nu_item)
    
    if item != clean_item:
        return clean_item
def clean_all_images(directory):
    images = get_images_from_dir(directory)
    for image in images:
        dirname = os.path.dirname(image)
        image_base = os.path.basename(image)
        clean_base = clean_item(image_base)
        if clean_base:
            clean_image = os.path.join(dirname,clean_base)
            shutil.move(image,clean_image)
def fix_path(item):
    items = [item for item in item.split('/') if item]
    items_len = len(items)
    for i,item in enumerate(items):
        if i == 0:
            full_path = f"/{item}"
        elif i != (items_len -1):
            
            cleanItem = clean_item(item)
            if cleanItem:
                nu_path = os.path.join(full_path,item)
                clean_path = os.path.join(full_path,cleanItem)
                shutil.move(nu_path,clean_path)
                full_path = clean_path
            else:
                
                full_path = os.path.join(full_path,item)
        else:
           clean_all_images(full_path)
           return full_path
    return item
