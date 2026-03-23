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

# Run the CLI
dl-translate --help
dl-translate --format md "./document.pdf"
dl-translate --dry-run --format md "./folder"
dl-translate --extract-only "./scan.pdf"    # Markdown extraction without translation
```

## Environment setup

Requires `DEEPL_AUTH_KEY` in `.env` (copy from `.env.example`). DOCX output requires Pandoc installed separately.

## Architecture

The pipeline flows: **discovery → extraction → markdown protection → translation → output**.

- **`cli.py`** — Typer entry point. Orchestrates the full pipeline: discovers files, dispatches to the right extractor, translates, writes output. The `run()` function is the main flow.
- **`discovery.py`** — Resolves CLI path arguments (files, directories, globs) into a sorted list of supported files. Recursive directory walking is on by default.
- **`extractors/`** — Each module returns a result with a `.markdown` attribute:
  - `pdf.py` — PyMuPDF text extraction; falls back to OCR for scanned pages. Exports images to `{stem}_assets/`.
  - `docx.py` — python-docx; maps Word headings/tables to Markdown. Exports images to `{stem}_assets/`.
  - `md.py` — Direct UTF-8 read.
  - `image.py` — Pillow + EasyOCR.
  - `common.py` — Shared extractor types.
- **`md_translate.py`** — Splits YAML front matter (preserved verbatim) and fenced code blocks (preserved verbatim) from translatable prose. This is the core Markdown protection logic.
- **`translate.py`** — DeepL client wrapper. Handles API key loading, language detection (sends a sample to DeepL), target language normalization (`EN` → `EN-US`), and paragraph-boundary chunking (45k char limit per request).
- **`ocr_engine.py`** — EasyOCR lazy loader.
- **`output_docx.py`** — Markdown → DOCX conversion via pypandoc.

## Key design decisions

- Translation direction is EN↔ES only. Language is auto-detected unless `--target-lang` is specified.
- Extractors produce intermediate Markdown; translation operates on that Markdown representation, not on the original format.
- Output files are written next to the source with `_en`/`_es` suffixes. Asset images go to `{stem}_assets/`.
- Tests use fake/stub translators (simple string prefix functions) to avoid calling DeepL.

## Claude Code skill

A `/translate-file` skill is available at `.claude/skills/translate-file/`. When working in this repo, Claude Code auto-discovers it. For global use, copy the folder to `~/.claude/skills/translate-file/`. See the skill's README.md for installation options.
