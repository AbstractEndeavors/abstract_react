from .gallery_index_generation import *
from .imports import *
# ---------------------------------------------------------------------------
# 10. ORCHESTRATOR — the single entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    config=None,
    kinds=None,               # None = all, or set of {"pdf", "image", "video"}
    write_html=True,
    write_sitemap=True,
    write_media_map_flag=True,
    write_galleries=True,
    sitemap_output_dir=None,
    media_map_output_path=None,
    gallery_roots=None,       # list of dirs to generate galleries for
    registry=None,            # optional ProcessorRegistry with custom handlers
    dry_run=False,
):
    """
    Discover -> Enrich -> Process -> Write sitemaps/media_map/galleries.

    This is the single motion that ties everything together.
    """
    if config is None:
        config = make_tdd_config()

    if sitemap_output_dir is None:
        sitemap_output_dir = config.output_root
    if media_map_output_path is None:
        media_map_output_path = os.path.join(config.output_root, "media_map.json")
    if gallery_roots is None:
        gallery_roots = [config.pdfs_dir, config.imgs_dir, config.videos_dir]

    # --- Discover ---
    print("=== DISCOVER ===")
    discoverers = {
        "pdf": discover_pdfs,
        "image": discover_images,
        "video": discover_videos,
    }
    if kinds:
        discoverers = {k: v for k, v in discoverers.items() if k in kinds}

    all_records = []
    for kind_name, discover_fn in discoverers.items():
        count = 0
        for record in discover_fn(config):
            all_records.append(record)
            count += 1
        print("  discovered %d %s records" % (count, kind_name))

    # --- Enrich ---
    print("=== ENRICH ===")
    for record in all_records:
        enrich_record(record, config)
    print("  enriched %d records" % len(all_records))

    # --- Process (custom handlers) ---
    if registry:
        print("=== PROCESS (custom handlers) ===")
        registry.process_all(all_records, config)

    # --- Write outputs ---
    if not dry_run:
        if write_sitemap:
            print("=== SITEMAP ===")
            paths = write_sitemaps(all_records, config, sitemap_output_dir)
            for p in paths:
                print("  wrote %s" % p)

        if write_media_map_flag:
            print("=== MEDIA MAP ===")
            write_media_map(all_records, config, media_map_output_path)
            print("  wrote %s" % media_map_output_path)

        if write_galleries:
            print("=== GALLERIES ===")
            for root in gallery_roots:
                if os.path.isdir(root):
                    generate_all_galleries(root, config)
    else:
        print("=== DRY RUN — skipping writes ===")
        print("  would write sitemap to %s" % sitemap_output_dir)
        print("  would write media_map to %s" % media_map_output_path)
        print("  would generate galleries under: %s" % gallery_roots)

    print("=== DONE === (%d total records)" % len(all_records))
    return all_records


from pathlib import Path
def get_viewer_pages():
    PDF_ROOT = "/srv/media/thedailydialectics/pdfs"
    pdf_paths = [str(p) for p in Path(PDF_ROOT).rglob("*.pdf")]
    pdf_url = None
    for pdf_path in pdf_paths:
        try:
            pdf_url = get_viewer_page(pdf_path)
        except Exception as e:
            print(f"{e}")
            pass
        print(pdf_url)
