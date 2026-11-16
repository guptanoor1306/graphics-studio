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


# ---- fonts LA Studio already has: Make Layers can leave them out of each frame (a frame is mostly its fonts) ----
_FACE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.I)
_SKIP_ITEM = re.compile(r"([A-Za-z0-9_\-]+(?: [A-Za-z0-9_\-]+)*)\s*:\s*([1-9]00)(i?)")   # words split by single spaces: no ambiguity, no slow matching
MAX_SKIP_LEN, MAX_SKIP_ITEM = 2048, 80
MAX_SKIP = 64


def _face_key(body: str) -> tuple[str, int, bool] | None:
    """(family, weight, italic) of one @font-face block; weight 400 when it says nothing."""
    fam = re.search(r"font-family\s*:\s*([^;}]+)", body, re.I)
    if not fam:
        return None
    family = fam.group(1).strip().strip("\"'").strip()
    w = re.search(r"font-weight\s*:\s*([A-Za-z0-9]+)(\s+\d)?", body, re.I)
    raw = (w.group(1).lower() if w else "400")
    if w and w.group(2):
        return family, -1, False                                             # a weight range (variable font): never taken from the computer
    weight = int(raw) if raw.isdigit() and len(raw) <= 4 else {"normal": 400, "bold": 700}.get(raw, 400)
    italic = bool(re.search(r"font-style\s*:\s*(italic|oblique)", body, re.I))
    return family, weight, italic


def font_faces(html: str) -> list[dict]:
    """Every font a page or stylesheet defines, once: [{family, weight, italic}]."""
    out, seen = [], set()
    for m in _FACE.finditer(html or ""):
        k = _face_key(m.group(1))
        if k and k not in seen:
            seen.add(k)
            out.append({"family": k[0], "weight": k[1], "italic": k[2]})
    return out


def parse_skip(value) -> set[tuple[str, int, bool]]:
    """export.html?skip=Inter:300,Inter:700i -> {("inter", 300, False), ("inter", 700, True)}; anything else is ignored."""
    out, value = set(), str(value or "")
    if len(value) > MAX_SKIP_LEN:
        return out
    for part in value.split(",")[: MAX_SKIP * 4]:
        part = part.strip()
        m = _SKIP_ITEM.fullmatch(part) if len(part) <= MAX_SKIP_ITEM else None
        if m:
            out.add((m.group(1).strip().lower(), int(m.group(2)), bool(m.group(3))))
            if len(out) >= MAX_SKIP:
                break
    return out


_STYLE = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold",
          800: "ExtraBold", 900: "Black"}


def _local_src(family: str, weight: int, italic: bool) -> str:
    """src for a font installed on the computer: its full name and its PostScript name ("Inter Light", "Inter-Light")."""
    style = _STYLE.get(weight, "Regular")
    if italic:
        style = "Italic" if style == "Regular" else style + "Italic"
    full = f"{family} {style[:-6] + ' Italic' if italic and style != 'Italic' else style}"
    ps = f"{family.replace(' ', '')}-{style}"
    return f'src:local("{full}"),local("{ps}")'


def drop_faces(html: str, skip: set) -> str:
    """The fonts named in skip are taken from the computer instead of the page: each @font-face keeps its family, weight
    and style, only its src becomes local(…). The page then picks exactly the same weights as before, without the
    font files inside it."""
    if not skip:
        return html
    def swap(m):
        k = _face_key(m.group(1))
        if not k or (k[0].lower(), k[1], k[2]) not in skip:
            return m.group(0)
        body = re.sub(r"src\s*:(?:[^;()]|\([^)]*(?:\)|\Z))*;?", "", m.group(1)).strip().rstrip(";")   # (a data: URL has its own ";")
        return "@font-face{" + (body + ";" if body else "") + _local_src(*k) + "}"
    return _FACE.sub(swap, html)


def theme_font_faces(base_dir: pathlib.Path) -> list[dict]:
    """The fonts a kit's stylesheets define (its main CSS and templates/fonts.css)."""
    css_path, _ = _theme_css(base_dir)
    css = css_path.read_text()
    extra = base_dir / "templates" / "fonts.css"
    if extra.is_file() and extra != css_path:
        css += "\n" + extra.read_text()
    return font_faces(css)


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

    def resolve(url):
        p = (base_dir / "scenes" / re.sub(r"^.*?/assets/", "../assets/", url)).resolve()
        if not p.exists():
            p = (base_dir / url.split('/kit/')[-1]).resolve()
        if not p.exists() and url.startswith("../"):
            p = (base_dir / url).resolve()
        return p if p.exists() and p.is_file() else None

    def fix_src(m):
        url = m.group(2)
        if url.startswith(("data:", "http")):
            return m.group(0)
        p = resolve(url)
        return f'{m.group(1)}="{_data_uri(p)}"' if p else m.group(0)

    def fix_url(m):  # pictures set in styles: url('../assets/…'), url("…") or url(…) unquoted
        url = m.group(2).strip()
        if url.startswith(("data:", "http", "#")):
            return m.group(0)
        p = resolve(url)
        return f"url('{_data_uri(p)}')" if p else m.group(0)
    html = re.sub(r'(src)="([^"]+)"', fix_src, html)
    html = re.sub(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""", fix_url, html)
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

    async with async_playwright() as p:
        b = await launch_chromium(p)
        parts = await asyncio.gather(*(work(r) for r in rows))
        await b.close()
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


def export_zip(
    pages,
    theme_dir: pathlib.Path,
    want_png=True,
    viewport=(1920, 1080),
    *,
    storyboard_csv: str | None = None,
    zip_path: pathlib.Path | None = None,
    extra_files: dict[str, str] | None = None,
) -> bytes:
    """pages: list of (frame_id, full_html, skip_overlay, html_overlay|None). Base href in html must point at this server's /themes/."""
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
            z.writestr(name, data)
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
