from .imports import *
def normalize_keywords(raw, limit=12):
    """Deduplicate and cap a keyword list."""
    if isinstance(raw, str):
        raw = [k.strip() for k in raw.split(",") if k.strip()]
    if not isinstance(raw, list):
        return []
    seen = set()
    out = []
    for item in raw:
        k = str(item).strip()
        key = k.lower()
        if not k or key in seen or len(key) < 3:
            continue
        seen.add(key)
        out.append(k)
        if len(out) >= limit:
            break
    return out
def discover_images(config: SiteConfig):
    """
    Yield one record per image leaf directory.
    Expected layout:
        {slug}/{slug}.webp (or .jpg/.png)
        {slug}/info.json
        {slug}/index.html
    """
    dirs,files = get_files_and_dirs(config.imgs_dir,allowed_exts=['.json'])
    info_paths = [file for file in files if file.endswith('info.json')]
    
    for info_path in info_paths:
        correct_urls(info_path)
        html_path = info_path.replace('info.json', "index.html")
        img_dir = os.path.dirname(info_path)
        slug = os.path.basename(img_dir)
        img_path = get_best_image(img_dir)
        if img_path:
            img_base = os.path.splitext(os.path.basename(img_path))[0]
            if img_base != slug:
                continue

            

            info = safe_load_json(info_path)
            title = info.get("title") or humanize(slug)
            description = clean_text(
                info.get("longdesc") or info.get("alt") or info.get("caption") or ""
            )
            keywords = normalize_keywords(info.get("keywords_str", ""))
            schema = info.get("schema") or {}
            thumb_path = first_existing_file(
                os.path.join(img_dir, f"{slug}_thumb.webp"),
                os.path.join(img_dir, f"{slug}_thumb.jpg"),
                os.path.join(img_dir, f"{slug}_resized.png"),
                img_path,  # the image is its own thumbnail by default
            )

            yield make_record(
                kind="image",
                slug=slug,
                dir_path=img_dir,
                title=title,
                description=description,
                keywords=keywords,
                source_path=img_path,
                html_path=html_path,
                info_path=info_path,
                thumbnail_path=thumb_path,   # <-- new
                info=info,
                schema=schema,
            )


def discover_videos(config):
    """
    Yield one record per video leaf directory.
    Expected layout:
        {slug}/{slug}.mp4
        {slug}/info.json
        {slug}/thumbnails/{slug}_frame_N.jpg
        {slug}/captions.srt
    """
    for vid_path in find_files_by_ext(config.videos_dir, set(config.video_exts)):
        vid_dir = os.path.dirname(vid_path)
        slug = os.path.basename(vid_dir)

        info_path = os.path.join(vid_dir, "info.json")
        html_path = os.path.join(vid_dir, "index.html")
        info = safe_load_json(info_path)

        title = clean_text(
            info.get("seo_title") or humanize(slug), 120
        )
        description = clean_text(
            info.get("seo_description") or info.get("summary") or "", 200
        )
        keywords = normalize_keywords(
            info.get("seo_tags")
            or info.get("keywords")
            or info.get("combined_keywords")
            or []
        )
        duration = info.get("duration_formatted", "")
        resolution = (info.get("file_metadata") or {}).get("resolution", "")

        # thumbnail
        thumb_dir = os.path.join(vid_dir, "thumbnails")
        thumb_path = ""
        if os.path.isdir(thumb_dir):
            pattern = "%s_frame_0.jpg" % slug
            candidate = os.path.join(thumb_dir, pattern)
            if os.path.isfile(candidate):
                thumb_path = candidate

        # fallback thumbnail from info.json
        if not thumb_path:
            raw_thumb = (info.get("thumbnail") or {}).get("file_path", "")
            if raw_thumb and os.path.isfile(raw_thumb):
                thumb_path = raw_thumb

        # poster
        poster_path = first_existing_file(
            os.path.join(vid_dir, "poster.jpg"),
            os.path.join(vid_dir, "poster.png"),
            os.path.join(vid_dir, "thumbnail.jpg"),
            os.path.join(vid_dir, "thumbnail.png"),
        )

        # captions
        captions_path = first_existing_file(
            os.path.join(vid_dir, "captions.srt"),
            os.path.join(vid_dir, "captions.vtt"),
        )

        yield make_record(
            kind="video",
            slug=slug,
            dir_path=vid_dir,
            title=title,
            description=description,
            keywords=keywords,
            source_path=vid_path,
            html_path=html_path,
            info_path=info_path,
            info=info,
            thumbnail_path=thumb_path,
            poster_path=poster_path,
            captions_path=captions_path,
            duration=duration,
            resolution=resolution,
        )


def discover_all(config):
    """Yield all media records across all types."""
    yield from discover_pdfs(config)
    yield from discover_images(config)
    yield from discover_videos(config)
