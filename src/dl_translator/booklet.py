"""Booklet/saddle-stitch PDF page splitting and reordering.

A booklet PDF has landscape pages where each PDF page contains two
book pages side by side. This module splits each page in half,
detects printed page numbers, and reorders the halves sequentially.
"""

from __future__ import annotations

import io
import re

import fitz
import numpy as np
from PIL import Image


def _page_to_image(page: fitz.Page, dpi: int = 200) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def _find_page_number(
    detections: list[tuple[list, str, float]],
    half_h: int,
    side: str,
    half_w: int,
) -> int | None:
    """Find a page number near the bottom of a half-page.

    Left halves have numbers at bottom-left, right halves at
    bottom-right.
    """
    candidates: list[tuple[int, float]] = []
    for bbox, txt, conf in detections:
        txt = txt.strip()
        # Accept 1-2 digit numbers
        if not re.match(r"^\d{1,2}$", txt):
            continue
        mid_y = (bbox[0][1] + bbox[2][1]) / 2
        mid_x = (bbox[0][0] + bbox[2][0]) / 2
        # Must be in bottom 20% of page
        if mid_y < half_h * 0.80:
            continue
        # Left pages: number on left side; right pages: number on right
        if side == "left" and mid_x > half_w * 0.4:
            continue
        if side == "right" and mid_x < half_w * 0.6:
            continue
        candidates.append((int(txt), conf))

    if not candidates:
        return None
    # Return highest-confidence match
    candidates.sort(key=lambda x: -x[1])
    return candidates[0][0]


def is_booklet_pdf(doc: fitz.Document) -> bool:
    """Heuristic: True if pages are landscape (wider than tall)."""
    if len(doc) < 2:
        return False
    # Check first non-cover page
    for i in range(min(3, len(doc))):
        page = doc[i]
        r = page.rect
        if r.width > r.height * 1.2:
            return True
    return False


def split_booklet_pages(
    doc: fitz.Document,
    dpi: int = 200,
    gpu: bool = False,
) -> list[tuple[int | None, np.ndarray]]:
    """Split each PDF page into left/right halves with page numbers.

    Returns list of (page_number, rgb_array) sorted by page number.
    Halves without a detected page number get None.
    """
    from dl_translator.ocr_engine import get_easyocr_reader

    reader = get_easyocr_reader(gpu=gpu)
    halves: list[tuple[int | None, np.ndarray]] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        im = _page_to_image(page, dpi=dpi)
        w, h = im.size
        mid = w // 2

        left_im = im.crop((0, 0, mid, h))
        right_im = im.crop((mid, 0, w, h))

        for side, half_im in [("left", left_im), ("right", right_im)]:
            arr = np.asarray(half_im)
            raw = reader.readtext(arr, detail=1, paragraph=False)
            items = []
            for item in raw:
                txt = str(item[1]).strip()
                if txt:
                    items.append((item[0], txt, float(item[2])))

            pg_num = _find_page_number(items, h, side, mid)
            halves.append((pg_num, arr))

    # Sort: numbered pages first (by number), then unnumbered
    numbered = [(n, arr) for n, arr in halves if n is not None]
    unnumbered = [(n, arr) for n, arr in halves if n is None]
    numbered.sort(key=lambda x: x[0])

    return unnumbered + numbered


def split_and_ocr_booklet(
    doc: fitz.Document,
    dpi: int = 200,
    gpu: bool = False,
) -> list[tuple[int | None, str]]:
    """Split booklet and OCR each half-page.

    Returns list of (page_number, ocr_text) sorted by page number.
    """
    from dl_translator.ocr_engine import ocr_rgb_array

    halves = split_booklet_pages(doc, dpi=dpi, gpu=gpu)
    results: list[tuple[int | None, str]] = []
    for pg_num, arr in halves:
        text = ocr_rgb_array(arr, gpu=gpu)
        if text.strip():
            results.append((pg_num, text))
    return results
