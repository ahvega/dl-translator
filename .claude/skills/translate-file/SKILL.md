---
name: translate-file
description: "Translate documents (PDF, DOCX, Markdown, images) between English and Spanish using the DeepL API. Use when the user says /translate-file, asks to translate a document, convert a PDF/DOCX/image to another language, or translate between English and Spanish. Supports single files, directories, and glob patterns."
allowed-tools: Bash, Read, Glob, Grep
---

# /translate-file - Translate Documents EN/ES

Translate PDF, DOCX, Markdown, and image files between English and Spanish using the DeepL API via the `dl-translate` CLI.

## Usage

```
/translate-file <path(s) or glob> [--format md|docx] [--target-lang EN|ES] [--extract-only] [--force-ocr] [--gpu]
```

### Examples

```
/translate-file report.pdf
/translate-file report.pdf --format docx --target-lang ES
/translate-file documents/*.docx --format md
/translate-file scan.pdf --force-ocr
/translate-file image.png
/translate-file ./incoming/ --format md
/translate-file report.pdf --extract-only
```

## Workflow

### 1. Parse user input

Extract from `$ARGUMENTS`:
- **File paths, directories, or glob patterns** (required)
- **Output format** (optional, default: `md`): `md` or `docx`
- **Target language** (optional, auto-detected): `EN` or `ES`
- **Extract-only mode** (optional): skip translation, output Markdown extraction only
- **Force OCR** (optional): OCR all PDF pages regardless of text layer
- **GPU** (optional): use GPU for EasyOCR if CUDA available

If the user provides a directory, `dl-translate` processes it recursively by default.

### 2. Check prerequisites

Before running, verify the environment:

```bash
python -c "import dl_translator" 2>/dev/null && echo "OK" || echo "NOT_INSTALLED"
```

If `dl-translator` is not installed:
1. Check if a venv exists at the project root or a known location.
2. Suggest installation:
   ```bash
   pip install -e "E:/MyDevTools/dl-translator[dev]"
   ```
   Or if working outside the repo:
   ```bash
   pip install dl-translator
   ```

Verify the DeepL API key is configured:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; key=os.environ.get('DEEPL_AUTH_KEY',''); print('KEY_SET' if key.strip() else 'KEY_MISSING')"
```

If `KEY_MISSING`, tell the user to set `DEEPL_AUTH_KEY` in `.env` or as an environment variable. Link them to [DeepL API Free](https://www.deepl.com/pro-api) to get a key.

### 3. Resolve and confirm files

Use the Glob tool to expand any glob patterns. Show the user:
- Number of files to be processed
- File types detected
- Output format
- Target language (or "auto-detect")

Ask for confirmation if more than 5 files will be processed.

### 4. Run the translation

Build and execute the `dl-translate` command:

```bash
dl-translate --format <format> [--target-lang <lang>] [--force-ocr] [--gpu] [--extract-only] [--continue-on-error] "<path1>" "<path2>" ...
```

**Key flags:**
- Always pass `--format` explicitly (default to `md` if user didn't specify)
- Add `--continue-on-error` when processing multiple files
- Pass `--target-lang` only if the user specified a language; otherwise let the tool auto-detect

If `dl-translate` is not on PATH (common when venv is not activated), use:

```bash
python -m dl_translator.cli <args>
```

Or activate the venv first:

```bash
source "E:/MyDevTools/dl-translator/.venv/Scripts/activate" && dl-translate <args>
```

### 5. Report results

After execution:
- Show which output files were created and their locations
- For OCR inputs, note that a source-language Markdown reference file was also created
- Report any errors
- If DOCX output was requested and failed, check if Pandoc is installed

## Supported Formats

See [references/supported-formats.md](references/supported-formats.md) for detailed format information.

**Input:** PDF, DOCX, Markdown (.md), PNG, JPG, JPEG, WebP, TIFF, BMP
**Output:** Markdown (.md) or DOCX (requires Pandoc)

## Output Naming

- Translated files: `{stem}_{en|es}.{md|docx}` next to the source
- Asset images: `{stem}_assets/` directory
- OCR source text: `{stem}_{source_lang}.md` (only for scanned/OCR inputs)
- Extract-only: `{stem}_extract.md`

## Error Handling

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `DEEPL_AUTH_KEY is not set` | Missing API key | Set in `.env` or environment |
| `Unsupported file type` | File extension not recognized | Check supported formats |
| DOCX export fails | Pandoc not installed | `winget install pandoc` |
| OCR is very slow | CPU-only processing | Use `--gpu` if CUDA available |
| Import error | dl-translator not installed | `pip install -e ".[dev]"` |

## Important Notes

- Translation direction is EN/ES only. Source language is auto-detected unless `--target-lang` is specified.
- DeepL Free tier has a 500,000 character/month limit. Use `--extract-only` to preview content size before translating large batches.
- The first OCR run downloads EasyOCR models (~100MB). Requires internet access.
- DOCX output requires Pandoc installed and on PATH.
