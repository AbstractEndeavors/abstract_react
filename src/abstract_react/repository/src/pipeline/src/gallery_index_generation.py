from .media_map_generation import *
# ---------------------------------------------------------------------------
# 9. GALLERY INDEX GENERATION — directory-level gallery pages
# ---------------------------------------------------------------------------

def build_gallery_card(dir_path, config):
    """Build a card dict for a subdirectory, used in gallery pages."""
    slug = os.path.basename(dir_path)
    metadata = _load_dir_metadata(dir_path)
    title = metadata.get("title") or metadata.get("name") or humanize(slug)
    description = clean_text(
        metadata.get("description") or metadata.get("summary") or metadata.get("caption") or ""
    )
    image = _resolve_thumbnail_url(metadata, dir_path, config)
    keywords = normalize_keywords(metadata.get("keywords") or [], limit=8)
    child_count = len([
        f for f in os.listdir(dir_path) if not f.startswith(".")
    ]) if os.path.isdir(dir_path) else 0
    meta_text = "%d item%s" % (child_count, "s" if child_count != 1 else "")

    return {
        "title": title,
        "href": path_to_url(dir_path, config.media_root, config.root_url) + "/",
        "image": image,
        "description": description,
        "meta": meta_text,
        "tags": keywords,
        "kind": "dir",
    }


def _load_dir_metadata(directory):
    """Try multiple metadata file locations."""
    candidates = [
        os.path.join(directory, "metadata.json"),
        os.path.join(directory, "meta", "metadata.json"),
        os.path.join(directory, "info.json"),
        os.path.join(directory, "manifest.json"),
    ]
    for c in candidates:
        data = safe_load_json(c)
        if data:
            return data
    return {}


def _resolve_thumbnail_url(metadata, directory, config):
    """Resolve thumbnail from metadata fields or first image in dir."""
    candidates = [
        metadata.get("thumbnail_link"),
        metadata.get("thumbnail_url"),
        metadata.get("thumbnail_url_resized"),
        metadata.get("thumbnail_resized"),
        metadata.get("thumbnail"),
        (metadata.get("og") or {}).get("image"),
    ]
    
    for value in candidates:
        if not value:
            continue
        value = str(value).strip()
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if os.path.isabs(value) and os.path.exists(value):
            return path_to_url(value, config.media_root, config.root_url)
        local = os.path.join(directory, value)
        if os.path.exists(local):
            return path_to_url(local, config.media_root, config.root_url)

    # fallback: first image in dir
    for dirpath, _, filenames in os.walk(directory):
        for fname in sorted(filenames):
            if os.path.splitext(fname)[1].lower() in config.image_exts:
                return path_to_url(os.path.join(dirpath, fname), config.media_root, config.root_url)
    return ""


def render_gallery_page(directory, cards, config):
    """Render a gallery HTML page for a directory."""
    metadata = _load_dir_metadata(directory)
    title = metadata.get("title") or humanize(os.path.basename(directory))
    description = clean_text(
        metadata.get("description") or metadata.get("summary")
        or "Browse %s on %s. Contains %d entries." % (title, config.site_name, len(cards))
    )
    dir_url = path_to_url(directory, config.media_root, config.root_url)
    canonical = dir_url + "/"
    breadcrumbs = breadcrumbs_html(dir_url, config.root_url)
    thumbnail = _resolve_thumbnail_url(metadata, directory, config)
    keywords = normalize_keywords(metadata.get("keywords") or [], limit=12)
    keywords_str = ", ".join(keywords)

    cards_html_parts = []
    for card in cards:
        tags_html = ""
        if card.get("tags"):
            tags_inner = "".join(
                '<span class="card-tag">%s</span>' % xml_escape(t) for t in card["tags"][:8]
            )
            tags_html = '<div class="card-tags">%s</div>' % tags_inner

        if card.get("image"):
            image_html = '<img src="%s" alt="%s" loading="lazy">' % (
                xml_escape(card["image"]), xml_escape(card["title"])
            )
        else:
            image_html = '<div class="card-image-fallback">No Preview</div>'

        kind_badge = "Directory" if card.get("kind") == "dir" else "Page"

        cards_html_parts.append("""
    <a class="card" href="%s">
      <div class="card-media">
        %s
        <span class="card-kind">%s</span>
      </div>
      <div class="card-body">
        <div class="card-title">%s</div>
        <div class="card-desc">%s</div>
        %s
        <div class="card-meta">%s</div>
      </div>
    </a>""" % (
            xml_escape(card["href"]),
            image_html,
            kind_badge,
            xml_escape(card["title"]),
            xml_escape(card.get("description", "")),
            tags_html,
            xml_escape(card.get("meta", "")),
        ))

    cards_html = "\n".join(cards_html_parts)

    # meta tags
    meta_parts = [
        "<title>%s</title>" % xml_escape(title),
        '<meta name="description" content="%s">' % xml_escape(description),
    ]
    if keywords_str:
        meta_parts.append('<meta name="keywords" content="%s">' % xml_escape(keywords_str))
    meta_parts.append('<link rel="canonical" href="%s">' % xml_escape(canonical))
    if thumbnail:
        meta_parts.append('<meta property="og:image" content="%s">' % xml_escape(thumbnail))
    meta_parts.extend([
        '<meta property="og:title" content="%s">' % xml_escape(title),
        '<meta property="og:description" content="%s">' % xml_escape(description),
        '<meta property="og:url" content="%s">' % xml_escape(canonical),
        '<meta property="og:type" content="website">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % xml_escape(title),
        '<meta name="twitter:description" content="%s">' % xml_escape(description),
    ])
    if thumbnail:
        meta_parts.append('<meta name="twitter:image" content="%s">' % xml_escape(thumbnail))

    meta_html = "\n  ".join(meta_parts)

    return GALLERY_TEMPLATE % {
        "meta_html": meta_html,
        "breadcrumbs": breadcrumbs,
        "title": xml_escape(title),
        "description": xml_escape(description),
        "cards_html": cards_html,
    }


