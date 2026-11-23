"""Human storyboard PDF uploads (per project)."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PDF_DIR = ROOT / "data" / "storyboard_pdfs"
MAX_PDF_BYTES = 25 * 1024 * 1024


def pdf_path(project_id: int) -> pathlib.Path:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    return PDF_DIR / f"{project_id}.pdf"


def read_pdf(project_id: int) -> bytes:
    p = pdf_path(project_id)
    if not p.is_file():
        raise FileNotFoundError("No storyboard PDF uploaded for this project")
    raw = p.read_bytes()
    if len(raw) > MAX_PDF_BYTES:
        raise ValueError(f"PDF exceeds {MAX_PDF_BYTES // (1024 * 1024)}MB limit")
    return raw


def save_pdf(project_id: int, raw: bytes) -> pathlib.Path:
    if len(raw) > MAX_PDF_BYTES:
        raise ValueError(f"PDF exceeds {MAX_PDF_BYTES // (1024 * 1024)}MB limit")
    if not raw:
        raise ValueError("Empty file")
    try:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        p = pdf_path(project_id)
        p.write_bytes(raw)
    except OSError as e:
        raise OSError(
            f"Could not write PDF to server storage ({e}). "
            "On Railway, mount a volume at /app/data (or set DATA_DIR) so uploads survive redeploys."
        ) from e
    return p


THIN_PAGE_CHARS = 200   # fewer selectable characters than this: the page is mostly a picture


def raster_pages(pdf_bytes: bytes, *, max_pages: int = 20, scale: float = 1.75, only_thin: bool = False) -> list[tuple[str, bytes]]:
    """JPEG renders of PDF pages so Claude can read dense timestamp tables and sketches.

    only_thin: Claude already gets every page of an attached PDF as its text plus a picture, so a page with a text
    layer was being paid for twice. Render only pages with little selectable text (scans, sketches, screenshots).
    STUDIO_PDF_PAGE_IMAGES=all brings back a render of every page."""
    import os
    if only_thin and os.environ.get("STUDIO_PDF_PAGE_IMAGES", "").strip().lower() == "all":
        only_thin = False
    try:
        import fitz  # pymupdf
    except ImportError:
        return []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return []
    out: list[tuple[str, bytes]] = []
    n = min(len(doc), max_pages)
    mat = fitz.Matrix(scale, scale)
    for i in range(n):
        try:
            if only_thin and len((doc[i].get_text("text") or "").strip()) >= THIN_PAGE_CHARS:
                continue
            pix = doc[i].get_pixmap(matrix=mat, alpha=False)
            out.append(("image/jpeg", pix.tobytes("jpeg")))
        except Exception:
            continue
    doc.close()
    return out
