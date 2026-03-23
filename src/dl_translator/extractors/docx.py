from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from dl_translator.extractors.common import ExtractResult


def _iter_body_blocks(document: Document):
    body = document.element.body
    for child in body:
        if child.tag == qn("w:p"):
            yield "p", Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield "t", Table(child, document)


def _drawing_count(paragraph: Paragraph) -> int:
    return len(paragraph._element.xpath(".//w:drawing"))


def _heading_level(style_name: str | None) -> int | None:
    if not style_name:
        return None
    if "Heading" in style_name:
        parts = style_name.split()
        try:
            return int(parts[-1])
        except ValueError:
            return 1
    if style_name == "Title":
        return 1
    return None


def _paragraph_to_md(paragraph: Paragraph) -> str:
    text = paragraph.text.replace("\r", "").strip()
    if not text:
        return ""
    hl = _heading_level(paragraph.style.name if paragraph.style else None)
    if hl is not None:
        return ("#" * hl) + " " + text + "\n\n"
    if paragraph.style and paragraph.style.name.startswith("List"):
        return "- " + text + "\n"
    return text + "\n\n"


def _table_to_md(table: Table) -> str:
    rows_data: list[list[str]] = []
    for row in table.rows:
        cells = []
        for cell in row.cells:
            t = cell.text.replace("\n", " ").replace("|", "\\|").strip()
            cells.append(t)
        rows_data.append(cells)
    if not rows_data:
        return ""
    width = max(len(r) for r in rows_data)
    norm = [r + [""] * (width - len(r)) for r in rows_data]
    header = norm[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for r in norm[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines) + "\n\n"


def _save_inline_shape(shape, assets_dir: Path, index: int) -> str:
    image = shape.image
    ext = (image.ext or "png").lower()
    if ext not in ("png", "jpeg", "jpg", "gif", "bmp", "webp"):
        ext = "png"
    name = f"img_{index:03d}.{ext}"
    out = assets_dir / name
    out.write_bytes(image.blob)
    return name


def _append_drawings(
    parts: list[str],
    paragraph: Paragraph,
    stem: str,
    saved_names: list[str],
    shape_idx: list[int],
) -> None:
    n = _drawing_count(paragraph)
    for _ in range(n):
        if shape_idx[0] < len(saved_names):
            fname = saved_names[shape_idx[0]]
            parts.append(f"![]({stem}_assets/{fname})\n\n")
            shape_idx[0] += 1


def _append_drawings_from_table(
    parts: list[str],
    table: Table,
    stem: str,
    saved_names: list[str],
    shape_idx: list[int],
) -> None:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                _append_drawings(parts, p, stem, saved_names, shape_idx)


def extract_docx(path: Path) -> ExtractResult:
    stem = path.stem
    parent = path.parent
    assets_dir = parent / f"{stem}_assets"
    doc = Document(path)

    saved_names: list[str] = []
    for i, shape in enumerate(doc.inline_shapes):
        assets_dir.mkdir(parents=True, exist_ok=True)
        name = _save_inline_shape(shape, assets_dir, i + 1)
        saved_names.append(name)

    parts: list[str] = []
    shape_idx = [0]

    for kind, block in _iter_body_blocks(doc):
        if kind == "p":
            para: Paragraph = block
            parts.append(_paragraph_to_md(para))
            _append_drawings(parts, para, stem, saved_names, shape_idx)
        else:
            tbl: Table = block
            parts.append(_table_to_md(tbl))
            _append_drawings_from_table(parts, tbl, stem, saved_names, shape_idx)

    if shape_idx[0] < len(saved_names):
        for j in range(shape_idx[0], len(saved_names)):
            parts.append(f"![]({stem}_assets/{saved_names[j]})\n\n")

    md = "".join(parts).strip() + "\n"
    asset_paths = [assets_dir / n for n in saved_names] if saved_names else []
    if asset_paths:
        return ExtractResult(
            markdown=md, assets_dir=assets_dir, asset_paths=asset_paths
        )
    return ExtractResult(markdown=md)
