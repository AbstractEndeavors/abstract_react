"""
registry: map relative-dir-path -> ImageEntry.

scanning is explicit (give it a root). nothing globals, nothing cached
across calls. if you want a singleton, build one at the call site.
"""
from __future__ import annotations
import json
import os
from typing import Dict, Iterator, Tuple

from .schema import ImageEntry

INFO_FILENAME = "info.json"


def iter_info_dirs(root: str) -> Iterator[Tuple[str, str]]:
    """yield (abs_dir, rel_dir) for every dir under root containing info.json."""
    root = os.path.abspath(root)
    for dirpath, _dirs, files in os.walk(root):
        if INFO_FILENAME in files:
            rel = os.path.relpath(dirpath, root)
            yield dirpath, rel


def load_entry(info_dir: str) -> ImageEntry:
    """load + validate a single info.json. raises on schema violations."""
    info_path = os.path.join(info_dir, INFO_FILENAME)
    with open(info_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ImageEntry.from_dict(data, source=info_path)


def build_registry(root: str) -> Dict[str, ImageEntry]:
    """
    walk root, return {rel_dir_posix: ImageEntry}.

    rel_dir is normalized to forward slashes so it's URL-shaped and stable
    across OS. duplicate keys are not possible because rel_dir is unique
    per directory.
    """
    reg: Dict[str, ImageEntry] = {}
    info_dirs = iter_info_dirs(root)
    
    for abs_dir, rel_dir in info_dirs:
        try:
            key = rel_dir.replace(os.sep, "/")
            reg[key] = load_entry(abs_dir)
        except:
            pass
    return reg
