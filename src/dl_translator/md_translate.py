from __future__ import annotations

import re
from collections.abc import Callable

_FENCED_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def split_front_matter(text: str) -> tuple[str | None, str]:
    """Return (front_matter, body) if YAML front matter exists, else (None, full)."""
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    if len(lines) < 2:
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[: i + 1])
            body = "\n".join(lines[i + 1 :])
            return fm, body
    return None, text


def translate_markdown_body(
    body: str,
    translate_chunk: Callable[[str], str],
) -> str:
    """Translate markdown body while leaving fenced ``` code blocks unchanged."""
    parts: list[str] = []
    last = 0
    for m in _FENCED_BLOCK.finditer(body):
        if m.start() > last:
            parts.append(translate_chunk(body[last : m.start()]))
        parts.append(m.group(0))
        last = m.end()
    if last < len(body):
        parts.append(translate_chunk(body[last:]))
    return "".join(parts)


def translate_full_markdown(
    md: str,
    translate_chunk: Callable[[str], str],
) -> str:
    """Leave YAML front matter unchanged; translate body with fenced code preserved."""
    fm, body = split_front_matter(md)
    if fm is None:
        return translate_markdown_body(md, translate_chunk)
    translated_body = translate_markdown_body(body, translate_chunk)
    sep = "\n" if body and not body.startswith("\n") else ""
    return fm + sep + translated_body
