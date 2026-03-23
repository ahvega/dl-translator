from __future__ import annotations

import os
from typing import TYPE_CHECKING

import deepl

if TYPE_CHECKING:
    from deepl import Translator

_MAX_CHARS_PER_REQUEST = 45000


def get_translator() -> "Translator":
    key = os.environ.get("DEEPL_AUTH_KEY")
    if not key or not key.strip():
        raise RuntimeError(
            "DEEPL_AUTH_KEY is not set. Copy .env.example"
            " to .env and add your DeepL API key."
        )
    return deepl.Translator(key.strip())


def normalize_target_for_deepl(lang: str) -> str:
    u = lang.upper().replace("_", "-")
    if u in ("EN", "EN-US", "EN-GB"):
        return "EN-US"
    if u == "ES":
        return "ES"
    raise ValueError(f"Unsupported target language: {lang!r} (use EN or ES)")


def detect_source_lang(translator: "Translator", sample_text: str) -> str:
    """Detect source language via DeepL. Returns 'EN' or 'ES'."""
    sample = sample_text.strip()
    if not sample:
        return "EN"
    chunk = sample[:1000]
    result = translator.translate_text(chunk, target_lang="EN-US")
    code = getattr(result, "detected_source_lang", None)
    if code is None:
        return "EN"
    c = str(code).upper()
    if c.startswith("ES"):
        return "ES"
    return "EN"


def _split_chunks(text: str, max_chars: int = _MAX_CHARS_PER_REQUEST) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        p = para + "\n\n"
        if size + len(p) > max_chars and buf:
            chunks.append("".join(buf))
            buf = [p]
            size = len(p)
        else:
            buf.append(p)
            size += len(p)
    if buf:
        chunks.append("".join(buf))
    return chunks


def translate_text_chunks(
    translator: "Translator",
    text: str,
    target_lang: str,
    source_lang: str | None = None,
) -> str:
    """Translate long text with paragraph-aware chunking."""
    if not text:
        return text
    kwargs: dict = {"target_lang": target_lang}
    if source_lang and source_lang.upper() not in ("AUTO", ""):
        kwargs["source_lang"] = source_lang.upper()

    out: list[str] = []
    for chunk in _split_chunks(text):
        res = translator.translate_text(chunk, **kwargs)
        out.append(str(res.text))
    return "".join(out)
