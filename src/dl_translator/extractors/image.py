from __future__ import annotations

from pathlib import Path

from PIL import Image
import numpy as np

from dl_translator.extractors.common import ExtractResult
from dl_translator.ocr_engine import ocr_rgb_array


def extract_image(path: Path, gpu: bool = False) -> ExtractResult:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img)
    text = ocr_rgb_array(arr, gpu=gpu)
    md = "# OCR\n\n" + text if text else "# OCR\n\n_(no text detected)_"
    return ExtractResult(markdown=md, used_ocr=True)
