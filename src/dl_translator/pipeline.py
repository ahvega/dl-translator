"""Phased translation pipeline with checkpoint-based resumption.

Phases for OCR-based inputs:
  1. extract   - PDF pages -> page images + raw OCR -> {stem}_extract.md
  2. ocr_clean - Local + Gemini OCR correction    -> {stem}_{src}.md
  3. translate - DeepL translation                 -> {stem}_{tgt}.md
  4. review    - Gemini semantic review of translation -> overwrite {stem}_{tgt}.md
  5. docx      - Markdown -> DOCX conversion       -> {stem}_{tgt}.docx

For non-OCR inputs, phases 1-2 collapse and phase 4 is skipped.
Each phase writes its output file; re-runs detect existing files and skip.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from deepl import Translator

console = Console(stderr=True)

_MIN_TEXT_CHARS = 40


def _pdf_is_scanned(path: Path) -> bool:
    """Quick check: True if PDF has mostly image-only pages."""
    import fitz

    doc = fitz.open(path)
    try:
        scanned = 0
        for i in range(min(3, len(doc))):
            text = doc[i].get_text("text") or ""
            if len(text.strip()) < _MIN_TEXT_CHARS:
                scanned += 1
        return scanned > 0
    finally:
        doc.close()


@dataclass
class PipelineState:
    """Tracks phase outputs for a single source file."""

    source: Path
    stem: str
    parent: Path
    source_lang: str = "EN"
    target_lang: str = "ES"
    used_ocr: bool = False

    @property
    def extract_path(self) -> Path:
        return self.parent / f"{self.stem}_extract.md"

    @property
    def source_md_path(self) -> Path:
        suf = "es" if self.source_lang.upper().startswith("ES") else "en"
        return self.parent / f"{self.stem}_{suf}.md"

    @property
    def target_md_path(self) -> Path:
        suf = "es" if self.target_lang.upper().startswith("ES") else "en"
        return self.parent / f"{self.stem}_{suf}.md"

    @property
    def target_docx_path(self) -> Path:
        suf = "es" if self.target_lang.upper().startswith("ES") else "en"
        return self.parent / f"{self.stem}_{suf}.docx"


def phase_extract(
    state: PipelineState,
    force_ocr: bool,
    gpu: bool,
) -> str:
    """Phase 1: Extract to Markdown. Returns raw markdown text."""
    if state.extract_path.exists():
        console.print(
            f"  [dim]Phase 1 (extract): skip"
            f" — {state.extract_path.name} exists[/dim]"
        )
        # Infer used_ocr from file type when resuming
        ext = state.source.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
            state.used_ocr = True
        elif ext == ".pdf":
            state.used_ocr = force_ocr or _pdf_is_scanned(state.source)
        return state.extract_path.read_text(encoding="utf-8")

    console.print("  [cyan]Phase 1 (extract):[/cyan] extracting...")
    from dl_translator.extractors.docx import extract_docx
    from dl_translator.extractors.image import extract_image
    from dl_translator.extractors.md import extract_markdown_file
    from dl_translator.extractors.pdf import extract_pdf

    ext = state.source.suffix.lower()
    if ext == ".pdf":
        result = extract_pdf(state.source, force_ocr=force_ocr, gpu=gpu)
    elif ext == ".docx":
        result = extract_docx(state.source)
    elif ext in (".md", ".markdown"):
        result = extract_markdown_file(state.source)
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
        result = extract_image(state.source, gpu=gpu)
    else:
        raise ValueError(f"Unsupported file type: {state.source}")

    state.used_ocr = result.used_ocr
    state.extract_path.write_text(result.markdown, encoding="utf-8")
    console.print(
        f"  [green]Phase 1 (extract): done[/green]" f" -> {state.extract_path.name}"
    )
    return result.markdown


def phase_ocr_clean(
    state: PipelineState,
    raw_md: str,
    fix_ocr: bool,
) -> str:
    """Phase 2: OCR cleanup. Returns cleaned source markdown."""
    if not state.used_ocr:
        return raw_md

    if state.source_md_path.exists():
        console.print(
            f"  [dim]Phase 2 (OCR clean): skip"
            f" — {state.source_md_path.name} exists[/dim]"
        )
        return state.source_md_path.read_text(encoding="utf-8")

    console.print("  [cyan]Phase 2 (OCR clean):[/cyan] correcting...")
    from dl_translator.ocr_cleanup import clean_ocr_markdown

    cleaned = clean_ocr_markdown(
        raw_md,
        state.source_lang,
        fix_ocr=fix_ocr,
        source_filename=state.stem,
    )
    state.source_md_path.write_text(cleaned, encoding="utf-8")
    console.print(
        f"  [green]Phase 2 (OCR clean): done[/green]" f" -> {state.source_md_path.name}"
    )
    return cleaned


def phase_translate(
    state: PipelineState,
    source_md: str,
    translator: "Translator",
) -> str:
    """Phase 3: DeepL translation. Returns translated markdown."""
    if state.target_md_path.exists():
        console.print(
            f"  [dim]Phase 3 (translate): skip"
            f" — {state.target_md_path.name} exists[/dim]"
        )
        return state.target_md_path.read_text(encoding="utf-8")

    console.print("  [cyan]Phase 3 (translate):[/cyan] translating...")
    from dl_translator.md_translate import translate_full_markdown
    from dl_translator.translate import translate_text_chunks

    def chunk_fn(s: str) -> str:
        return translate_text_chunks(translator, s, target_lang=state.target_lang)

    translated = translate_full_markdown(source_md, chunk_fn)
    state.target_md_path.write_text(translated, encoding="utf-8")
    console.print(
        f"  [green]Phase 3 (translate): done[/green]" f" -> {state.target_md_path.name}"
    )
    return translated


def phase_review(
    state: PipelineState,
    translated_md: str,
    fix_ocr: bool,
) -> str:
    """Phase 4: Post-translation semantic review via Gemini.

    Only runs for OCR inputs when --fix-ocr is enabled.
    Overwrites the target markdown with the reviewed version.
    """
    if not state.used_ocr or not fix_ocr:
        return translated_md

    console.print("  [cyan]Phase 4 (review):[/cyan]" " semantic consistency check...")
    from dl_translator.gemini_fix import review_translation_with_gemini

    reviewed = review_translation_with_gemini(translated_md, state.target_lang)
    if reviewed != translated_md:
        state.target_md_path.write_text(reviewed, encoding="utf-8")
        console.print(
            f"  [green]Phase 4 (review): done[/green]"
            f" -> {state.target_md_path.name} updated"
        )
    else:
        console.print("  [green]Phase 4 (review): done[/green] (no changes)")
    return reviewed


def phase_docx(
    state: PipelineState,
    translated_md: str,
) -> Path:
    """Phase 5: Convert to DOCX."""
    if state.target_docx_path.exists():
        console.print(
            f"  [dim]Phase 5 (docx): skip"
            f" — {state.target_docx_path.name} exists[/dim]"
        )
        return state.target_docx_path

    console.print("  [cyan]Phase 5 (docx):[/cyan] converting...")
    from dl_translator.output_docx import markdown_to_docx

    markdown_to_docx(
        translated_md,
        state.target_docx_path,
        resource_parent=state.parent,
    )
    console.print(
        f"  [green]Phase 5 (docx): done[/green]" f" -> {state.target_docx_path.name}"
    )
    return state.target_docx_path


def run_pipeline(
    path: Path,
    translator: "Translator",
    target_lang_override: str | None,
    fmt: str,
    force_ocr: bool,
    gpu: bool,
    fix_ocr: bool,
) -> None:
    """Run the full phased pipeline for one file."""
    state = PipelineState(
        source=path,
        stem=path.stem,
        parent=path.parent,
    )

    console.print(f"\n[bold]{path}[/bold]")

    # Phase 1: Extract
    raw_md = phase_extract(state, force_ocr=force_ocr, gpu=gpu)

    # Detect languages (need raw text for detection)
    from dl_translator.translate import (
        detect_source_lang,
        normalize_target_for_deepl,
    )

    need_detection = not target_lang_override or state.used_ocr
    if need_detection:
        state.source_lang = detect_source_lang(translator, raw_md)
    if target_lang_override:
        state.target_lang = normalize_target_for_deepl(target_lang_override)
    else:
        state.target_lang = (
            "EN-US" if state.source_lang.upper().startswith("ES") else "ES"
        )

    # Phase 2: OCR cleanup
    source_md = phase_ocr_clean(state, raw_md, fix_ocr=fix_ocr)

    # Phase 3: Translate
    translated_md = phase_translate(state, source_md, translator)

    # Phase 4: Semantic review
    translated_md = phase_review(state, translated_md, fix_ocr=fix_ocr)

    # Phase 5: DOCX (if requested)
    if fmt == "docx":
        phase_docx(state, translated_md)

    console.print(f"[green]All phases complete for {path.name}[/green]")
