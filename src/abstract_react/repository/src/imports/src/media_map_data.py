from .constants import MEDIA_MAP_PATH
from .init_imports import safe_load_from_json
def get_media_map_data():
    return safe_load_from_json(MEDIA_MAP_PATH)

