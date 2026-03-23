# dl-translator

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Typer CLI](https://img.shields.io/badge/CLI-Typer-009688?logo=python&logoColor=white)](https://typer.tiangolo.com/)
[![DeepL API](https://img.shields.io/badge/translation-DeepL-0F2B46?logo=deepl&logoColor=white)](https://www.deepl.com/pro-api)
[![EasyOCR](https://img.shields.io/badge/OCR-EasyOCR-5C2D91)](https://github.com/JaidedAI/EasyOCR)
[![PyMuPDF](https://img.shields.io/badge/PDF-PyMuPDF-0096D6)](https://pymupdf.readthedocs.io/)
[![python-docx](https://img.shields.io/badge/DOCX-python--docx-2B579A)](https://python-docx.readthedocs.io/)
[![Pandoc optional](https://img.shields.io/badge/DOCX%20export-Pandoc-1A1A1A?logo=pandoc&logoColor=white)](https://pandoc.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](https://pytest.org/)

**Author:** Adalberto H. Vega

Convert **PDF**, **DOCX**, **Markdown**, or **images** into **Markdown**, then translate the content between **English** and **Spanish** with the [DeepL API](https://www.deepl.com/pro-api). The tool is designed for local and batch workflows: it detects supported files, extracts readable Markdown, preserves as much structure as practical, and writes the translated file beside the source using `_en` or `_es` suffixes.

## What it does

`dl-translator` is a Python CLI for document localization workflows where the original source may be a text PDF, scanned PDF, Word document, Markdown file, or image.

The pipeline is:

1. Discover one or more input files from explicit paths, folders, or glob patterns.
2. Extract the source into a temporary Markdown representation.
3. Preserve structural elements where possible, especially headings, paragraphs, tables, and embedded images.
4. Detect whether the source is English or Spanish.
5. Translate to the opposite language, or to an explicitly requested target.
6. Save the result as Markdown or DOCX in the same folder as the original file.

## Features

- **Input formats:** PDF, DOCX, Markdown, PNG, JPG, JPEG, WebP, TIFF, and BMP.
- **Scanned PDF support:** pages without a text layer are rasterized and OCR'd with EasyOCR.
- **OCR reference output:** OCR-based inputs also keep a full Markdown copy of the extracted source text in the original detected language for review and traceability.
- **OCR cleanup pass:** OCR-based Markdown goes through a lightweight word-validity cleanup pass that attempts to repair common character confusions such as `0/o`, `1/l/i`, `@/a`, and `$/s`.
- **Heading and table preservation:** DOCX headings and tables are mapped into Markdown; text PDFs use PyMuPDF's Markdown extraction when available.
- **Front matter safety:** YAML front matter in Markdown files is preserved unchanged.
- **Code fence safety:** fenced code blocks are excluded from translation.
- **Asset export:** embedded images from PDF and DOCX are exported to `{stem}_assets/` and linked from Markdown.
- **Batch processing:** recursive folder walking is enabled by default.
- **Flexible output:** write `.md` or `.docx`; interactive runs can prompt for the format if `--format` is omitted.
- **DOCX font normalization:** generated Word documents are normalized to use **Arial**.
- **Final DOCX prompt:** when translated Markdown output is created in an interactive shell, the tool can offer to generate DOCX copies at the end of the run.
- **Windows-friendly usage:** documented with PowerShell examples and venv setup.

## How output files are named

Outputs are written **next to the source file**, using the **target language suffix**:

- `document_en.md`
- `document_es.md`
- `document_en.docx`
- `document_es.docx`

Embedded image exports go to:

- `document_assets/`

For OCR-based inputs such as scanned PDFs and images, the tool also writes a Markdown reference file in the original detected language, for example:

- `document_es.md` for the OCR source text
- `document_en.md` for the translated output

## Architecture

```text
input file/folder/glob
  -> discovery.py
  -> extractor by type
     -> PDF: PyMuPDF text extraction or page OCR
     -> DOCX: python-docx to Markdown
     -> Markdown: direct read
     -> Image: OCR
  -> md_translate.py
     -> preserve front matter
     -> skip fenced code blocks
  -> translate.py
     -> detect source language
     -> chunk long text for DeepL
  -> output
     -> Markdown beside source
     -> optional DOCX via Pandoc
```

## Requirements

| Requirement | Purpose |
| ------------- | --------- |
| **Python 3.10+** | Runtime |
| **DeepL API key** | Translation (`DEEPL_AUTH_KEY` in `.env`) |
| **Pandoc** (optional) | Required only for `--format docx` |
| **Internet access** | DeepL API and first-time EasyOCR model downloads |

EasyOCR pulls in PyTorch. The first install can take time and may download large wheels. The first OCR run may also download model files. OCR cleanup uses `wordfreq` and `rapidfuzz` to make conservative post-processing corrections on likely OCR mistakes.

If `pip install` fails on Windows with a file-lock error such as “the process cannot access the file because it is being used by another process”, close any Python processes using that virtual environment and retry.

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

### DOCX export support

If you want DOCX output, install Pandoc:

```powershell
winget install --id JohnMacFarlane.Pandoc
```

Verify it is available:

```powershell
pandoc --version
```

## Running the tool

After activating the virtual environment, run the installed CLI command:

```powershell
cd E:\MyDevTools\dl-translator
.\.venv\Scripts\Activate.ps1
dl-translate --help
```

This is an installed console command created by the Python package entry point. On Windows it is usually exposed as an `.exe` launcher inside `.venv\Scripts`, not as a separate `dl-translate.ps1` script.

### Translate a single file to Markdown

```powershell
dl-translate --format md ".\document.pdf"
```

### Translate a single file to DOCX

```powershell
dl-translate --format docx ".\document.pdf"
```

### Let the tool ask for output format

```powershell
dl-translate ".\document.pdf"
```

If you choose Markdown output in an interactive shell, the CLI can ask at the end whether you also want DOCX copies of the translated results.

### Process a folder recursively

```powershell
dl-translate --format md ".\docs"
```

Directory inputs are recursive by default. The CLI prints a note when that behavior applies.

### Process a glob pattern

```powershell
dl-translate --format md ".\incoming\*.pdf"
```

### Dry run

```powershell
dl-translate --dry-run --format md ".\incoming"
```

### Extract Markdown only, without translation

```powershell
dl-translate --extract-only ".\scan.pdf"
```

## CLI reference

| Argument / option | Description |
| ------------------- | ------------- |
| `paths` | One or more files, directories, or globs such as `*.pdf` or `docs\**\*.docx`. |
| `-f`, `--format` | Output format: `md` or `docx`. In an interactive shell, the tool prompts if omitted. |
| `--no-recursive` | Disable default recursive traversal for directory inputs. |
| `--target-lang` | Force the target language: `EN` or `ES`. If omitted, the tool detects the source language and chooses the opposite. |
| `--force-ocr` | Force OCR for all PDF pages instead of using any available text layer. |
| `--gpu` | Enable GPU-backed EasyOCR if CUDA is available. |
| `--dry-run` | Show which files would be processed without calling DeepL. |
| `--continue-on-error` | Continue processing additional files if one fails. |
| `--extract-only` | Skip DeepL and write `{stem}_extract.md` next to the source file. |

## How translation works

### Language direction

The tool supports **English** and **Spanish** translation workflows:

- English source -> Spanish output
- Spanish source -> English output

If `--target-lang` is omitted, the CLI sends a sample chunk to DeepL, reads the detected source language, and translates to the opposite language.

### Chunking

DeepL requests are chunked at paragraph boundaries so long documents can be translated without sending a single oversized payload.

### Markdown protection rules

- YAML front matter is left untouched.
- Fenced code blocks are copied verbatim.
- The surrounding Markdown prose is translated.

## Format-specific behavior

### PDF

- Uses **PyMuPDF**.
- If text is available, the extractor prefers the PDF text layer.
- If little or no text is found, pages are rasterized and OCR'd.
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
- OCR text is normalized into a temporary Markdown document before translation.
- A final cleanup pass attempts to fix some obvious OCR mistakes using language-aware word scoring.

## Production deployment

This project is suitable for small internal automation and batch document pipelines.

### Recommended deployment model

1. Create a dedicated Python virtual environment.
2. Inject `DEEPL_AUTH_KEY` as an environment variable or secret.
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

DeepL Free allows **500,000 characters per month**. Because scanned PDFs can expand into a lot of OCR text, estimate batch sizes before large runs and consider using `--dry-run` and smaller batches during rollout.

### Performance notes

- OCR on CPU can be slow, especially for scanned PDFs.
- The first OCR run downloads EasyOCR models.
- GPU acceleration is optional and only helps if CUDA-compatible PyTorch is installed and available.

### Operational recommendations

- Keep the tool in a dedicated worker environment for large batches.
- Use `--continue-on-error` in unattended jobs.
- Keep input and output directories separate if downstream consumers watch translated files.
- Add your own wrapper job if you need metrics, retries, scheduling, or alerting.

## Testing

Run the test suite with:

```powershell
cd E:\MyDevTools\dl-translator
.\.venv\Scripts\Activate.ps1
pytest -q
```

## Project layout

```text
src/dl_translator/
  __main__.py
  cli.py              # Typer entry point
  discovery.py        # file and glob discovery
  md_translate.py     # front matter and fenced-code protection
  ocr_engine.py       # EasyOCR loader
  output_docx.py      # Markdown -> DOCX via Pandoc
  translate.py        # DeepL client and chunking
  extractors/
    common.py
    docx.py
    image.py
    md.py
    pdf.py
tests/
  test_md_translate.py
```

## Limitations

- Complex multi-column documents or floating-layout PDFs may not convert perfectly to Markdown.
- OCR quality depends on scan quality, page rotation, image resolution, and available compute.
- DOCX export quality depends on Pandoc's Markdown interpretation.
- The current implementation is focused on English/Spanish workflows only.

## Troubleshooting

### `DEEPL_AUTH_KEY is not set`

Make sure `.env` exists or the variable is exported in the shell before running the CLI.

### DOCX export fails

Install Pandoc and confirm `pandoc --version` works in the same shell session.

### OCR is slow

That is expected for scanned PDFs on CPU. Reduce batch size, use `--extract-only` for debugging, or enable `--gpu` if CUDA is available.

### EasyOCR downloads models on first run

This is expected. Keep network access available for the first OCR execution.

## License

Specify a license before distributing the repository broadly outside your account or organization.
