from __future__ import annotations

import io
from pathlib import Path

import fitz
from PIL import Image
import numpy as np

from dl_translator.extractors.common import ExtractResult
from dl_translator.ocr_engine import ocr_rgb_array

MIN_TEXT_CHARS = 40


def _page_to_rgb(page: fitz.Page, dpi: int = 200) -> np.ndarray:
    pix = page.get_pixmap(dpi=dpi)
    im = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    return np.asarray(im)


def _extract_images(doc: fitz.Document, page: fitz.Page, assets_dir: Path, page_index: int) -> list[str]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    rel_refs: list[str] = []
    for i, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        try:
            base = doc.extract_image(xref)
        except Exception:
            continue
        ext = (base.get("ext") or "png").lower()
        if ext not in ("png", "jpg", "jpeg", "webp"):
            ext = "png"
        name = f"page{page_index + 1:03d}_img{i + 1:02d}.{ext}"
        out = assets_dir / name
        out.write_bytes(base["image"])
        rel_refs.append(name)
    return rel_refs


def extract_pdf(path: Path, force_ocr: bool = False, gpu: bool = False) -> ExtractResult:
    stem = path.stem
    parent = path.parent
    assets_dir = parent / f"{stem}_assets"
    asset_paths: list[Path] = []

    doc = fitz.open(path)
    parts: list[str] = []

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            img_refs = _extract_images(doc, page, assets_dir, page_index)
            for name in img_refs:
                asset_paths.append(assets_dir / name)

            md_try = ""
            try:
                md_try = page.get_text("markdown") or ""
            except Exception:
                md_try = ""

            plain = page.get_text("text") or ""
            use_ocr = force_ocr or len(plain.strip()) < MIN_TEXT_CHARS

            if use_ocr:
                rgb = _page_to_rgb(page)
                ocr_text = ocr_rgb_array(rgb, gpu=gpu)
                block = f"## Page {page_index + 1}\n\n{ocr_text}\n"
            else:
                if md_try.strip():
                    block = md_try.strip()
                    if not block.startswith("#"):
                        block = f"## Page {page_index + 1}\n\n{block}"
                else:
                    block = f"## Page {page_index + 1}\n\n{plain.strip()}\n"

            for n in img_refs:
                block += f"\n![]({stem}_assets/{n})\n"

            parts.append(block)

        full = "\n\n---\n\n".join(parts)
        if not full.strip():
            full = "_(empty PDF)_"
        if asset_paths:
            return ExtractResult(markdown=full, assets_dir=assets_dir, asset_paths=asset_paths)
        return ExtractResult(markdown=full)
    finally:
        doc.close()
