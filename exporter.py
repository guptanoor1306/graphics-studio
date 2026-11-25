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
import asyncio
import threading, base64, io, mimetypes, os, pathlib, re, zipfile

FLATTEN_JS = r"""(overlay) => {
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
    e.dataset.x = Math.round(r.left); e.dataset.y = Math.round(r.top);
    e.dataset.w = Math.round(r.width); e.dataset.h = Math.round(r.height);
  }
  document.querySelectorAll('script').forEach(s => s.remove());
  if (overlay) document.body.classList.add('overlay');
  return '<!doctype html>' + document.documentElement.outerHTML;
}"""


_DATA_URI_CACHE: dict[str, str] = {}
_EXPORT_PARALLEL = max(1, int(os.environ.get("EXPORT_PARALLEL", "4")))


def _data_uri(path: pathlib.Path) -> str:
    key = str(path.resolve())
    cached = _DATA_URI_CACHE.get(key)
    if cached is not None:
        return cached
    mime = mimetypes.guess_type(str(path))[0] or ('font/ttf' if path.suffix == '.ttf' else 'application/octet-stream')
    uri = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    _DATA_URI_CACHE[key] = uri
    return uri


def _theme_css(base_dir: pathlib.Path) -> tuple[pathlib.Path, str]:
    for name in ("varsity.css", "house.css", "zo.css", "reel.css"):
        p = base_dir / "templates" / name
        if p.is_file():
            return p, name
    tpl = base_dir / "templates"
    if tpl.is_dir():
        for p in sorted(tpl.glob("*.css")):
            if p.name != "fonts.css":
                return p, p.name
    raise FileNotFoundError(f"No theme CSS in {base_dir / 'templates'}")


_CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")
_CSS_IMPORT = re.compile(r"""@import\s+(?:url\(\s*)?(['"]?)([^'")\s;]+)\1\s*\)?\s*([^;]*);""")
_LINK_CSS = re.compile(r"""<link\b[^>]*\brel=["']stylesheet["'][^>]*>""", re.I)


def _clean(url: str) -> str:
    return url.strip().split("?")[0].split("#")[0]


def _css_inline(css: str, folder: pathlib.Path, fallback, depth: int = 0) -> str:
    """A stylesheet with its @imports written in place and every url(...) as a data URI. Links start at the
    stylesheet's own folder (how a browser reads them); `fallback` resolves the kit's older ../assets forms.
    No @import url(data:...) is left: LA Studio's reader can't parse a data: import (its ';' ends the match)."""
    def imp(m):
        p = (folder / _clean(m.group(2))).resolve()
        if depth < 6 and p.is_file() and p.suffix == ".css":
            inner = _css_inline(p.read_text(), p.parent, fallback, depth + 1)
            return f"@media {m.group(3).strip()} {{\n{inner}\n}}" if m.group(3).strip() else inner
        return m.group(0)

    def url(m):
        u = m.group(2).strip()
        if u.startswith(("data:", "http", "#", "//")):
            return m.group(0)
        p = (folder / _clean(u)).resolve()
        if not p.is_file():
            p = fallback(u)
        return f"url('{_data_uri(p)}')" if p else m.group(0)
    return _CSS_URL.sub(url, _CSS_IMPORT.sub(imp, css))


