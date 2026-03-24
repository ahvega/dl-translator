# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

dl-translator is a Python CLI that converts PDF, DOCX, Markdown, and image files into Markdown, then translates between English and Spanish using the DeepL API. The CLI command is `dl-translate`.

## Development commands

```bash
# Activate venv (Windows)
.venv/Scripts/activate

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest -q

# Run a single test
pytest tests/test_md_translate.py::test_split_front_matter -v

# Formatting and linting
black src/ tests/
flake8 src/ tests/

# Run the CLI
dl-translate --help
dl-translate --format md "./document.pdf"
dl-translate --fix-ocr --format md "./scanned.pdf"
dl-translate --dry-run --format md "./folder"
dl-translate --extract-only "./scan.pdf"
```

## Environment setup

Requires `DEEPL_AUTH_KEY` in `.env` (copy from `.env.example`). Optional: `GOOGLE_API_KEY` for Gemini Flash OCR correction (`--fix-ocr`). DOCX output requires Pandoc installed separately.

## Architecture

The pipeline is **phased with checkpoint-based resumption**. Each phase writes output to disk; re-runs skip completed phases.

**Phase flow:** `cli.py` → `pipeline.py` → Phase 1-5

- **`cli.py`** — Typer entry point. Handles argument parsing, file discovery, and delegates to `pipeline.run_pipeline()` for each file.
- **`pipeline.py`** — Phased execution engine. Manages `PipelineState` per file and runs:
  - Phase 1 (extract): dispatches to extractors, writes `_extract.md`
  - Phase 2 (OCR clean): runs `ocr_cleanup.py`, writes `_{src_lang}.md`
  - Phase 3 (translate): runs DeepL via `translate.py`, writes `_{tgt_lang}.md`
  - Phase 4 (review): optional Gemini semantic review
  - Phase 5 (docx): optional DOCX conversion
- **`discovery.py`** — Resolves CLI path arguments (files, directories, globs) into a sorted list of supported files.
- **`extractors/`** — Each module returns `ExtractResult` with `.markdown`, `.used_ocr`, and optional asset paths:
  - `pdf.py` — PyMuPDF text extraction; falls back to OCR for scanned pages. Auto-detects booklet layouts via `booklet.py`.
  - `docx.py` — python-docx; maps Word headings/tables to Markdown.
  - `md.py` — Direct UTF-8 read.
  - `image.py` — Pillow + EasyOCR.
- **`booklet.py`** — Detects saddle-stitch/booklet PDFs (landscape pages), splits each page in half, detects printed page numbers via OCR, and reorders sequentially.
- **`paragraph_join.py`** — Joins OCR continuation lines into paragraphs based on punctuation/capitalization patterns. ALL CAPS lines treated as headings.
- **`ocr_engine.py`** — Confidence-aware EasyOCR with spatial paragraph grouping using bounding box Y-coordinates.
- **`ocr_cleanup.py`** — Two-layer OCR correction: Layer 1 (rapidfuzz + wordfreq local fixes), Layer 2 (Gemini Flash, opt-in).
- **`gemini_fix.py`** — Gemini 2.0 Flash client for OCR post-correction and post-translation semantic review. Uses document filename as title hint.
- **`md_translate.py`** — YAML front matter and fenced code block protection during translation.
- **`translate.py`** — DeepL client wrapper. Language detection, target normalization, paragraph-boundary chunking (45k char limit).
- **`output_docx.py`** — Markdown → DOCX via pypandoc with Arial font enforcement across all runs, tables, headers, and footers.

## Key design decisions

- Translation direction is EN↔ES only. Language is auto-detected unless `--target-lang` is specified.
- Extractors produce intermediate Markdown; translation operates on that Markdown representation, not on the original format.
- Output files are written next to the source with `_en`/`_es` suffixes. Asset images go to `{stem}_assets/`.
- Pipeline phases use file-based checkpoints. Delete `_extract.md`/`_es.md`/`_en.md` to force re-processing.
- Gemini Flash is optional (requires `GOOGLE_API_KEY`). Without it, only local OCR correction runs.
- Tests use fake/stub translators (simple string prefix functions) to avoid calling DeepL.

## Claude Code skill

A `/translate-file` skill is available at `.claude/skills/translate-file/`. When working in this repo, Claude Code auto-discovers it. For global use, copy the folder to `~/.claude/skills/translate-file/`.
