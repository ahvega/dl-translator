"""Lazy EasyOCR reader (English + Spanish)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

_reader = None
_lock = threading.Lock()


@dataclass
class OcrResult:
    """OCR output with per-detection confidence scores."""

    text: str
    detections: list[tuple[str, float]] = field(default_factory=list)
    mean_confidence: float = 1.0


def get_easyocr_reader(gpu: bool = False):
    """Return a singleton easyocr.Reader(['en','es'])."""
    global _reader
    with _lock:
        if _reader is None:
            import easyocr

            _reader = easyocr.Reader(["en", "es"], gpu=gpu, verbose=False)
    return _reader


def ocr_rgb_array(image_rgb: "np.ndarray", gpu: bool = False) -> str:
    """Run OCR on HxWx3 uint8 RGB image; return plain text."""
    result = ocr_rgb_array_detailed(image_rgb, gpu=gpu)
    return result.text


def ocr_rgb_array_detailed(image_rgb: "np.ndarray", gpu: bool = False) -> OcrResult:
    """Run OCR returning text, per-detection scores, and mean confidence."""
    reader = get_easyocr_reader(gpu=gpu)
    raw = reader.readtext(image_rgb, detail=1, paragraph=False)
    if not raw:
        return OcrResult(text="", detections=[], mean_confidence=0.0)

    detections: list[tuple[str, float]] = []
    total_conf = 0.0
    for item in raw:
        txt = str(item[1]).strip()
        conf = float(item[2])
        if txt:
            detections.append((txt, conf))
            total_conf += conf

    mean_conf = total_conf / len(detections) if detections else 0.0
    text = "\n\n".join(txt for txt, _ in detections)
    return OcrResult(
        text=text,
        detections=detections,
        mean_confidence=mean_conf,
    )
