# Supported Formats Reference

## Input Formats

| Format | Extensions | Extraction Method | Notes |
|--------|-----------|-------------------|-------|
| **PDF (text)** | `.pdf` | PyMuPDF text extraction | Preferred when text layer exists |
| **PDF (scanned)** | `.pdf` | PyMuPDF rasterize + EasyOCR | Auto-fallback when text layer is sparse |
| **DOCX** | `.docx` | python-docx | Preserves headings, tables, inline images |
| **Markdown** | `.md`, `.markdown` | Direct UTF-8 read | Preserves YAML front matter and code fences |
| **PNG** | `.png` | Pillow + EasyOCR | |
| **JPEG** | `.jpg`, `.jpeg` | Pillow + EasyOCR | |
| **WebP** | `.webp` | Pillow + EasyOCR | |
| **TIFF** | `.tif`, `.tiff` | Pillow + EasyOCR | |
| **BMP** | `.bmp` | Pillow + EasyOCR | |

## Output Formats

| Format | Extension | Requirements |
|--------|-----------|-------------|
| **Markdown** | `.md` | None (default) |
| **DOCX** | `.docx` | Pandoc must be installed |

## Extraction Pipeline

```
PDF (text layer) -> PyMuPDF Markdown extraction -> translate -> output
PDF (scanned)    -> rasterize -> EasyOCR -> Markdown -> translate -> output
DOCX             -> python-docx heading/table mapping -> Markdown -> translate -> output
Markdown         -> direct read (preserve front matter + code fences) -> translate -> output
Image            -> Pillow load -> EasyOCR -> Markdown -> translate -> output
```

## Preservation Rules

- **YAML front matter** (`---` delimited) is preserved unchanged
- **Fenced code blocks** (``` delimited) are preserved unchanged
- **Headings** from DOCX are mapped to Markdown `#` levels
- **Tables** from DOCX are mapped to Markdown pipe tables
- **Embedded images** from PDF/DOCX are exported to `{stem}_assets/`

## Language Support

| Direction | DeepL Target Code |
|-----------|------------------|
| English -> Spanish | `ES` |
| Spanish -> English | `EN-US` |

Source language is detected automatically by sending a sample to DeepL unless `--target-lang` is specified.
