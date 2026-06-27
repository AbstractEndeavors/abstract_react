"""
site-level config that the per-image info.json doesn't (and shouldn't) carry.

required at the call site so a misconfigured build fails immediately
rather than rendering pages with the wrong canonical host.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SiteConfig:
    root_url: str       # e.g. "https://thedailydialectics.com" — no trailing slash
    site_name: str      # e.g. "thedailydialectics"
    home_label: str = "Home"

    def __post_init__(self) -> None:
        if self.base_url.endswith("/"):
            # frozen dataclass — can't mutate, just yell.
            raise ValueError("SiteConfig.base_url must not have a trailing slash: %r" % self.base_url)
