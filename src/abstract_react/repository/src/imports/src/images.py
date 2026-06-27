from abstract_utilities import MIME_TYPES,os
from .exts import *
def is_image(item):
    IMAGE_EXTS = get_image_exts()
    ext = os.path.splitext(item)[-1]
    ext_lower = ext.lower()
    return ext_lower in IMAGE_EXTS
def get_images_from_dir(directory):
    dirlist = os.listdir(directory)
    return [os.path.join(directory,image) for image in dirlist if is_image(image)]
def get_best_image(directory,resized=False):
    images = get_images_from_dir(directory)
    if resized:
        resizeds = [image for image in images if "_resized" in os.path.basename(image)]
        if resizeds:
            return resizeds[0]
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
