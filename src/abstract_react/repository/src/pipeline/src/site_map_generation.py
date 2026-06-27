from .process_registry import *
from .imports import dataclass,os
# ---------------------------------------------------------------------------
# 7. SITEMAP GENERATION — from enriched records
# ---------------------------------------------------------------------------

@dataclass
class SitemapUrl:
    loc: str
    lastmod: str = ""
    changefreq: str = ""
    priority: str = ""


def infer_changefreq_and_priority(url):
    """Assign changefreq/priority based on URL path prefix."""
    path = url.split("://", 1)[-1]
    path = "/" + path.split("/", 1)[1] if "/" in path else "/"
    clean = path.strip("/")
    if clean == "":
        return "daily", "1.0"
    if clean.startswith("pdfs"):
        return "weekly", "0.9"
    if clean.startswith("imgs"):
        return "weekly", "0.8"
    if clean.startswith("videos"):
        return "weekly", "0.8"
    return "monthly", "0.7"


def records_to_sitemap_urls(records, config):
    """Convert enriched records into deduplicated SitemapUrl list."""
    seen = {}
    for rec in records:
        loc = rec.get("canonical_url") or rec.get("dir_url", "")
        if not loc:
            continue

        changefreq, priority = infer_changefreq_and_priority(loc)

        # best lastmod: html file mtime, then source file mtime
        lastmod = (
            iso_date_from_mtime(rec.get("html_path"))
            or iso_date_from_mtime(rec.get("metadata_path"))
            or iso_date_from_mtime(rec.get("source_path"))
            or ""
        )

        entry = SitemapUrl(loc=loc, lastmod=lastmod, changefreq=changefreq, priority=priority)

        existing = seen.get(loc)
        if existing is None or (entry.lastmod or "") > (existing.lastmod or ""):
            seen[loc] = entry

    return sorted(seen.values(), key=lambda x: x.loc)


def render_sitemap_xml(urls):
    """Render a list of SitemapUrl into sitemap XML."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in urls:
        if not url.loc:
            continue
        lines.append("  <url>")
        lines.append("    <loc>%s</loc>" % xml_escape(url.loc))
        if url.lastmod:
            lines.append("    <lastmod>%s</lastmod>" % url.lastmod)
        if url.changefreq:
            lines.append("    <changefreq>%s</changefreq>" % url.changefreq)
        if url.priority:
            lines.append("    <priority>%s</priority>" % url.priority)
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def render_sitemap_index_xml(base_url, sitemap_names, output_dir):
    """Render a sitemap index XML."""
    today = datetime.now(timezone.utc).date().isoformat()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for name in sitemap_names:
        path = os.path.join(output_dir, name)
        lastmod = iso_date_from_mtime(path) or today
        lines.append("  <sitemap>")
        lines.append("    <loc>%s</loc>" % xml_escape(base_url.rstrip("/") + "/" + name))
        lines.append("    <lastmod>%s</lastmod>" % lastmod)
        lines.append("  </sitemap>")
    lines.append("</sitemapindex>")
    lines.append("")
    return "\n".join(lines)


def write_sitemaps(records, config, output_dir):
    """
    Write sitemap.xml (or split sitemaps + index) from records.
    Returns list of written file paths.
    """
    urls = records_to_sitemap_urls(records, config)
    os.makedirs(output_dir, exist_ok=True)
    written = []

    if len(urls) <= config.max_sitemap_urls:
        out_path = os.path.join(output_dir, "sitemap.xml")
        safe_write_text(out_path, render_sitemap_xml(urls))
        written.append(out_path)
        return written

    # split into chunks
    chunk_size = config.max_sitemap_urls
    sitemap_names = []
    for idx in range(0, len(urls), chunk_size):
        batch = urls[idx:idx + chunk_size]
        name = "sitemap-%d.xml" % (idx // chunk_size + 1)
        out_path = os.path.join(output_dir, name)
        safe_write_text(out_path, render_sitemap_xml(batch))
        written.append(out_path)
        sitemap_names.append(name)

    index_path = os.path.join(output_dir, "sitemap.xml")
    safe_write_text(
        index_path,
        render_sitemap_index_xml(config.root_url, sitemap_names, output_dir),
    )
    written.append(index_path)
    return written
