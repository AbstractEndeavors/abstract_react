from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class FieldResolver:
    name: str
    keys: list[str]
    derive: Callable[[dict], Any] | None = None
    required: bool = False


class ResolutionError(Exception):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"unresolvable fields: {missing}")


def resolve_domain(info: dict, resolvers: list[FieldResolver]) -> dict:
    resolved = dict(info)
    missing = []

    for r in resolvers:
        value = None
        for key in r.keys:
            value = resolved.get(key)
            if value is not None:
                break

        if value is None and r.derive is not None:
            value = r.derive(resolved)

        if value is None and r.required:
            missing.append(r.name)

        resolved[r.name] = value

    if missing:
        raise ResolutionError(missing)

    return resolved


# --- resolver declarations, order matters ---

META_RESOLVERS = [
    # 1. straight lookups first — no fallbacks, just populate the namespace
    FieldResolver("path",             ["path"]),
    FieldResolver("title",            ["title"]),
    FieldResolver("app_name",         ["app_name"]),
    FieldResolver("domain_name",      ["name"]),
    FieldResolver("tokenized_domain", ["tokenized_domain"]),

    # 2. any_domain: domain -> name -> app_name -> title
    FieldResolver(
        "any_domain",
        ["domain", "name", "app_name", "title"],
        required=True,
    ),

    # 3. title_variants: try both raw keys, then derive from any_domain
    #    this collapses your any_variants + title_variants + variants dance
    FieldResolver(
        "title_variants",
        ["title_variants", "variants"],
        derive=lambda r: (
            title_variants_from_domain(r["any_domain"])
            if r.get("any_domain")
            else None
        ),
    ),

    # 4. variants: prefer the raw "variants" key, fall back to resolved title_variants
    FieldResolver(
        "variants",
        ["variants"],
        derive=lambda r: r.get("title_variants"),
    ),

    # 5. full_url: any_domain, or first title variant
    FieldResolver(
        "full_url",
        ["any_domain"],
        derive=lambda r: (
            r["title_variants"][0]
            if r.get("title_variants")
            else None
        ),
        required=True,
    ),

    # 6. share_url: explicit key, or full_url
    FieldResolver(
        "share_url",
        ["share_url"],
        derive=lambda r: r.get("full_url"),
    ),

    # 7. canonical: always full_url
    FieldResolver(
        "canonical",
        [],
        derive=lambda r: r.get("full_url"),
    ),
]

