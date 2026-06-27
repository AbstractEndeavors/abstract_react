from abstract_utilities import os,get_file_parts,eatOuter,eatAll
from .constants import MEDIA_DIR,ROOT_URL
from .init_imports import *
def is_filename_start_with(item,string):
   basename = os.path.basename(item)
   return basename.startswith(string)
def is_filename_starts_with_dirbase(item):
    file_parts = get_file_parts(item)
    dirbase = file_parts.get('dirbase')
    return is_filename_start_with(item,dirbase)
def path_to_url(path, media_root=MEDIA_DIR, site_root = ROOT_URL):
    return path.replace(MEDIA_DIR,ROOT_URL)
def create_out_path(rel_path):
    if not rel_path.startswith(MEDIA_DIR):
        return f"{eatOuter(MEDIA_DIR,'/')}/{eatAll(rel_path,'/')}"
    return rel_path
def print_item(item):
    for item_key in ITEM_KEYS:
        value = item.get(item_key)
        if value:
            print(item_key)
            print(item.get(item_key))
def print_items(items):
    for item in items:
        print_item(item)
def is_search_strings(values,search_strings):
    values = str(values)
    for search_string in search_strings:
        if search_string not in values:
            return False
    return True
# ---------------------------------------------------------------------------
# 3. SHARED UTILITIES — one copy, used everywhere
# ---------------------------------------------------------------------------

##def path_to_url(path, media_root=MEDIA_DIR, site_root = ROOT_URL):
##    """Convert an absolute filesystem path to a public URL."""
##    if not path:
##        return ""
##    real = os.path.realpath(str(path))
##    root_real = os.path.realpath(str(media_root))
##    if not real.startswith(root_real):
##        return ""
##    rel = real[len(root_real):].lstrip(os.sep)
##    return "%s/%s" % (site_root.rstrip("/"), rel.replace(os.sep, "/")) if rel else site_root.rstrip("/") + "/"
##
##
def url_to_path(url, media_root=MEDIA_DIR, site_root = ROOT_URL):
     """Convert a public URL back to a filesystem path, or None."""
     if not url or site_root not in url:
        return None
     rel = url.replace(site_root, "").lstrip("/")
     candidate = os.path.join(media_root, rel)
     return candidate if os.path.exists(candidate) else None


def safe_load_json(path):
    """Load JSON from path, return {} on any failure."""
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def safe_write_json(path, data):
    """Write JSON to path, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def safe_read_text(path):
    """Read text file, return '' on failure."""
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def safe_write_text(path, content):
    """Write text to path, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def humanize(name):
    """'some_slug-name' -> 'Some Slug Name'"""
    return name.replace("-", " ").replace("_", " ").strip().title()


def clean_text(value, max_len=160):
    """Collapse whitespace, truncate cleanly."""
    if isinstance(value, list):
        value = str(value[0]) if value else ""
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= max_len:
        return value
    return value[:max_len].rsplit(" ", 1)[0] + "…"


def xml_escape(value):
    return html_mod.escape(str(value), quote=True)


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


def breadcrumbs_html(url, site_root):
    """Generate breadcrumb HTML from a URL."""
    path_part = url.rstrip("/").replace(site_root, "").lstrip("/")
    segments = [s for s in path_part.split("/") if s]
    crumbs = ['<a href="%s">Home</a>' % site_root]
    acc = site_root
    for i, seg in enumerate(segments):
        acc += "/%s" % seg
        if i < len(segments) - 1:
            crumbs.append('<a href="%s/">%s</a>' % (acc, humanize(seg)))
        else:
            crumbs.append("<span>%s</span>" % seg)
    return " › ".join(crumbs)


def first_existing_file(*paths):
    """Return the first path that exists as a file, or ''."""
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return ""


def find_files_by_ext(root, exts, recursive=True):
    """Walk root and yield files matching any extension in exts."""
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        # sort for determinism
        for fname in sorted(filenames):
            if os.path.splitext(fname)[1].lower() in exts:
                yield os.path.join(dirpath, fname)
        if not recursive:
            break


def child_dirs(directory, skip_dirs):
    """List immediate child directories, excluding skip set and dotfiles."""
    if not os.path.isdir(directory):
        return []
    result = []
    for name in sorted(os.listdir(directory)):
        full = os.path.join(directory, name)
        if os.path.isdir(full) and name not in skip_dirs and not name.startswith("."):
            result.append(full)
    return result


def iso_date_from_mtime(path):
    """Return ISO date string from file mtime, or None."""
    if not path or not os.path.exists(path):
        return None
    return datetime.fromtimestamp(
        os.stat(path).st_mtime, tz=timezone.utc
    ).date().isoformat()
