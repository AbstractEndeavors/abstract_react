from abstract_utilities import MIME_TYPES,os
def get_image_exts():
    return [ext.lower() for ext in list(MIME_TYPES.get('image').keys())]
def get_video_exts():
    return [ext.lower() for ext in list(MIME_TYPES.get('video').keys())]

