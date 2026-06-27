"""
Site-wide configuration.

One dataclass, explicit fields, no module-level side effects.
Consumers receive a SiteConfig instance — they never reach into globals.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from .exts import *

# ---------------------------------------------------------------------------
# Image extensions — inlined so config.py has zero exotic deps
# ---------------------------------------------------------------------------
IMAGE_EXTS = get_image_exts()

SKIP_DIRS = frozenset({
    "text", "pages", "images", "thumbnails", "pdf_pages","0000",
    "preprocessed_images", "preprocessed_text",
    "node_modules", ".git", "__pycache__",
})

IMAGE_CANDIDATES = ["image.webp", "image.png", "image.jpg", "image.jpeg"]


@dataclass(frozen=True)
class SiteConfig:
    """Immutable bag of every path / URL the pipeline needs."""

    site_name:   str = SITE_NAME
    domain:      str = DOMAIN
    root_url:    str = ROOT_URL

    # derived EXTS
    video_exts   tuple = get_video_exts()
    image_exts   tuple = get_image_exts()
    # derived URL prefixes
    imgs_url:    str = IMGS_URL
    pdfs_url:    str = PDFS_URL

    # local filesystem roots
    root_dir:    str = ROOT_DIR
    media_root:  str = MEDIA_DIR
    videos_root:  str = VIDEOS_DIR
    
    # sub-dirs (computed in __post_init__)
    imgs_dir:    str = IMGS_DIR
    pdfs_dir:    str = PDFS_DIR
    pages_dir:   str = PAGES_DIR
    videos_dir:   str = VIDEOS_DIR
    media_pages_dir: str = MEDIA_PAGES_DIR

    image_exts:  tuple = tuple(IMAGE_EXTS)
    skip_dirs:   frozenset = SKIP_DIRS

    def __post_init__(self):
        # frozen=True requires object.__setattr__ for computed fields
        _set = object.__setattr__
        _set(self, "imgs_url",  f"{self.root_url}/imgs")
        _set(self, "pdfs_url",  f"{self.root_url}/pdfs")
        _set(self, "imgs_dir",  os.path.join(self.media_root, "imgs"))
        _set(self, "pdfs_dir",  os.path.join(self.media_root, "pdfs"))
        _set(self, "videos_dir",  os.path.join(self.media_root, "videos"))
        _set(self, "pages_dir", os.path.join(self.root_dir, "pages"))
        _set(self, "media_pages_dir", os.path.join(self.media_root, "pages"))


# ---------------------------------------------------------------------------
# Default instance — importable, but never mutated
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = SiteConfig()
