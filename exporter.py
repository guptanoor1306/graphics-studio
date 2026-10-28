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

FLATTEN_JS = r"""(flattenOpts) => {
  let overlay = false;
  let scale = 1;
  if (flattenOpts === true) overlay = true;
  else if (flattenOpts === false) overlay = false;
  else if (flattenOpts && typeof flattenOpts === 'object') {
    overlay = !!flattenOpts.overlay;
    scale = Math.max(1, Number(flattenOpts.scale) || 1);
  }
  const name = (e) => {
    const c = (e.className && e.className.baseVal === undefined ? e.className : '') || e.tagName.toLowerCase();
    const t = (e.innerText || e.getAttribute('src') || '').trim().replace(/\s+/g,' ').slice(0,40);
    return (c.split(' ')[0] || e.tagName.toLowerCase()) + (t ? ':' + t : '');
  };
  const plate = document.querySelector('.plate');
  if (plate) { plate.dataset.layer = 'plate:background'; if (overlay) plate.remove(); }
  if (typeof StudioLayerRegistry !== 'undefined') {
    StudioLayerRegistry.flattenRegistryLayers(overlay);
  }
  const blocks = [...document.querySelectorAll('[data-spec-idx], body > .abs > *, body > .abs > * > *, body > div[style*="position: absolute"], body > img, body > svg')];
  const boxes = blocks.map(e => [e, e.getBoundingClientRect()]);
  for (const [e, r] of boxes) {
    if (!r.width || !r.height) continue;
    if (e.dataset.x != null && e.dataset.y != null) continue;
    e.dataset.layer = e.dataset.layer || name(e);
    e.dataset.x = String(Math.round(r.left)); e.dataset.y = String(Math.round(r.top));
    e.dataset.w = String(Math.round(r.width)); e.dataset.h = String(Math.round(r.height));
  }
  if (scale !== 1) {
    const mul = (n) => Math.round(parseFloat(n) * scale);
    document.querySelectorAll('[data-x],[data-y],[data-w],[data-h]').forEach((el) => {
      for (const k of ['x', 'y', 'w', 'h']) {
        if (el.dataset[k] == null || el.dataset[k] === '') continue;
        el.dataset[k] = String(mul(el.dataset[k]));
      }
    });
  }
  document.querySelectorAll('script').forEach(s => s.remove());
  if (overlay) document.body.classList.add('overlay');
  return '<!doctype html>' + document.documentElement.outerHTML;
}"""


def export_scale() -> float:
    """Pixel multiplier for PNG + layer coords (2 = 1920×1080 → 3840×2160). Set EXPORT_SCALE=1 for legacy."""
    raw = (os.environ.get("EXPORT_SCALE") or "2").strip()
    try:
        s = float(raw)
    except ValueError:
        s = 2.0
    return max(1.0, min(4.0, s))


def _data_uri(path: pathlib.Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or ('font/ttf' if path.suffix == '.ttf' else 'application/octet-stream')
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _theme_css(base_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    for name in ("varsity.css", "house.css"):
        p = base_dir / "templates" / name
        if p.is_file():
            return p, name
    raise FileNotFoundError(f"No theme CSS in {base_dir / 'templates'}")


def inline_assets(html: str, base_dir: pathlib.Path) -> str:
    """Replace the stylesheet link with inline CSS (fonts embedded) and every relative src/url with data URIs."""
    css_path, css_name = _theme_css(base_dir)
    css = css_path.read_text()
    css = re.sub(
        r"url\((\.\./fonts/[^)]+)\)",
        lambda m: f"url({_data_uri((base_dir / 'templates' / 'fonts' / pathlib.Path(m.group(1)).name).resolve())})"
        if (base_dir / "templates" / "fonts").is_dir()
        else m.group(0),
        css,
    )
    css = re.sub(r"url\((\.\./fonts/[^)]+)\)", lambda m: f"url({_data_uri((base_dir / 'scenes' / m.group(1)).resolve())})", css)
    html = re.sub(rf'<link rel="stylesheet" href="[^"]*{re.escape(css_name)}">', f"<style>{css}</style>", html)

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
    if "window.RENDERED" in html or "render.js" in html:
        try:
            await pg.wait_for_function("window.RENDERED === true", timeout=20_000)
        except Exception:
            pass
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(120)
    await pg.evaluate(
        """() => {
      if (window.OPTS) window.OPTS.tagLayers = true;
      if (typeof window.initMfInlineText === 'function') window.initMfInlineText();
    }"""
    )


def _layer_registry_js() -> str:
    p = pathlib.Path(__file__).resolve().parent / "static" / "layer_registry.js"
    return p.read_text()


async def _render(pages, want_png, viewport=(1920, 1080), scale: float = 1.0):
    from playwright.async_api import async_playwright
    registry_js = _layer_registry_js()
    vw, vh = viewport
    scale = max(1.0, min(4.0, float(scale or 1.0)))
    flat = {"scale": scale}
    out = {}
    async with async_playwright() as p:
        b = await launch_chromium(p)
        ctx = await b.new_context(
            viewport={"width": vw, "height": vh},
            device_scale_factor=scale,
        )
        pg = await ctx.new_page()
        for fid, html, fss in pages:
            await _load_frame(pg, html)
            await pg.evaluate(registry_js)
            if want_png:
                out[f"png/{fid}.png"] = await pg.screenshot()
            out[f"html/{fid}.html"] = await pg.evaluate(FLATTEN_JS, {**flat, "overlay": False})
            if not fss:
                await _load_frame(pg, html)
                await pg.evaluate(registry_js)
                out[f"html_overlay/{fid}.html"] = await pg.evaluate(FLATTEN_JS, {**flat, "overlay": True})
                if want_png:
                    await pg.evaluate(
                        "document.body.classList.add('overlay');"
                        "document.querySelectorAll('.plate').forEach(e=>e.remove())"
                    )
                    out[f"png/{fid}_overlay.png"] = await pg.screenshot(omit_background=True)
        await ctx.close()
        await b.close()
    return out


def export_zip(
    pages,
    theme_dir: pathlib.Path,
    want_png=True,
    viewport=(1920, 1080),
    scale: float | None = None,
) -> bytes:
    """pages: list of (frame_id, full_html, is_fss). Base href in html must point at this server's /themes/."""
    sc = export_scale() if scale is None else max(1.0, min(4.0, float(scale)))
    files = asyncio.run(_render(pages, want_png, viewport, sc))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            if name.endswith('.html'):
                data = inline_assets(data, theme_dir).encode()
            z.writestr(name, data)
        vw, vh = viewport
        pw, ph = int(vw * sc), int(vh * sc)
        z.writestr(
            'README.txt',
            'html/          one static self-contained page per frame (plate included)\n'
            'html_overlay/  anchor frames without the plate (graphics only)\n'
            'png/           rendered frames (+ _overlay.png with transparency)\n'
            f'Design canvas: {vw}x{vh} CSS px. Export scale: {sc:g}x → PNG size {pw}x{ph}.\n'
            f'Layer data-x/y/w/h are in export px ({pw}x{ph} space). Set EXPORT_SCALE=1 on the server for 1:1 1080p.\n',
        )
    return buf.getvalue()
