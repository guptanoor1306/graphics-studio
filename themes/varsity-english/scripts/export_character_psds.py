#!/usr/bin/env python3
"""Export character groups from varsity-english-characters.zip PSDs into kit PNGs.

Keeps any existing PNG as *_legacy.png, writes refreshed art to the standard INDEX paths.
Run from repo root: python3 themes/varsity-english/scripts/export_character_psds.py
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from PIL import Image
from psd_tools import PSDImage

KIT = Path(__file__).resolve().parents[1]
ASSETS = KIT / "assets"
SOURCES = ASSETS / "_char_sources" / "varsity-english-characters"

# PSD file → layer group name (substring match) → standard asset path under assets/
EXPORTS = [
    ("Character 6.psd", "Character yellow", "setC/character_friend_yellow.png"),
    ("Character 2.psd", "Character 4", "setC/character_friend_blue.png"),
    ("Character 1.psd", "Character", "setC/character_small_on_box.png"),
    ("Chracter 3.psd", "Women 1", "setA/character_rahul_standing.png"),
    ("Character 4.psd", "Character style 3", "setB/character_mustache_garland.png"),
    ("Character 5.psd", "Character Style 2", "setA/character_rahul_pointing.png"),
]


def _find_group(doc: PSDImage, name_part: str):
    key = name_part.strip().lower()

    def walk(layers):
        for layer in layers:
            if layer.is_group() and key in (layer.name or "").strip().lower():
                return layer
            if layer.is_group():
                hit = walk(layer)
                if hit:
                    return hit
        return None

    return walk(doc)


def _alpha_crop(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if bb:
        im = im.crop(bb)
    return im


def export_one(psd_name: str, layer_key: str, rel_dest: str) -> dict:
    psd_path = SOURCES / psd_name
    if not psd_path.is_file():
        raise FileNotFoundError(psd_path)
    doc = PSDImage.open(psd_path)
    group = _find_group(doc, layer_key)
    if group is None:
        raise RuntimeError(f"{psd_name}: no group matching {layer_key!r}")
    im = _alpha_crop(group.composite())
    dest = ASSETS / rel_dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    legacy = dest.with_name(dest.stem + "_legacy.png")
    if dest.is_file() and not legacy.is_file():
        shutil.copy2(dest, legacy)
    im.save(dest, "PNG")
    return {
        "psd": psd_name,
        "layer": group.name,
        "dest": rel_dest,
        "legacy": legacy.name if legacy.is_file() else None,
        "size": list(im.size),
    }


def main():
    if not SOURCES.is_dir():
        raise SystemExit(f"Missing extracted sources at {SOURCES} (unzip varsity-english-characters.zip there)")
    manifest = {"sources_dir": str(SOURCES.relative_to(KIT)), "exports": []}
    for psd, layer, dest in EXPORTS:
        manifest["exports"].append(export_one(psd, layer, dest))
        print(f"OK {dest} ← {psd} / {layer}")
    meta_path = ASSETS / "_character_refresh.json"
    meta_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
