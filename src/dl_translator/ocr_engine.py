"""Lazy EasyOCR reader (English + Spanish)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

_reader = None
_lock = threading.Lock()


def get_easyocr_reader(gpu: bool = False):
    """Return a singleton easyocr.Reader(['en','es']). First call downloads models."""
    global _reader
    with _lock:
        if _reader is None:
            import easyocr

            _reader = easyocr.Reader(["en", "es"], gpu=gpu, verbose=False)
    return _reader


def ocr_rgb_array(image_rgb: "np.ndarray", gpu: bool = False) -> str:
    """Run OCR on HxWx3 uint8 RGB image; return plain text."""
    reader = get_easyocr_reader(gpu=gpu)
    lines = reader.readtext(image_rgb, detail=0, paragraph=True)
    if isinstance(lines, list):
        parts = [str(x).strip() for x in lines if str(x).strip()]
        return "\n\n".join(parts)
    return str(lines).strip()
