"""Kits that reuse another kit's skill and renderer under their own name (their own videos and toolkit).

themes/<alias> is a symlink to the base kit's folder, so the skill, assets and build script are shared; code that
checks a kit by name asks base(theme) instead of the raw name."""
ALIAS = {
    "zo-ipo-graphics": "zo-product-graphics",     # ZO IPO: its own toolkit; generates with the ZO Product skill for now
}


def base(theme: str | None) -> str:
    t = str(theme or "")
    return ALIAS.get(t, t)
