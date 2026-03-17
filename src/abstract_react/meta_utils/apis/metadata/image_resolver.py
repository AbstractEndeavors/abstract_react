from pathlib import Path
from PIL import Image
from abstract_webtools import *
_FORMAT_TO_MIME = {
    "JPEG": "image/jpeg",
    "PNG":  "image/png",
    "GIF":  "image/gif",
    "WEBP": "image/webp",
    "BMP":  "image/bmp",
    "TIFF": "image/tiff",
}


def get_image_info(path: str | None) -> dict:
    """Returns actual width, height, mime from the file. Safe defaults if anything fails."""
    out = {"width": "1200", "height": "627", "mime": "image/jpeg"}

    if not path or not Path(path).is_file():
        return out

    try:
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format or ""
        out["width"] = str(w)
        out["height"] = str(h)
        out["mime"] = _FORMAT_TO_MIME.get(fmt, "image/jpeg")
    except Exception:
        pass

    return out
def get_parsed_url(domain, **kwargs):
    parsed_url = dict(kwargs)
    post_variants = []
    # http / www
    http_www = get_http_www(domain)
    parsed_url.update(http_www)
    http = http_www.get('http')
    # basic domain pieces
    domain_paths = get_domain_paths(domain, http=http)
    if 'path' not in parsed_url:
        parsed_url['path']=[]
    parsed_url['path']+=domain_paths
    domain_name_ext = get_domain_name_ext(domain, http=http)
    parsed_url.update(domain_name_ext)

    domain_name = parsed_url.get('name',"") or ""
    domain = parsed_url.get('domain',"") or ""
        # tokenization
    tokenized_domain = tokenize_domain(domain)
    parsed_url["tokenized_domain"] = tokenized_domain
    app_name = " ".join(tokenized_domain)
    parsed_url["app_name"] = app_name
    

  


    
    # author / "i_url"
    parsed_url["author"] = f"@{domain_name.lower()}"
    parsed_url["i_url"] = f"{domain_name}://"

    # combine with domain
    # compute final title
    title = get_title(parsed_url)
    post_variants=[title,app_name,domain]
    variants = title_variants_from_domain(domain)
    base_variants = list(set([variant for variant in variants if variant not in post_variants]))
    # update the organized variants
    parsed_url["title_variants"] = get_all_title_variants(variants=base_variants,page=title,name=app_name,domain=domain)

    parsed_url["title"] = pad_or_trim(
        "title",
        string=title,
        title_variants=parsed_url["title_variants"],
        page=title,
        domain=domain,
        name = app_name
    )

    # get keywords
    keywords_info = get_keywords(parsed_url,page=title,domain=domain,name = app_name)
    parsed_url.update(keywords_info)

    keywords = parsed_url.get("keywords", [])

    # FINAL: longest→shortest list with TITLE first, DOMAIN second
    domain = parsed_url.get("domain")
    if domain:
        final_variants = [title, ]

        # remove title/domain from pool
        pool = set(keywords + variants)
        pool.discard(title)
        pool.discard(parsed_url.get("domain"))

        # sort longest → shortest
        final_variants += sort_longest_first(pool)

        parsed_url["title_variants"] = final_variants
   
    return parsed_url
