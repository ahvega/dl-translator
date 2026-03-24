"""Join OCR text lines into proper paragraphs.

Rules:
- If a line does NOT end with sentence-ending punctuation (. ? !)
  and the next line starts with a lowercase letter, join with a space
  (it's a continuation of the same paragraph).
- A paragraph break is kept when a line ends with . ? ! and the
  next line starts with an uppercase letter.
- Lines that are ALL CAPS are treated as headings/labels and always
  get their own paragraph.
"""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"[.?!:;]\s*$")
_STARTS_LOWER = re.compile(r"^[a-záéíóúüñ]")
_ALL_CAPS = re.compile(r"^[A-ZÁÉÍÓÚÜÑ\s\d.,;:!?()]+$")


def join_paragraphs(text: str) -> str:
    """Join continuation lines into paragraphs."""
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    result: list[str] = []
    buf = lines[0]

    for i in range(1, len(lines)):
        cur = lines[i]

        # Empty line = explicit paragraph break
        if not cur.strip():
            result.append(buf)
            result.append("")
            buf = ""
            continue

        # If buffer is empty, start fresh
        if not buf.strip():
            buf = cur
            continue

        # ALL CAPS lines are headings — always new paragraph
        if _ALL_CAPS.match(cur.strip()) and len(cur.strip()) > 3:
            result.append(buf)
            buf = cur
            continue

        # Previous line ends with sentence punctuation AND
        # current line starts with uppercase → paragraph break
        if _SENTENCE_END.search(buf) and not _STARTS_LOWER.match(cur.lstrip()):
            result.append(buf)
            buf = cur
            continue

        # Current line starts with lowercase → continuation
        if _STARTS_LOWER.match(cur.lstrip()):
            buf = buf.rstrip() + " " + cur.lstrip()
            continue

        # Default: if previous doesn't end with punctuation,
        # likely continuation
        if not _SENTENCE_END.search(buf):
            buf = buf.rstrip() + " " + cur.lstrip()
            continue

        # Otherwise new paragraph
        result.append(buf)
        buf = cur

    if buf:
        result.append(buf)

    return "\n".join(result)


def join_markdown_paragraphs(markdown: str) -> str:
    """Apply paragraph joining to markdown, preserving structure.

    Skips headings (## Page N), horizontal rules (---),
    image references (![](...)), and fenced code blocks.
    """
    blocks = markdown.split("\n\n")
    result: list[str] = []

    for block in blocks:
        stripped = block.strip()
        # Skip structural elements
        if (
            stripped.startswith("#")
            or stripped.startswith("---")
            or stripped.startswith("![")
            or stripped.startswith("```")
            or not stripped
        ):
            result.append(block)
        else:
            result.append(join_paragraphs(block))

    return "\n\n".join(result)
