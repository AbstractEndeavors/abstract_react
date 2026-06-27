from .site_map_generation import *
from .imports import SiteConfig
# ---------------------------------------------------------------------------
# 8. MEDIA MAP GENERATION — explicit per-kind projections
# ---------------------------------------------------------------------------

def _project_common(rec: dict) -> dict:
    return {
        "kind": rec["kind"],
        "slug": rec["slug"],
        "title": rec["title"],
        "description": rec["description"],
        "keywords": rec["keywords"],
        "dir_url": rec["dir_url"],
        "source_url": rec["source_url"],
        "html_url": rec["html_url"],
        "canonical_url": rec["canonical_url"],
        "thumbnail_url": rec["thumbnail_url"],
    }


def _project_image(rec: dict) -> dict:
    info = rec.get("info") or {}
    entry = _project_common(rec)
    entry.update({
        "alt": info.get("alt", ""),
        "caption": info.get("caption", ""),
        "longdesc": info.get("longdesc", ""),
        "filename": info.get("filename", ""),
        "ext": info.get("ext", ""),
        "dimensions": info.get("dimensions") or {},
        "file_size": info.get("file_size", ""),
        "license": info.get("license", ""),
        "attribution": info.get("attribution", ""),
        "schema": info.get("schema") or {},
        "social_meta": info.get("social_meta") or {},
    })
    return entry


def _project_pdf(rec: dict) -> dict:
    entry = _project_common(rec)
    entry.update({
        "page_count": rec["page_count"],
        "pages": [
            {
                "page_number": p["page_number"],
                "html_url": p.get("html_url", ""),
                "image_url": p.get("image_url", ""),
                "thumb_url": p.get("thumb_url", ""),
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "keywords": p.get("keywords") or [],
            }
            for p in rec.get("pages") or []
        ],
    })
    return entry


def _project_video(rec: dict) -> dict:
    info = rec.get("info") or {}
    entry = _project_common(rec)
    entry.update({
        "duration": rec["duration"],
        "resolution": rec["resolution"],
        "poster_url": rec["poster_url"],
        "captions_url": rec["captions_url"],
        "file_metadata": info.get("file_metadata") or {},
    })
    return entry


_PROJECTORS = {
    "image": _project_image,
    "pdf": _project_pdf,
    "video": _project_video,
}

_KIND_TO_KEY = {"pdf": "pdfs", "image": "images", "video": "videos"}


def build_media_map(records: list[dict], config: SiteConfig) -> dict:
    grouped: dict[str, list[dict]] = {"pdfs": [], "images": [], "videos": []}

    for rec in records:
        kind = rec.get("kind", "")
        key = _KIND_TO_KEY.get(kind)
        projector = _PROJECTORS.get(kind)
        if key is None or projector is None:
            continue
        grouped[key].append(projector(rec))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root_url": config.root_url,
        "media_root": config.media_root,
        "counts": {k: len(v) for k, v in grouped.items()},
        **grouped,
    }


def write_media_map(records, config, output_path):
    """Write the media map JSON."""
    payload = build_media_map(records, config)
    safe_write_json(output_path, payload)
    return output_path
