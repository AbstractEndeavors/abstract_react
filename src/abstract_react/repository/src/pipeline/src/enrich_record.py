from .imports import *
from .discover import *

# ---------------------------------------------------------------------------
# 5. ENRICHMENT — resolve URLs, fill computed fields
# ---------------------------------------------------------------------------

def enrich_record(record, config):
    """
    Fill in all URL fields and canonical URL from paths.
    Mutates record in place and returns it.
    """
    mr = config.media_root
    sr = config.root_url

    record["dir_url"] = path_to_url(record["dir_path"], mr, sr)
    record["source_url"] = path_to_url(record["source_path"], mr, sr)
    record["html_url"] = path_to_url(record["html_path"], mr, sr) if record["html_path"] else ""
    record["thumbnail_url"] = path_to_url(record["thumbnail_path"], mr, sr)
    record["thumbnail_resized_url"] = path_to_url(record["thumbnail_resized_path"], mr, sr)
    record["poster_url"] = path_to_url(record["poster_path"], mr, sr)
    record["captions_url"] = path_to_url(record["captions_path"], mr, sr)

    # canonical: prefer html_url, fallback to dir_url
    if not record["canonical_url"]:
        meta_canonical = record["metadata"].get("canonical", "")
        if meta_canonical and not meta_canonical.endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf")
        ):
            record["canonical_url"] = meta_canonical
        elif record["html_url"]:
            record["canonical_url"] = record["html_url"]
        else:
            record["canonical_url"] = record["dir_url"] + "/"

    # enrich page URLs for PDFs
    for page in record.get("pages", []):
        page["dir_url"] = path_to_url(page["dir_path"], mr, sr)
        page["image_url"] = path_to_url(page["image_path"], mr, sr)
        page["thumb_url"] = path_to_url(page["thumb_path"], mr, sr)
        page["html_url"] = path_to_url(page["html_path"], mr, sr)

    return record
