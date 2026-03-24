# dl-translator

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Typer CLI](https://img.shields.io/badge/CLI-Typer-009688?logo=python&logoColor=white)](https://typer.tiangolo.com/)
[![DeepL API](https://img.shields.io/badge/translation-DeepL-0F2B46?logo=deepl&logoColor=white)](https://www.deepl.com/pro-api)
[![Gemini Flash](https://img.shields.io/badge/OCR%20fix-Gemini%20Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com/)
[![EasyOCR](https://img.shields.io/badge/OCR-EasyOCR-5C2D91)](https://github.com/JaidedAI/EasyOCR)
[![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-0096D6)](https://pymupdf.readthedocs.io/)
[![python-docx](https://img.shields.io/badge/DOCX-python--docx-2B579A)](https://python-docx.readthedocs.io/)
[![Pandoc optional](https://img.shields.io/badge/DOCX%20export-Pandoc-1A1A1A?logo=pandoc&logoColor=white)](https://pandoc.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)

**Author:** Adalberto H. Vega

Convert **PDF**, **DOCX**, **Markdown**, or **images** into **Markdown**, then translate the content between **English** and **Spanish** with the [DeepL API](https://www.deepl.com/pro-api). The tool is designed for local and batch workflows: it detects supported files, extracts readable Markdown, preserves as much structure as practical, and writes the translated file beside the source using `_en` or `_es` suffixes.

## What it does

`dl-translator` is a Python CLI for document localization workflows where the original source may be a text PDF, scanned PDF, Word document, Markdown file, or image.

The pipeline is phased, with checkpoint-based resumption:

1. **Extract** — Discover files, rasterize and OCR scanned pages, produce `{stem}_extract.md`.
2. **OCR Clean** — Local dictionary-based fixes (rapidfuzz + wordfreq) plus optional Gemini Flash AI correction. Produces `{stem}_{source_lang}.md`.
3. **Translate** — Detect source language, translate via DeepL. Produces `{stem}_{target_lang}.md`.
4. **Review** — Optional Gemini Flash semantic consistency check on the translation.
5. **DOCX** — Optional Markdown to DOCX conversion via Pandoc with Arial font normalization.

Each phase writes its output to disk. On re-run, completed phases are **skipped automatically**, so interrupted or incremental workflows resume where they left off.

## Features

- **Input formats:** PDF, DOCX, Markdown, PNG, JPG, JPEG, WebP, TIFF, and BMP.
- **Scanned PDF support:** pages without a text layer are rasterized and OCR'd with EasyOCR.
- **Booklet PDF support:** auto-detects saddle-stitch/booklet layouts (landscape pages with two book pages side by side), splits each page in half, detects printed page numbers, and reorders content sequentially.
- **Paragraph joining:** OCR text lines are joined into proper paragraphs based on punctuation and capitalization patterns rather than raw line breaks.
- **Two-layer OCR correction:**
  - **Layer 1 (local, always active):** rapidfuzz + wordfreq character-substitution fixes for common OCR confusions (`0→o`, `1→l/i`, `@→a`, `$→s`, etc.).
  - **Layer 2 (Gemini Flash, opt-in with `--fix-ocr`):** sends OCR text to Google Gemini 2.0 Flash for AI-powered correction of garbled ornamental/decorative fonts. Uses the source filename as a title hint for cover pages.
- **Post-translation review:** when `--fix-ocr` is enabled, Gemini Flash also reviews the translated output for semantic consistency issues caused by residual OCR errors.
- **Phased pipeline with checkpoints:** each phase writes its output file; re-runs skip completed phases automatically.
- **OCR reference output:** OCR-based inputs keep a Markdown copy of the cleaned source text in the original language for review.
- **Heading and table preservation:** DOCX headings and tables are mapped into Markdown; text PDFs use PyMuPDF's Markdown extraction when available.
- **Front matter safety:** YAML front matter in Markdown files is preserved unchanged.
- **Code fence safety:** fenced code blocks are excluded from translation.
- **Asset export:** embedded images from PDF and DOCX are exported to `{stem}_assets/` and linked from Markdown.
- **Batch processing:** recursive folder walking is enabled by default.
- **Flexible output:** write `.md` or `.docx`; interactive runs can prompt for the format if `--format` is omitted.
- **DOCX font normalization:** generated Word documents are normalized to use **Arial** across all paragraphs, tables, headers, and footers.
- **Confidence-aware OCR:** EasyOCR detections include per-word confidence scores and spatial bounding boxes, used for paragraph grouping and quality assessment.
- **Windows-friendly usage:** documented with PowerShell examples and venv setup.

## How output files are named

Outputs are written **next to the source file**, using the **target language suffix**:

- `document_en.md` / `document_es.md` — translated output
- `document_en.docx` / `document_es.docx` — DOCX output (if requested)
- `document_extract.md` — raw OCR extraction (Phase 1 checkpoint)
- `document_assets/` — embedded images

For OCR-based inputs, the cleaned source text is also saved:

- `document_es.md` — OCR-cleaned source text (Spanish original)
- `document_en.md` — translated output (English)

## Architecture

```text
input file/folder/glob
  -> discovery.py              # resolve paths, globs, directories
  -> pipeline.py               # phased execution with checkpoints
     Phase 1: extractor by type
        -> PDF: PyMuPDF text or page OCR
           -> booklet.py       # auto-detect and split booklet layouts
        -> DOCX: python-docx to Markdown
        -> Markdown: direct read
        -> Image: Pillow + EasyOCR
        -> ocr_engine.py       # confidence-aware OCR with spatial grouping
        -> paragraph_join.py   # join continuation lines into paragraphs
     Phase 2: ocr_cleanup.py
        -> Layer 1: rapidfuzz + wordfreq local fixes
        -> Layer 2: gemini_fix.py (optional, --fix-ocr)
     Phase 3: translate.py
        -> detect source language via DeepL
        -> chunk long text at paragraph boundaries
     Phase 4: gemini_fix.py    # semantic review (optional, --fix-ocr)
     Phase 5: output_docx.py   # Pandoc + Arial font enforcement
```

## Requirements

| Requirement | Purpose |
| ------------- | --------- |
| **Python 3.10+** | Runtime |
| **DeepL API key** | Translation (`DEEPL_AUTH_KEY` in `.env`) |
| **Google API key** (optional) | Gemini Flash OCR correction (`GOOGLE_API_KEY` in `.env`, used with `--fix-ocr`) |
| **Pandoc** (optional) | Required only for `--format docx` |
| **Internet access** | DeepL API, Gemini API, and first-time EasyOCR model downloads |

EasyOCR pulls in PyTorch. The first install can take time and may download large wheels. The first OCR run may also download model files.

If `pip install` fails on Windows with a file-lock error such as "the process cannot access the file because it is being used by another process", close any Python processes using that virtual environment and retry.

## Installation

### Development setup

```powershell
cd E:\MyDevTools\dl-translator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### DeepL configuration

1. Create a [DeepL API Free](https://www.deepl.com/pro-api) or Pro account.
2. Copy `.env.example` to `.env`.
3. Set your API key:

```env
DEEPL_AUTH_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx
```

Free-tier keys commonly end with `:fx`, which allows the DeepL client to use the free endpoint automatically.

### Gemini Flash configuration (optional)

For AI-powered OCR correction with `--fix-ocr`:

1. Get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Add to `.env`:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Gemini 2.0 Flash free tier allows 15 requests/minute and 1M tokens/minute, which is sufficient for most document workflows.

### DOCX export support

If you want DOCX output, install Pandoc:

```powershell
winget install --id JohnMacFarlane.Pandoc
```

## Running the tool

After activating the virtual environment, run the installed CLI command:

```powershell
cd E:\MyDevTools\dl-translator
.\.venv\Scripts\Activate.ps1
dl-translate --help
```

### Translate a single file

```powershell
dl-translate --format md ".\document.pdf"
```

### Translate with Gemini OCR correction

```powershell
dl-translate --fix-ocr --format md ".\scanned-document.pdf"
```

This enables both Layer 2 OCR correction and post-translation semantic review via Gemini Flash.

### Translate a single file to DOCX

```powershell
dl-translate --format docx ".\document.pdf"
```

### Process a folder recursively

```powershell
dl-translate --format md ".\docs"
```

### Dry run

```powershell
dl-translate --dry-run --format md ".\incoming"
```

### Extract Markdown only, without translation

```powershell
dl-translate --extract-only ".\scan.pdf"
```

### Resume an interrupted run

Simply re-run the same command. The pipeline detects existing checkpoint files and skips completed phases:

```powershell
dl-translate --fix-ocr --format md ".\document.pdf"
# Output:
#   Phase 1 (extract): skip — document_extract.md exists
#   Phase 2 (OCR clean): skip — document_es.md exists
#   Phase 3 (translate): translating...
```

To force a full re-run, delete the intermediate files (`_extract.md`, `_es.md`, `_en.md`).

## CLI reference

| Argument / option | Description |
| ------------------- | ------------- |
| `paths` | One or more files, directories, or globs such as `*.pdf` or `docs\**\*.docx`. |
| `-f`, `--format` | Output format: `md` or `docx`. If omitted in an interactive terminal, you will be prompted. |
| `--no-recursive` | Disable default recursive traversal for directory inputs. |
| `--target-lang` | Force the target language: `EN` or `ES`. If omitted, the tool detects the source language and chooses the opposite. |
| `--force-ocr` | Force OCR for all PDF pages instead of using any available text layer. |
| `--fix-ocr` | Use Gemini Flash to fix garbled OCR text from ornamental or unclear fonts. Also enables post-translation semantic review. Requires `GOOGLE_API_KEY` in `.env`. |
| `--gpu` | Enable GPU-backed EasyOCR if CUDA is available. |
| `--dry-run` | Show which files would be processed without calling DeepL. |
| `--continue-on-error` | Continue processing additional files if one fails. |
| `--extract-only` | Skip DeepL and write `{stem}_extract.md` next to the source file. |

## How OCR correction works

### Layer 1: Local dictionary-based fixes (always active for OCR text)

Uses `rapidfuzz` and `wordfreq` to detect and fix common OCR character confusions:

| OCR output | Likely intended | Confusion |
|-----------|----------------|-----------|
| `h0la` | `hola` | `0` → `o` |
| `FRED@` | `FREDA` | `@` → `a` |
| `COLEGIQ` | `COLEGIO` | `Q` → `O` |

Each token is checked against language-specific word frequency databases. If a substitution produces a significantly more common word, it replaces the original.

### Layer 2: Gemini Flash AI correction (opt-in with `--fix-ocr`)

For text that local correction can't fix (ornamental fonts, garbled sequences), the text is sent to Gemini 2.0 Flash with:
- A system prompt specialized for OCR post-correction
- The source document filename as a title hint (helps recover garbled title pages)
- Language context

Gemini processes text in 4K-character chunks, preserving Markdown structure and fenced code blocks.

### Post-translation review (Phase 4)

When `--fix-ocr` is enabled, the translated output also goes through a Gemini review pass that checks for semantic inconsistencies caused by residual OCR errors propagating through translation.

## Booklet PDF support

The tool auto-detects **saddle-stitch/booklet PDFs** where each physical page contains two book pages side by side (landscape orientation). When detected:

1. Each PDF page is split vertically into left and right halves.
2. Printed page numbers are detected via OCR near the bottom corners.
3. Half-pages are reordered by their printed page number.
4. Unnumbered pages (covers, title pages) are placed first.
5. OCR text within each half-page is spatially grouped into paragraphs.

This is common in educational booklets, pamphlets, and print-ready documents.

## Format-specific behavior

### PDF

- Uses **PyMuPDF**.
- If text is available, the extractor prefers the PDF text layer.
- If little or no text is found, pages are rasterized and OCR'd.
- Booklet layouts are auto-detected and split.
- Exported PDF images are written to `{stem}_assets/`.

### DOCX

- Uses **python-docx**.
- Maps Word heading styles to Markdown headings.
- Converts tables to Markdown tables.
- Exports inline images to `{stem}_assets/`.

### Markdown

- Reads the file as UTF-8 with replacement fallback.
- Preserves YAML front matter.
- Skips fenced code blocks during translation.

### Images

- Uses **Pillow** + **EasyOCR**.
- OCR text is spatially grouped into paragraphs using bounding box positions.
- Continuation lines are joined based on punctuation and capitalization.

## Production deployment

This project is suitable for small internal automation and batch document pipelines.

### Recommended deployment model

1. Create a dedicated Python virtual environment.
2. Inject `DEEPL_AUTH_KEY` and optionally `GOOGLE_API_KEY` as environment variables or secrets.
3. Install Pandoc only if DOCX export is required.
4. Use non-interactive flags such as `--format md` for automation.
5. Send stdout/stderr to your logging platform or wrapper script.

### Secret management

Never commit `.env` files. In production, prefer:

- GitHub Actions secrets
- Azure Key Vault
- Docker secrets
- Kubernetes Secrets
- environment variables provided by the host

### Quota planning

- **DeepL Free:** 500,000 characters per month. Use `--dry-run` and `--extract-only` to estimate batch sizes.
- **Gemini Flash Free:** 15 requests/minute, 1M tokens/minute. Sufficient for most documents.

### Performance notes

- OCR on CPU can be slow, especially for scanned PDFs.
- Booklet splitting doubles the number of OCR passes (two halves per page).
- The first OCR run downloads EasyOCR models.
- GPU acceleration is optional and only helps if CUDA-compatible PyTorch is installed.

## Claude Code skill

A `/translate-file` skill is available at `.claude/skills/translate-file/`. When working in this repo, Claude Code auto-discovers it. For global use, copy the folder to `~/.claude/skills/translate-file/`. See the skill's [README](.claude/skills/translate-file/README.md) for installation options.

## Testing

Run the test suite with:

```powershell
cd E:\MyDevTools\dl-translator
.\.venv\Scripts\Activate.ps1
pytest -q
```

Code quality tools:

```powershell
black src/ tests/          # formatting
flake8 src/ tests/         # linting
```

## Project layout

```text
src/dl_translator/
  __main__.py
  cli.py                # Typer entry point
  pipeline.py           # phased pipeline with checkpoint resumption
  discovery.py          # file and glob discovery
  booklet.py            # booklet PDF splitting and reordering
  paragraph_join.py     # OCR line joining into paragraphs
  md_translate.py       # front matter and fenced-code protection
  ocr_engine.py         # confidence-aware EasyOCR with spatial grouping
  ocr_cleanup.py        # two-layer OCR correction (local + Gemini)
  gemini_fix.py         # Gemini Flash OCR and translation review
  output_docx.py        # Markdown -> DOCX via Pandoc + Arial enforcement
  translate.py          # DeepL client and chunking
  extractors/
    common.py
    docx.py
    image.py
    md.py
    pdf.py
tests/
  test_md_translate.py
  test_output_docx.py
  test_gemini_fix.py
.claude/skills/
  translate-file/       # Claude Code skill
.plan/
  document-translator-tool-plan.md
```

## Limitations

- Complex multi-column documents or floating-layout PDFs may not convert perfectly to Markdown.
- OCR quality depends on scan quality, page rotation, image resolution, and available compute.
- Heavily stylized ornamental fonts may produce garbled text that even Gemini cannot fully recover.
- Booklet page number detection depends on OCR recognizing small digits near page corners.
- DOCX export quality depends on Pandoc's Markdown interpretation.
- The current implementation is focused on English/Spanish workflows only.

## Troubleshooting

### `DEEPL_AUTH_KEY is not set`

Make sure `.env` exists or the variable is exported in the shell before running the CLI.

### `--fix-ocr` has no effect

Ensure `GOOGLE_API_KEY` is set in `.env`. The tool silently falls back to local-only correction if the key is missing.

### DOCX export fails

Install Pandoc and confirm `pandoc --version` works in the same shell session.

### OCR is slow

That is expected for scanned PDFs on CPU. Reduce batch size, use `--extract-only` for debugging, or enable `--gpu` if CUDA is available. Booklet PDFs take roughly twice as long due to the page splitting.

### Pipeline skips phases unexpectedly

The pipeline detects checkpoint files on disk. Delete `_extract.md`, `_es.md`, and `_en.md` files next to the source to force a full re-run.

### EasyOCR downloads models on first run

This is expected. Keep network access available for the first OCR execution.

## License

Specify a license before distributing the repository broadly outside your account or organization.
