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


def _bbox_mid_y(bbox) -> float:
    """Return the vertical midpoint of a bounding box."""
    ys = [pt[1] for pt in bbox]
    return (min(ys) + max(ys)) / 2.0


def _bbox_height(bbox) -> float:
    """Return the height of a bounding box."""
    ys = [pt[1] for pt in bbox]
    return max(ys) - min(ys)


def _group_into_paragraphs(
    items: list[tuple[list, str, float]],
) -> list[list[tuple[str, float]]]:
    """Group detections into paragraphs by vertical proximity.

    Detections on the same line (Y midpoints within half a line
    height) are joined with spaces. A vertical gap larger than
    1.5x the line height starts a new paragraph.
    """
    if not items:
        return []

    # Sort top-to-bottom, then left-to-right
    sorted_items = sorted(items, key=lambda it: (_bbox_mid_y(it[0]), it[0][0][0]))

    lines: list[list[tuple[str, float]]] = []
    line_ys: list[float] = []
    cur_line: list[tuple[str, float]] = []
    cur_y = _bbox_mid_y(sorted_items[0][0])
    cur_h = max(_bbox_height(sorted_items[0][0]), 10.0)

    for bbox, txt, conf in sorted_items:
        mid_y = _bbox_mid_y(bbox)
        h = _bbox_height(bbox)
        if cur_line and abs(mid_y - cur_y) > cur_h * 0.6:
            # New line
            lines.append(cur_line)
            line_ys.append(cur_y)
            cur_line = []
            cur_y = mid_y
            cur_h = max(h, 10.0)
        cur_line.append((txt, conf))
        # Running average of Y for the current line
        cur_y = (cur_y + mid_y) / 2.0
        cur_h = max(cur_h, h)

    if cur_line:
        lines.append(cur_line)
        line_ys.append(cur_y)

    # Group lines into paragraphs based on vertical gaps
    paragraphs: list[list[tuple[str, float]]] = []
    cur_para: list[tuple[str, float]] = []
    prev_y = line_ys[0] if line_ys else 0.0

    for i, line in enumerate(lines):
        y = line_ys[i]
        if i > 0:
            gap = abs(y - prev_y)
            avg_h = max(
                sum(_bbox_height(sorted_items[0][0]) for _ in line) / len(line),
                10.0,
            )
            if gap > avg_h * 1.8:
                # Large gap -> new paragraph
                if cur_para:
                    paragraphs.append(cur_para)
                cur_para = []
        # Join all detections on this line with spaces
        line_text = " ".join(txt for txt, _ in line)
        line_conf = sum(c for _, c in line) / len(line) if line else 0.0
        cur_para.append((line_text, line_conf))
        prev_y = y

    if cur_para:
        paragraphs.append(cur_para)

    return paragraphs


def ocr_rgb_array_detailed(image_rgb: "np.ndarray", gpu: bool = False) -> OcrResult:
    """Run OCR returning text, per-detection scores, and mean confidence."""
    reader = get_easyocr_reader(gpu=gpu)
    raw = reader.readtext(image_rgb, detail=1, paragraph=False)
    if not raw:
        return OcrResult(text="", detections=[], mean_confidence=0.0)

    # Collect raw detections with bounding boxes
    items: list[tuple[list, str, float]] = []
    all_detections: list[tuple[str, float]] = []
    total_conf = 0.0
    for item in raw:
        bbox = item[0]
        txt = str(item[1]).strip()
        conf = float(item[2])
        if txt:
            items.append((bbox, txt, conf))
            all_detections.append((txt, conf))
            total_conf += conf

    mean_conf = total_conf / len(all_detections) if all_detections else 0.0

    # Group into paragraphs by spatial position
    paragraphs = _group_into_paragraphs(items)
    para_texts: list[str] = []
    for para_lines in paragraphs:
        para_texts.append("\n".join(txt for txt, _ in para_lines))

    text = "\n\n".join(para_texts)
    return OcrResult(
        text=text,
        detections=all_detections,
        mean_confidence=mean_conf,
    )
