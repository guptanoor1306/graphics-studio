#!/usr/bin/env python3
"""Build reel frames to 1080×1920 PNGs (Graphics Studio + local CLI)."""
import argparse, json, os, pathlib

KIT = pathlib.Path(__file__).resolve().parent.parent
TPL = KIT / "templates"
CANVAS_W, CANVAS_H = 1080, 1920
CANVAS = (CANVAS_W, CANVAS_H)
OVERLAY_TYPES = {"ost", "anchor"}
SKIP_STUDIO = frozenset({"footage", "screen", "repeat", None, ""})


def page_html(frame, overlay):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="reel.css"></head><body><div id="stage"></div>
<script>window.FRAME={json.dumps(frame)};window.OPTS={{overlay:{str(overlay).lower()}}};</script>
<script src="render.js"></script></body></html>"""


def launch(p):
    exe = os.environ.get("CHROMIUM_PATH")
    kw = {"args": ["--allow-file-access-from-files", "--disable-web-security"]}
    if exe:
        kw["executable_path"] = exe
    return p.chromium.launch(**kw)


def contact_sheets(out, ids):
    from PIL import Image, ImageDraw

    W, H = 270, 480
    for s in range(0, len(ids), 6):
        sheet = Image.new("RGB", (W * 2, (H + 30) * 3), "white")
        d = ImageDraw.Draw(sheet)
        for i, fid in enumerate(ids[s : s + 6]):
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
        pg = br.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H})
        for f in frames:
            fid = str(f["id"])
            if only and fid not in only:
                continue
            if f.get("type") in (None, "footage", "screen", "repeat"):
                continue
            for overlay in ([False, True] if f["type"] in OVERLAY_TYPES else [False]):
                tmp = TPL / f"_tmp_{os.getpid()}.html"
                tmp.write_text(page_html(f, overlay))
                pg.goto(tmp.as_uri())
                pg.wait_for_function("window.RENDERED === true", timeout=20000)
                pg.wait_for_timeout(120)
                if not overlay:
                    for w in pg.evaluate("window.QA ? window.QA() : ['render.js failed']"):
                        print(f"WARN {fid}: {w}")
                        nwarn += 1
                name = f"{fid}_overlay.png" if overlay else f"{fid}.png"
                pg.screenshot(
                    path=str(out / name),
                    omit_background=overlay,
                    clip={"x": 0, "y": 0, "width": CANVAS_W, "height": CANVAS_H},
                )
                tmp.unlink(missing_ok=True)
            built.append(fid)
            print(f"ok {fid} ({f.get('type')})")
        br.close()
    if built and not a.no_sheet:
        for old in out.glob("_sheet_*.jpg"):
            old.unlink()
        ids = [f["id"] for f in frames if (out / f"{f['id']}.png").exists()]
        contact_sheets(out, ids)
    print(f"built {len(built)} frames, {nwarn} warnings -> {out}")


def _studio_page_html(frame: dict, *, overlay: bool = False, edit: bool = False) -> str:
    opts: dict = {"overlay": overlay}
    if edit:
        opts["studioEdit"] = True
    body_cls = "studio-edit-mode" if edit else ""
    body_attr = f' class="{body_cls}"' if body_cls else ""
    meta = f'<meta name="studio-canvas" content="{CANVAS_W},{CANVAS_H}">'
    return f"""<!doctype html><html><head><meta charset="utf-8">{meta}
<link rel="stylesheet" href="../templates/reel.css"></head><body{body_attr}><div id="stage"></div>
<script>window.FRAME={json.dumps(frame)};window.OPTS={json.dumps(opts)};</script>
<script src="../templates/render.js"></script></body></html>"""


def _placeholder_html(frame: dict, edit: bool) -> str:
    fid = frame.get("id", "?")
    typ = frame.get("type") or "beat"
    vo = (frame.get("vo") or frame.get("why") or "Storyboard-only beat — no graphic.").replace("<", "&lt;")
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="studio-canvas" content="{CANVAS_W},{CANVAS_H}"><style>
body{{margin:0;font:400 15px Manrope,system-ui,sans-serif;background:#1a1917;color:#eee;display:flex;align-items:center;justify-content:center;height:100vh}}
.card{{max-width:720px;padding:28px 32px;border:1px solid #444;border-radius:12px;background:#252422}}
.k{{color:#9a9;font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
</style></head><body><div class="card"><div class="k">{typ} · {fid}</div>
<p style="margin:12px 0 0;line-height:1.55">{vo}</p>
<p style="margin:16px 0 0;color:#888;font-size:13px">No static graphic for this beat.</p></div></body></html>"""


def frame_html(frame, look=None, edit=False):
    ftype = frame.get("type")
    if ftype in SKIP_STUDIO:
        return _placeholder_html(frame, edit)
    return _studio_page_html(frame, overlay=False, edit=edit)


CHECK_JS = "() => (typeof window.QA === 'function' ? window.QA() : (window.RENDER_ERROR ? [window.RENDER_ERROR] : []))"


if __name__ == "__main__":
    main()
