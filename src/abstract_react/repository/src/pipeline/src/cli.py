from .orchestrator import *
from .imports import SiteConfig,make_tdd_config,write_image_htmls,PUBLIC_DIR,MEDIA_MAP_PATH
# ---------------------------------------------------------------------------
# 11. CLI
# ---------------------------------------------------------------------------
def run_unified_pipeline():

    import argparse

    p = argparse.ArgumentParser(description="Unified media pipeline for thedailydialectics")
    p.add_argument("--dry-run", action="store_true", default=False,
                   help="Print what would be done without writing")
    p.add_argument("--kinds", nargs="*", choices=["pdf", "image", "video"], default=None,
                   help="Only process these kinds (default: all)")
    p.add_argument("--no-sitemap", action="store_true", default=False)
    p.add_argument("--no-media-map", action="store_true", default=False)
    p.add_argument("--no-galleries", action="store_true", default=False)
    p.add_argument("--no-html", action="store_true", default=False)
    p.add_argument("--sitemap-dir",
                   default=PUBLIC_DIR)
    p.add_argument("--media-map-path",
                   default=MEDIA_MAP_PATH)
    args = p.parse_args()
    
    config = make_tdd_config()
    write_image_htmls()
    get_viewer_pages()
    run_pipeline(
        config=config,
        kinds=set(args.kinds) if args.kinds else None,
        write_html=not args.no_html,
        write_sitemap=not args.no_sitemap,
        write_media_map_flag=not args.no_media_map,
        write_galleries=not args.no_galleries,
        sitemap_output_dir=args.sitemap_dir,
        media_map_output_path=args.media_map_path,
        dry_run=args.dry_run,
    )
