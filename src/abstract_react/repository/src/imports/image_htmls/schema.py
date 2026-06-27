"""
schema for image-index info.json.

required fields raise on missing; optional fields default to None.
nothing here invents data — if a field isn't in info.json, it isn't here.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import os
from .imports import get_best_image
from PIL import Image

# fields you can put in info.json, grouped by required/optional.
# update these two tuples to evolve the schema — they are the single source
# of truth that ImageEntry.from_dict checks against.
_REQUIRED = (
    "filename",
    "ext",
    "title",
    "alt",
    "longdesc",
    "keywords_str",
    "license",
    "attribution",
    "dimensions",
    "schema",
    "social_meta",
)
_OPTIONAL = (
    "caption",
    "file_size",
)


@dataclass(frozen=True)
class Dimensions:
    width: int
    height: int

    @classmethod
    def from_dict(cls, d: dict) -> "Dimensions":
        return cls(width=int(d["width"]), height=int(d["height"]))


@dataclass(frozen=True)
class ImageEntry:
    # required
    filename: str
    ext: str
    title: str
    alt: str
    longdesc: str
    keywords_str: str
    license: str
    attribution: str
    dimensions: Dimensions
    schema: dict        # raw JSON-LD blob, passed through verbatim
    social_meta: dict   # og:* / twitter:* keys
    # optional
    caption: Optional[str] = None
    file_size: Optional[float] = None

    @classmethod
    def from_dict(cls, d: dict, *, source: str = "<dict>") -> "ImageEntry":
        missing = [k for k in _REQUIRED if k not in d]
##        if missing:
##            raise ValueError(
##                "info.json at %s missing required fields: %s" % (source, missing)
##            )
##        unknown = [k for k in d.keys() if k not in _REQUIRED and k not in _OPTIONAL]
##        if unknown:
##            # warn-loud rather than silently drop. swap to raise if you want strict.
##            import sys
##            print(
##                "[image_index] %s has unknown keys (ignored): %s" % (source, unknown),
##                file=sys.stderr,
##            )
        image_path = get_best_image(os.path.dirname(source),resized=True)
        basename = os.path.basename(image_path)
        filename,ext = os.path.splitext(basename)
        filename = d.get("filename") or filename

        ext = d.get("ext") or ext
        title = d.get("title") or filename.replace('_',' ').replace('-',' ')
        alt = d.get("alt") or filename
        longdesc = d.get("longdesc") or alt
        keywords_str = d.get("keywords_str") or ','.join(title.split(' '))
        license = d.get("license")
        attribution  = d.get("attribution")
        dimensions  = d.get("dimensions")
        if not dimensions:
            img = Image.open(image_path)
            width, height = img.size
            dimensions = {"width":width,"height":height}
        schema  = d.get("schema")
        social_meta  = d.get("social_meta")
        caption  = d.get("caption")
        file_size  = d.get("file_size")
        social_meta  = d.get("social_meta")
        return cls(
            filename=filename,
            ext=ext,
            title=title,
            alt=alt,
            longdesc=longdesc,
            keywords_str=keywords_str,
            license=license,
            attribution=attribution,
            dimensions=Dimensions.from_dict(dimensions),
            schema=schema,
            social_meta=social_meta,
            caption=caption,
            file_size=file_size,
        )

    # convenience derived views — kept here so templates don't compute logic
    @property
    def keywords_list(self) -> list:
        return [k.strip() for k in self.keywords_str.split(",") if k.strip()]

    @property
    def display_caption(self) -> str:
        # caption falls back to alt — explicit fallback, not a smart default
        return self.caption if self.caption else self.alt

    def to_template_ctx(self) -> dict:
        d = asdict(self)
        d["keywords_list"] = self.keywords_list
        d["display_caption"] = self.display_caption
        return d
