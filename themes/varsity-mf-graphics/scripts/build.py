#!/usr/bin/env python3
"""Build every frame in spec.json to 1920x1080 PNGs.

usage: python3 build.py spec.json --out out [--only 0.27,1.38] [--no-sheet]

Writes out/<id>.png for each frame, out/<id>_overlay.png (transparent) for
frames that sit over the anchor (ribbon / definition / anchor), and
out/_sheet_N.jpg contact sheets (6 frames each). Prints WARN lines.
"""
import argparse, json, os, sys, pathlib, math

KIT = pathlib.Path(__file__).resolve().parent.parent
TPL = KIT / "templates"
ANCHOR = {"ribbon", "definition", "anchor"}


def page_html(frame, overlay):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="house.css"></head><body><div id="stage"></div>
<script>window.FRAME={json.dumps(frame)};window.OPTS={{overlay:{str(overlay).lower()}}};</script>
<script src="render.js"></script></body></html>"""


def launch(p):
    exe = os.environ.get("CHROMIUM_PATH")
    kw = {"args": ["--allow-file-access-from-files", "--disable-web-security"]}
    if exe:
        kw["executable_path"] = exe
    try:
        return p.chromium.launch(**kw)
    except Exception:
        for c in ["/opt/pw-browsers/chromium", "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]:
            for path in pathlib.Path(c).parent.glob(pathlib.Path(c).name + "*") if not os.path.exists(c) else [pathlib.Path(c)]:
                exe = path
                if path.is_dir():
                    hits = list(path.rglob("chrome")) + list(path.rglob("chromium"))
                    hits = [h for h in hits if h.is_file() and os.access(h, os.X_OK)]
                    if not hits:
                        continue
                    exe = hits[0]
                try:
                    kw["executable_path"] = str(exe)
                    return p.chromium.launch(**kw)
                except Exception:
                    pass
        raise


def contact_sheets(out, ids):
    from PIL import Image, ImageDraw
    W, H = 640, 360
    for s in range(0, len(ids), 6):
        sheet = Image.new("RGB", (W * 2, (H + 30) * 3), "white")
        d = ImageDraw.Draw(sheet)
        for i, fid in enumerate(ids[s:s + 6]):
            im = Image.open(out / f"{fid}.png").convert("RGB").resize((W, H))
            x, y = (i % 2) * W, (i // 2) * (H + 30)
            sheet.paste(im, (x, y + 30))
            d.text((x + 6, y + 8), fid, fill="black")
        sheet.save(out / f"_sheet_{s // 6 + 1}.jpg", quality=82)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default="out")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-sheet", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    frames = spec["frames"] if isinstance(spec, dict) else spec
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    built, nwarn = [], 0
    with sync_playwright() as p:
        br = launch(p)
        pg = br.new_page(viewport={"width": 1920, "height": 1080})
        for f in frames:
            fid = str(f["id"])
            if only and fid not in only:
                continue
            if f.get("type") in (None, "footage", "screen", "repeat"):
                continue  # storyboard-only beats, nothing to render
            for overlay in ([False, True] if f["type"] in ANCHOR else [False]):
                tmp = TPL / f"_tmp_{os.getpid()}.html"
                tmp.write_text(page_html(f, overlay))
                pg.goto(tmp.as_uri())
                pg.wait_for_function("window.RENDERED === true", timeout=20000)
                pg.wait_for_load_state("networkidle")
                pg.wait_for_timeout(120)
                if not overlay:
                    for w in pg.evaluate("window.QA ? window.QA() : ['render.js failed']"):
                        print(f"WARN {fid}: {w}")
                        nwarn += 1
                name = f"{fid}_overlay.png" if overlay else f"{fid}.png"
                pg.screenshot(path=str(out / name), omit_background=overlay, clip={"x": 0, "y": 0, "width": 1920, "height": 1080})
                tmp.unlink(missing_ok=True)
            built.append(fid)
            print(f"ok {fid} ({f['type']})")
        br.close()
    if built and not a.no_sheet:
        for old in out.glob("_sheet_*.jpg"):
            old.unlink()
        ids = [f["id"] for f in frames if (out / f"{f['id']}.png").exists()]
        contact_sheets(out, ids)  # always all frames in spec order, even with --only
    print(f"built {len(built)} frames, {nwarn} warnings -> {out}")


SKIP_STUDIO = frozenset({"footage", "screen", "repeat", None, ""})


def _studio_page_html(frame: dict, *, overlay: bool = False, edit: bool = False) -> str:
    import json

    opts: dict = {"overlay": overlay}
    if edit:
        opts["studioEdit"] = True
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../templates/house.css"></head><body><div id="stage"></div>
<script>window.FRAME={json.dumps(frame)};window.OPTS={json.dumps(opts)};</script>
<script src="../templates/render.js"></script></body></html>"""


def _placeholder_html(frame: dict, edit: bool) -> str:
    fid = frame.get("id", "?")
    typ = frame.get("type") or "beat"
    vo = (frame.get("vo") or frame.get("why") or "Storyboard-only beat — no graphic PNG.").replace("<", "&lt;")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;font:400 15px Inter,system-ui,sans-serif;background:#1a1917;color:#eee;display:flex;align-items:center;justify-content:center;height:100vh}}
.card{{max-width:720px;padding:28px 32px;border:1px solid #444;border-radius:12px;background:#252422}}
.k{{color:#9a9;font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
</style></head><body><div class="card"><div class="k">{typ} · {fid}</div>
<p style="margin:12px 0 0;line-height:1.55">{vo}</p>
<p style="margin:16px 0 0;color:#888;font-size:13px">No rendered graphic for this beat in the MF kit.</p></div></body></html>"""


def frame_html(frame, look=None, edit=False):
    """Studio preview HTML (same contract as varsity-english build.py)."""
    ftype = frame.get("type")
    if ftype in SKIP_STUDIO:
        return _placeholder_html(frame, edit)
    return _studio_page_html(frame, overlay=False, edit=edit)


CHECK_JS = "() => (typeof window.QA === 'function' ? window.QA() : (window.RENDER_ERROR ? [window.RENDER_ERROR] : []))"


if __name__ == "__main__":
    main()
