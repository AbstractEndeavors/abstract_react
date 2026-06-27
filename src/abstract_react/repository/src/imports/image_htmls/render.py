"""
render an ImageEntry to HTML.

the env (jinja loader, site config) is passed in. nothing module-global.
"""
from __future__ import annotations
import json
import os
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .schema import ImageEntry
from .imports import *

def make_env(template_root: str) -> Environment:
    """build a jinja2 env rooted at the templates dir."""
    return Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(["html"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )


def build_breadcrumbs(rel_dir: str, site: SiteConfig) -> list:
    """
    given 'imgs/mems/micro-fluidics' produce a list of {label, href} pairs.
    last item has href=None — it's the current page.
    """
    parts = [p for p in rel_dir.split("/") if p]
    crumbs = [{"label": site.home_label, "href": site.root_url + "/"}]
    accum = ""
    for i, p in enumerate(parts):
        accum = (accum + "/" + p) if accum else "/" + p
        is_last = (i == len(parts) - 1)
        crumbs.append({
            "label": p.capitalize() if not is_last else p,
            "href": None if is_last else (site.root_url + accum + "/"),
        })
    return crumbs


def build_canonical_url(rel_dir: str, site: SiteConfig) -> str:
    return site.root_url + "/" + rel_dir.strip("/") + "/"


def render_entry(
    entry: ImageEntry,
    rel_dir: str,
    site: SiteConfig,
    env: Environment,
    *,
    template_name: str = "image_index/image_index_base.html",
    extra_ctx: Optional[dict] = None,
) -> str:
    """render one entry to a complete HTML string."""
    canonical_url = build_canonical_url(rel_dir, site)
    breadcrumbs = build_breadcrumbs(rel_dir, site)

    ctx = {
        "entry": entry.to_template_ctx(),
        "site": {
            "base_url": site.root_url,
            "site_name": site.site_name,
            "home_label": site.home_label,
        },
        "canonical_url": canonical_url,
        "breadcrumbs": breadcrumbs,
        "schema_json": json.dumps(entry.schema, indent=2),
    }
    if extra_ctx:
        ctx.update(extra_ctx)
    try:
        tmpl = env.get_template(template_name)
        return tmpl.render(**ctx)
    except:
        pass

def render_to_image_file(
    entry: ImageEntry,
    rel_dir: str,
    site: SiteConfig,
    env: Environment,
    out_dir: str,
    *,
    out_filename: str = "index.html",
    template_name: str = "image_index_base.html",
    extra_ctx: Optional[dict] = None,
) -> str:
    """render and write. returns the output path."""
    html = render_entry(entry, rel_dir, site, env,
                        template_name=template_name, extra_ctx=extra_ctx)
    if html:
        if not os.path.isdir(out_dir):
            
            os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, out_filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        return out_path

