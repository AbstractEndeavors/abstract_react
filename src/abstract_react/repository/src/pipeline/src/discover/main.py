from .images import discover_images
from .pdfs import discover_pdfs
from .videos import discover_videos
# ---------------------------------------------------------------------------
# 4. DISCOVERY — find all media items under the media root
# ---------------------------------------------------------------------------
def discover_all(config):
    """Yield all media records across all types."""
    yield from discover_pdfs(config)
    yield from discover_images(config)
    yield from discover_videos(config)