def inline_assets(html: str, base_dir: pathlib.Path) -> str:
    """A frame page made self-contained for LA Studio's Layers step: every stylesheet (the kit's and any extra
    link) inlined with its fonts and pictures, and every relative src / SVG image href / url(...) as a data URI.
    LA Studio refuses a page that still links a file (html_inline.check), so nothing relative may be left."""
    css_path, css_name = _theme_css(base_dir)

    def resolve(url):
        url = _clean(url)
        p = (base_dir / "scenes" / re.sub(r"^.*?/assets/", "../assets/", url)).resolve()
        if not p.exists():
            p = (base_dir / url.split('/kit/')[-1]).resolve()
        if not p.exists() and url.startswith("../"):
            p = (base_dir / url).resolve()
        if not p.exists():
            p = (base_dir / "templates" / url).resolve()
        if not p.exists() and "fonts/" in url:
            p = (base_dir / "templates" / "fonts" / pathlib.Path(url).name).resolve()
        return p if p.exists() and p.is_file() else None

    def link(m):
        tag = m.group(0)
        href = re.search(r"""\bhref=["']([^"']+)["']""", tag)
        if not href or href.group(1).startswith(("http", "data:", "//")):
            return tag
        h = href.group(1)
        p = resolve(h) or (css_path if pathlib.Path(_clean(h)).name == css_name else None)   # ZO chat has its own zo.css
        if not p or p.suffix != ".css":
            return tag
        return f"<style>{_css_inline(p.read_text(), p.parent, resolve)}</style>"
    html = _LINK_CSS.sub(link, html)
    html = re.sub(r"(<style\b[^>]*>)(.*?)(</style\s*>)",
                  lambda m: m.group(1) + _css_inline(m.group(2), css_path.parent, resolve) + m.group(3), html, flags=re.S | re.I)

    def fix_src(m):
        url = m.group(3)
        if url.startswith(("data:", "http", "#", "//", "${")):
            return m.group(0)
        p = resolve(url)
        return f'{m.group(1)}{m.group(2)}="{_data_uri(p)}"' if p else m.group(0)
    html = re.sub(r'(\s)(src)="([^"]+)"', fix_src, html)
    # SVG pictures (<image href="../assets/chars6/c1.png">): inline the file, never a link (<a href>)
    html = re.sub(r'(<image\b[^>]*?\s)((?:xlink:)?href)="([^"]+)"',
                  lambda m: m.group(0) if m.group(3).startswith(("data:", "http", "#")) or not resolve(m.group(3))
                  else f'{m.group(1)}{m.group(2)}="{_data_uri(resolve(m.group(3)))}"', html, flags=re.I)

    def fix_url(m):  # pictures set in style="" attributes: url('../assets/…')
        url = m.group(2).strip()
        if url.startswith(("data:", "http", "#")):
            return m.group(0)
        p = resolve(url)
        return f"url('{_data_uri(p)}')" if p else m.group(0)
    html = re.sub(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", fix_url, html)
    html = re.sub(r'<base [^>]*>', '', html)
    return html


class _SharedBrowser:
    """One Chromium kept open for Make Layers: each frame gets a fresh page in it instead of launching a whole
    browser per frame (that launch, times every frame, times everyone pressing Make Layers, slowed the server)."""
    _lock = threading.Lock()
    _loop = None
    _browser = None
    _pw = None
    _alock = None

    @classmethod
    def loop(cls):
        with cls._lock:
            if cls._loop is None:
                cls._loop = asyncio.new_event_loop()
                threading.Thread(target=cls._loop.run_forever, name="layers-browser", daemon=True).start()
        return cls._loop

    @classmethod
    async def browser(cls):
        if cls._alock is None:
            cls._alock = asyncio.Lock()
        async with cls._alock:
            if cls._browser is None or not cls._browser.is_connected():
                from playwright.async_api import async_playwright
                if cls._pw is None:
                    cls._pw = await async_playwright().start()
                cls._browser = await launch_chromium(cls._pw)
            return cls._browser

    @classmethod
    def render(cls, pages, want_png, viewport, timeout=180):
        async def go():
            return await _render_with(await cls.browser(), pages, want_png, viewport)
        return asyncio.run_coroutine_threadsafe(go(), cls.loop()).result(timeout=timeout)


def frame_page_for_layers(html: str, theme_dir: pathlib.Path, viewport=(1920, 1080)) -> str:
    """One frame as LA Studio's Layers step needs it: rendered once (the kit scripts build some picture paths
    at run time, e.g. MF's ../assets/illus/…, Varsity English's V.asset(...)), flattened to static HTML like the
    zip's html/ pages, then made self-contained. Falls back to inlining the source page if rendering fails."""
    try:
        try:
            files = _SharedBrowser.render([(None, html, True, None)], False, viewport)
        except Exception as e:     # the shared browser died or hung: one fresh browser for this frame
            print("frame_page_for_layers: shared browser failed, using a fresh one:", e, flush=True)
            _SharedBrowser._browser = None
            files = asyncio.run(_render([(None, html, True, None)], False, viewport))
        flat = next((v for k, v in files.items() if k.endswith(".html")), None)
        if flat:
            return inline_assets(flat, theme_dir)
    except Exception as e:
        print("frame_page_for_layers: rendering failed, inlining the source page:", e, flush=True)
    return inline_assets(html, theme_dir)


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
    await pg.wait_for_timeout(50)
    await pg.evaluate(
        """() => {
      if (window.OPTS) window.OPTS.tagLayers = true;
      if (typeof window.initMfInlineText === 'function') window.initMfInlineText();
    }"""
    )


def _layer_registry_js() -> str:
    p = pathlib.Path(__file__).resolve().parent / "static" / "layer_registry.js"
    return p.read_text()


def _page_row(row) -> tuple[str, str, bool, str | None]:
    if len(row) >= 4:
        return row[0], row[1], row[2], row[3]
    return row[0], row[1], row[2], None


async def _capture_page(
    b,
    registry_js: str,
    vw: int,
    vh: int,
    html: str,
    *,
    flatten_overlay: bool,
    want_png: bool,
    png_key: str | None,
    html_key: str,
    overlay_png: bool = False,
) -> dict[str, bytes | str]:
    pg = await b.new_page(viewport={"width": vw, "height": vh})
    out: dict[str, bytes | str] = {}
    try:
        await _load_frame(pg, html)
        await pg.evaluate(registry_js)
        if want_png and png_key:
            if overlay_png:
                await pg.evaluate(
                    "() => { document.body.classList.add('overlay');"
                    "document.querySelectorAll('.plate').forEach(e => e.remove()); }"
                )
            out[png_key] = await pg.screenshot(
                omit_background=True if overlay_png else False
            )
        out[html_key] = await pg.evaluate(FLATTEN_JS, flatten_overlay)
    finally:
        await pg.close()
    return out


async def _render_one(
    b,
    registry_js: str,
    want_png: bool,
    vw: int,
    vh: int,
    fid: str,
    html: str,
    skip_overlay: bool,
    html_overlay: str | None,
) -> dict[str, bytes | str]:
    full = _capture_page(
        b,
        registry_js,
        vw,
        vh,
        html,
        flatten_overlay=False,
        want_png=want_png,
        png_key=f"png/{fid}.png" if want_png else None,
        html_key=f"html/{fid}.html",
    )
    if skip_overlay:
        return await full
    ov_html = html_overlay if html_overlay is not None else html
    ov = _capture_page(
        b,
        registry_js,
        vw,
        vh,
        ov_html,
        flatten_overlay=True,
        want_png=want_png,
        png_key=f"png/{fid}_overlay.png" if want_png else None,
        html_key=f"html_overlay/{fid}.html",
        overlay_png=want_png,
    )
    full_r, ov_r = await asyncio.gather(full, ov)
    full_r.update(ov_r)
    return full_r


async def _render(pages, want_png, viewport=(1920, 1080)):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        b = await launch_chromium(p)
        try:
            return await _render_with(b, pages, want_png, viewport)
        finally:
            await b.close()


async def _render_with(b, pages, want_png, viewport=(1920, 1080)):
    registry_js = _layer_registry_js()
    vw, vh = viewport
    rows = [_page_row(r) for r in pages]
    sem = asyncio.Semaphore(_EXPORT_PARALLEL)

    async def work(row):
        fid, html, skip_overlay, html_overlay = row
        async with sem:
            return await _render_one(
                b,
                registry_js,
                want_png,
                vw,
                vh,
                fid,
                html,
                skip_overlay,
                html_overlay,
            )

    parts = await asyncio.gather(*(work(r) for r in rows))
    out: dict[str, bytes | str] = {}
    for part in parts:
        out.update(part)
    return out


def export_png(pages, viewport=(1920, 1080)) -> bytes:
    """Render the first page as a single PNG (full frame with plate when present)."""
    if not pages:
        raise ValueError("No frames to export")
    files = asyncio.run(_render(pages, True, viewport))
    fid = pages[0][0]
    key = f"png/{fid}.png"
    if key not in files:
        raise ValueError("Export produced no PNG")
    return files[key]


def renamed(key: str, names: dict[str, str] | None) -> str:
    """png/<fid>.png, png/<fid>_overlay.png, html/<fid>.html … with <fid> swapped for its name from `names`."""
    if not names or "/" not in key:
        return key
    folder, base = key.rsplit("/", 1)
    stem, dot, ext = base.rpartition(".")
    for suffix in ("_overlay", ""):
        if suffix and not stem.endswith(suffix):
            continue
        fid = stem[: len(stem) - len(suffix)] if suffix else stem
        new = names.get(fid)
        if new:
            return f"{folder}/{new}{suffix}{dot}{ext}"
    return key


def export_zip(
    pages,
    theme_dir: pathlib.Path,
    want_png=True,
    viewport=(1920, 1080),
    *,
    storyboard_csv: str | None = None,
    zip_path: pathlib.Path | None = None,
    extra_files: dict[str, str] | None = None,
    names: dict[str, str] | None = None,
) -> bytes:
    """pages: list of (frame_id, full_html, skip_overlay, html_overlay|None). Base href in html must point at this server's /themes/.
    names: frame id -> file name to use in the zip (e.g. "1.53_my_video"), so files are named by the time they come in."""
    if not pages:
        raise ValueError("No frames to export")
    files = asyncio.run(_render(pages, want_png, viewport))
    if not files:
        raise ValueError("Export produced no files")
    buf: io.BytesIO | None = None if zip_path else io.BytesIO()
    with zipfile.ZipFile(zip_path or buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            if name.endswith('.html'):
                data = inline_assets(data, theme_dir).encode()
            z.writestr(renamed(name, names), data)
        vw, vh = viewport
        readme = (
            'html/          one static self-contained page per frame (plate included)\n'
            'html_overlay/  anchor frames without the plate (graphics only)\n'
            'png/           rendered frames (+ _overlay.png with transparency)\n'
            f'Layer coordinates are in px at {vw}x{vh}.\n'
        )
        if storyboard_csv:
            z.writestr('storyboard-instructions.csv', storyboard_csv.encode('utf-8'))
            readme += 'storyboard-instructions.csv  timestamp-ordered storyboard beats (CSV)\n'
        for name, text in (extra_files or {}).items():
            z.writestr(name, text.encode("utf-8"))
            readme += f"{name}\n"
        z.writestr("README.txt", readme)
    if zip_path is not None:
        return b""
    assert buf is not None
    return buf.getvalue()