GALLERY_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  %(meta_html)s
  <style>
    :root {
      --bg: #0b0f14; --panel: #121821; --panel-2: #18212c;
      --text: #ebf2f8; --muted: #98a6b5; --accent: #6ab0ff;
      --border: #273241; --chip: #223041;
      --shadow: 0 12px 32px rgba(0,0,0,.28); --radius: 16px;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text);
                 font-family: Arial, Helvetica, sans-serif; }
    a { color: inherit; text-decoration: none; }
    .page { max-width: 1400px; margin: 0 auto; padding: 20px; }
    .crumbs { font-size: .88rem; color: var(--muted); margin-bottom: 18px; line-height: 1.5; }
    .crumbs a { color: var(--accent); }
    .hero { margin-bottom: 22px; padding: 18px 20px; border: 1px solid var(--border);
            border-radius: var(--radius); background: linear-gradient(180deg, var(--panel), var(--panel-2));
            box-shadow: var(--shadow); }
    .title { margin: 0 0 10px; font-size: 1.6rem; line-height: 1.3; }
    .description { margin: 0; color: var(--muted); max-width: 900px; line-height: 1.55; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
    .card { display: flex; flex-direction: column; min-width: 0; border: 1px solid var(--border);
            border-radius: 18px; overflow: hidden; background: var(--panel);
            box-shadow: var(--shadow); transition: transform .18s ease, border-color .18s ease; }
    .card:hover { transform: translateY(-2px); border-color: var(--accent); }
    .card-media { position: relative; background: #0f141b; min-height: 180px; }
    .card-media img { width: 100%%; height: 180px; object-fit: cover; display: block; }
    .card-image-fallback { min-height: 180px; display: grid; place-items: center;
                           color: var(--muted); font-size: .88rem; }
    .card-kind { position: absolute; top: 10px; right: 10px; background: rgba(11,15,20,.88);
                 border: 1px solid var(--border); color: var(--text); border-radius: 999px;
                 padding: 4px 8px; font-size: .72rem; }
    .card-body { padding: 14px; display: flex; flex-direction: column; gap: 8px; flex: 1; }
    .card-title { font-size: .98rem; font-weight: 700; line-height: 1.35; }
    .card-desc { font-size: .84rem; color: var(--muted); line-height: 1.5;
                 display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
                 overflow: hidden; min-height: 5em; }
    .card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .card-tag { background: var(--chip); border: 1px solid var(--border); border-radius: 999px;
                padding: 4px 8px; font-size: .72rem; color: var(--text); }
    .card-meta { margin-top: auto; font-size: .74rem; color: var(--muted); }
  </style>
</head>
<body>
  <div class="page">
    <nav class="crumbs">%(breadcrumbs)s</nav>
    <section class="hero">
      <h1 class="title">%(title)s</h1>
      <p class="description">%(description)s</p>
    </section>
    <section class="grid">
%(cards_html)s
    </section>
  </div>
</body>
</html>"""


def generate_gallery_for_dir(directory, config):
    """Build and write a gallery index.html for a single directory."""
    children = child_dirs(directory, config.skip_dirs)
    if not children:
        return None

    cards = [build_gallery_card(d, config) for d in children]
    html_content = render_gallery_page(directory, cards, config)
    out_path = os.path.join(directory, "index.html")
    safe_write_text(out_path, html_content)
    return out_path


def generate_all_galleries(root, config):
    """Walk the tree bottom-up and generate gallery pages."""
    dirs_to_process = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in config.skip_dirs and not d.startswith(".")
        ]
        dirs_to_process.append(dirpath)

    # bottom-up so child galleries exist before parent references them
    dirs_to_process.sort(key=lambda p: p.count(os.sep), reverse=True)

    written = []
    for d in dirs_to_process:
        result = generate_gallery_for_dir(d, config)
        if result:
            written.append(result)
            print("gallery: %s" % result)
    return written

