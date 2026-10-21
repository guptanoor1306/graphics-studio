"""Export frames for the in-house layer tool.

Each frame becomes ONE static, self-contained HTML file:
  - rendered in Chromium first, so JS-drawn parts (characters, wires, doodles) are real inline <svg>;
  - every <script> removed: the importer sees plain DOM only;
  - CSS inlined, fonts and images embedded as data: URIs, so nothing is fetched;
  - every visual element absolutely positioned at its rendered box (x, y, w, h in px),
    and named with data-layer="<type>:<text>", so the importer gets one layer per element in the right place;
  - the plate (studio/anchor background) is its own named layer, or left out (overlay=True).
Optionally also PNGs. Everything is returned as a zip.
"""
import asyncio, base64, io, mimetypes, os, pathlib, re, zipfile

FLATTEN_JS = r"""(overlay) => {
  // 1. name layers from the builder's structure
  const name = (e) => {
    const c = (e.className && e.className.baseVal === undefined ? e.className : '') || e.tagName.toLowerCase();
    const t = (e.innerText || e.getAttribute('src') || '').trim().replace(/\s+/g,' ').slice(0,40);
    return (c.split(' ')[0] || e.tagName.toLowerCase()) + (t ? ':' + t : '');
  };
  const plate = document.querySelector('.plate');
  if (plate) { plate.dataset.layer = 'plate:background'; if (overlay) plate.remove(); }
  // 2. layer candidates: images, svgs, and the outermost styled blocks of each component
  const blocks = [...document.querySelectorAll('body > .abs > *, body > .abs > * > *, body > div[style*="position: absolute"], body > img, body > svg')];
  // 3. freeze geometry: give each candidate absolute px box relative to the page
  const boxes = blocks.map(e => [e, e.getBoundingClientRect()]);
  for (const [e, r] of boxes) { if (!r.width || !r.height) continue; e.dataset.layer = e.dataset.layer || name(e);
    e.dataset.x = Math.round(r.left); e.dataset.y = Math.round(r.top); e.dataset.w = Math.round(r.width); e.dataset.h = Math.round(r.height); }
  document.querySelectorAll('script').forEach(s => s.remove());
  if (overlay) document.body.classList.add('overlay');
  return '<!doctype html>' + document.documentElement.outerHTML;
}"""


def _data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or ('font/ttf' if path.suffix == '.ttf' else 'application/octet-stream')
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def inline_assets(html: str, base_dir: pathlib.Path) -> str:
    """Replace the stylesheet link with inline CSS (fonts embedded) and every relative src/url with data URIs."""
    css_path = base_dir / "templates" / "varsity.css"
    css = css_path.read_text()
    css = re.sub(r"url\((\.\./fonts/[^)]+)\)", lambda m: f"url({_data_uri((base_dir / 'scenes' / m.group(1)).resolve())})", css)
    html = re.sub(r'<link rel="stylesheet" href="[^"]*varsity.css">', f"<style>{css}</style>", html)

    def fix_src(m):
        url = m.group(2)
        if url.startswith(("data:", "http")):
            return m.group(0)
        p = (base_dir / "scenes" / re.sub(r"^.*?/assets/", "../assets/", url)).resolve()
        if not p.exists():
            p = (base_dir / url.split('/kit/')[-1]).resolve()
        return f'{m.group(1)}="{_data_uri(p)}"' if p.exists() else m.group(0)
    html = re.sub(r'(src)="([^"]+)"', fix_src, html)
    html = re.sub(r'<base [^>]*>', '', html)
    return html


_CHROMIUM_ARGS = ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]


async def launch_chromium(pw):
    exe = os.environ.get("CHROMIUM_PATH")
    try:
        return await pw.chromium.launch(args=_CHROMIUM_ARGS)
    except Exception:
        if exe:
            return await pw.chromium.launch(executable_path=exe, args=_CHROMIUM_ARGS)
        raise


async def _load_frame(pg, html: str) -> None:
    await pg.set_content(html, wait_until="load", timeout=120_000)
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(120)


async def _render(pages, want_png):
    from playwright.async_api import async_playwright
    out = {}
    async with async_playwright() as p:
        b = await launch_chromium(p)
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        for fid, html, fss in pages:
            await _load_frame(pg, html)
            if want_png:
                out[f"png/{fid}.png"] = await pg.screenshot()
            out[f"html/{fid}.html"] = await pg.evaluate(FLATTEN_JS, False)
            if not fss:
                await _load_frame(pg, html)
                out[f"html_overlay/{fid}.html"] = await pg.evaluate(FLATTEN_JS, True)
                if want_png:
                    await pg.evaluate(
                        "document.body.classList.add('overlay');"
                        "document.querySelectorAll('.plate').forEach(e=>e.remove())"
                    )
                    out[f"png/{fid}_overlay.png"] = await pg.screenshot(omit_background=True)
        await b.close()
    return out


def export_zip(pages, theme_dir: pathlib.Path, want_png=True) -> bytes:
    """pages: list of (frame_id, full_html, is_fss). Base href in html must point at this server's /themes/."""
    files = asyncio.run(_render(pages, want_png))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            if name.endswith('.html'):
                data = inline_assets(data, theme_dir).encode()
            z.writestr(name, data)
        z.writestr('README.txt', 'html/          one static self-contained page per frame (plate included)\n'
                                 'html_overlay/  anchor frames without the plate (graphics only)\n'
                                 'png/           rendered frames (+ _overlay.png with transparency)\n'
                                 'Every element carries data-layer="<type>:<text>" and data-x/y/w/h (px at 1920x1080).\n')
    return buf.getvalue()
