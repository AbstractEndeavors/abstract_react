from .imports import *

def discover_pdfs(config: SiteConfig):
    """
    Yield one record per PDF directory.
    Expected layout:
        {slug}/{slug}.pdf
        {slug}/pages/0001/image.png, info.json, metadata.json, text.txt
        {slug}/meta/metadata.json
    """
    for pdf_path in find_files_by_ext(config.pdfs_dir, {".pdf"}):
        pdf_dir = os.path.dirname(pdf_path)
        slug = os.path.basename(pdf_dir)
        meta_path = os.path.join(pdf_dir, "meta", "metadata.json")
        html_path = os.path.join(pdf_dir, "index.html")

        metadata = safe_load_json(meta_path)
        title = metadata.get("title") or humanize(slug)
        description = clean_text(
            metadata.get("summary")
            or metadata.get("description")
            or "Read %s in image, text, or PDF view." % title
        )

        # discover pages
        pages_dir = os.path.join(pdf_dir, "pages")
        pages = []
        if os.path.isdir(pages_dir):
            for page_name in sorted(os.listdir(pages_dir)):
                page_dir = os.path.join(pages_dir, page_name)
                if not os.path.isdir(page_dir) or not page_name.isdigit():
                    continue
                page_num = int(page_name)
                page_image = first_existing_file(
                    os.path.join(page_dir, "image.webp"),
                    os.path.join(page_dir, "image.png"),
                    os.path.join(page_dir, "image.jpg"),
                    os.path.join(page_dir, "image.jpeg"),
                )
                page_thumb = first_existing_file(
                    os.path.join(page_dir, "image_627x1200.png"),
                    
                    os.path.join(page_dir, "resized_image.jpg"),
                    os.path.join(page_dir, "image.png"),
                    page_image,
                )
                page_info_path = os.path.join(page_dir, "info.json")
                page_meta_path = os.path.join(page_dir, "metadata.json")
                page_text_path = os.path.join(page_dir, "text.txt")
                page_html_path = os.path.join(page_dir, "index.html")

                page_info = safe_load_json(page_info_path)
                page_meta = safe_load_json(page_meta_path)

                page_keywords_raw = []
                kw_obj = page_info.get("keywords", {})
                if isinstance(kw_obj, dict):
                    page_keywords_raw = kw_obj.get("primary") or kw_obj.get("meta_keywords", "")
                    if isinstance(page_keywords_raw, str):
                        page_keywords_raw = [k.strip() for k in page_keywords_raw.split(",") if k.strip()]

                page_title = page_meta.get("title") or page_info.get("scope") or ""
                page_alt = page_meta.get("alt") or "%s page %s" % (slug, page_name)
                page_desc = page_meta.get("description") or clean_text(
                    safe_read_text(page_text_path) or page_alt
                )

                pages.append({
                    "page_number": page_num,
                    "page_name": page_name,
                    "dir_path": page_dir,
                    "image_path": page_image,
                    "thumb_path": page_thumb,
                    "html_path": page_html_path,
                    "info_path": page_info_path,
                    "metadata_path": page_meta_path,
                    "text_path": page_text_path,
                    "title": page_title,
                    "alt": page_alt,
                    "description": page_desc,
                    "keywords": normalize_keywords(page_keywords_raw),
                    "text": safe_read_text(page_text_path),
                    "info": page_info,
                    "metadata": page_meta,
                })

        # aggregate keywords from all pages
        all_kw = []
        for pg in pages:
            all_kw.extend(pg["keywords"])
        meta_kw = metadata.get("keywords") or []
        if isinstance(meta_kw, str):
            meta_kw = [k.strip() for k in meta_kw.split(",") if k.strip()]
        combined_kw = normalize_keywords(meta_kw + all_kw, limit=20)

        # thumbnail: first page thumb
        first_thumb = pages[0]["thumb_path"] if pages else ""

        yield make_record(
            kind="pdf",
            slug=slug,
            dir_path=pdf_dir,
            title=title,
            description=description,
            keywords=combined_kw,
            source_path=pdf_path,
            html_path=html_path,
            metadata_path=meta_path,
            thumbnail_path=first_thumb,
            metadata=metadata,
            pages=pages,
            page_count=len(pages),
        )


