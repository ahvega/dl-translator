from __future__ import annotations

from pathlib import Path

from dl_translator.extractors.common import ExtractResult


def extract_markdown_file(path: Path) -> ExtractResult:
    text = path.read_text(encoding="utf-8", errors="replace")
    return ExtractResult(markdown=text)
