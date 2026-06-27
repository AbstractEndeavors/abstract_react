from .imports import *
def discover_videos(config: SiteConfig):
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

