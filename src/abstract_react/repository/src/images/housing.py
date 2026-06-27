import os
import re
import shutil
import json
from .imports import *
# ---------- pure: name -> clean slug ---------------------------------------

_RESIZED_RE = re.compile(r'(_resized)+$')

def slugify_filename(name: str) -> str:
    """
    Filename (no ext) -> clean slug.
    Pure function. Same input always gives same output.
    """
    name = _RESIZED_RE.sub('', name)             # strip any number of _resized
    name = name.replace(',', '-').replace(' ', '-')
    name = re.sub(r'-{2,}', '-', name)           # collapse runs of dashes
    name = re.sub(r'\.-', '_', name)
    name = name.strip('-_')
    return name


# ---------- pure: image_path -> planned final location ---------------------

def plan_housing(image_path: str):
    """
    Returns a dict describing where this image should live.
    No filesystem mutation. Returns None if image is already housed correctly.
    """
    parent = os.path.dirname(image_path)
    base = os.path.basename(image_path)
    stem, ext = os.path.splitext(base)
    ext = ext.lower()

    slug = slugify_filename(stem)
    parent_basename = os.path.basename(parent)

    target_dir = os.path.join(parent, slug) if parent_basename != slug else parent
    target_image = os.path.join(target_dir, f"{slug}{ext}")
    target_info = os.path.join(target_dir, "info.json")

    already_housed = (
        os.path.abspath(image_path) == os.path.abspath(target_image)
        and os.path.isfile(target_info)
    )

    return {
        "src_image": image_path,
        "slug": slug,
        "ext": ext,
        "target_dir": target_dir,
        "target_image": target_image,
        "target_info": target_info,
        "already_housed": already_housed,
    }


# ---------- effectful: apply the plan, idempotently ------------------------

def apply_housing(plan: dict) -> str:
    """
    Move the image into its planned home and ensure info.json exists.
    Idempotent: safe to run repeatedly.
    Returns the final image path.
    """
    if plan["already_housed"]:
        return plan["target_image"]

    src = plan["src_image"]
    dst = plan["target_image"]
    target_dir = plan["target_dir"]

    if os.path.abspath(src) == os.path.abspath(dst):
        # already at target path, just ensure info.json
        _ensure_info_json(plan["target_info"])
        return dst

    if os.path.exists(dst):
        # another file already lives at the target name — refuse rather than snake
        raise FileExistsError(
            f"target already exists, refusing to overwrite: {dst} (source: {src})"
        )

    os.makedirs(target_dir, exist_ok=True)
    shutil.move(src, dst)
    _ensure_info_json(plan["target_info"])
    return dst


def _ensure_info_json(info_path: str) -> None:
    if os.path.isfile(info_path):
        return
    os.makedirs(os.path.dirname(info_path), exist_ok=True)
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)


# ---------- queue: walk root, plan, apply ----------------------------------

def find_loose_images(root: str, image_exts: tuple[str, ...]):
    """Yield every image under root. Filtering happens in plan_housing."""
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in image_exts:
                yield os.path.join(dirpath, fname)


def house_all_images(root: str, image_exts: tuple[str, ...], *, dry_run: bool = False):
    plans = (plan_housing(p) for p in find_loose_images(root, image_exts))
    for plan in plans:
        if plan["already_housed"]:
            continue
        if dry_run:
            print(f"WOULD: {plan['src_image']} -> {plan['target_image']}")
            continue
        try:
            final = apply_housing(plan)
            print(f"OK:    {plan['src_image']} -> {final}")
        except FileExistsError as e:
            print(f"SKIP:  {e}")
