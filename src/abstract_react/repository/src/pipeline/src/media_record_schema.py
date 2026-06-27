from .imports import *
# ---------------------------------------------------------------------------
# 2. MEDIA RECORD SCHEMA — one shape for everything
# ---------------------------------------------------------------------------

def make_record(
    kind,           # "pdf" | "image" | "video"
    slug,           # directory/file basename used as identifier
    dir_path,       # absolute path to the item's directory
    *,
    title="",
    description="",
    keywords=None,
    # paths on disk
    source_path="",       # the .pdf / .jpg / .mp4 file
    html_path="",         # generated index.html
    metadata_path="",     # metadata.json
    info_path="",         # info.json
    text_path="",         # text.txt (for pdfs/images)
    thumbnail_path="",
    thumbnail_resized_path="",
    poster_path="",       # videos
    captions_path="",     # videos
    # urls (computed)
    dir_url="",
    source_url="",
    html_url="",
    thumbnail_url="",
    thumbnail_resized_url="",
    poster_url="",
    captions_url="",
    canonical_url="",
    # structured data loaded from disk
    metadata=None,        # contents of metadata.json
    info=None,            # contents of info.json
    # children
    pages=None,           # list of page records (for pdfs)
    page_count=0,
    # extra
    schema=None,          # JSON-LD schema dict
    meta_bundle=None,     # resolved og/twitter/other meta
    duration="",
    resolution="",
):
    """
    Build a MediaRecord dict with all known fields.
    Explicit > implicit: every field is named, nothing is magic.
    """
    record = {
        "kind": kind,
        "slug": slug,
        "dir_path": dir_path,
        "title": title,
        "description": description,
        "keywords": keywords or [],
        "source_path": source_path,
        "html_path": html_path,
        "metadata_path": metadata_path,
        "info_path": info_path,
        "text_path": text_path,
        "thumbnail_path": thumbnail_path,
        "thumbnail_resized_path": thumbnail_resized_path,
        "poster_path": poster_path,
        "captions_path": captions_path,
        "dir_url": dir_url,
        "source_url": source_url,
        "html_url": html_url,
        "thumbnail_url": thumbnail_url,
        "thumbnail_resized_url": thumbnail_resized_url,
        "poster_url": poster_url,
        "captions_url": captions_url,
        "canonical_url": canonical_url,
        "metadata": metadata or {},
        "info": info or {},
        "pages": pages or [],
        "page_count": page_count,
        "schema": schema or {},
        "meta_bundle": meta_bundle or {},
        "duration": duration,
        "resolution": resolution,
    }

    return record


