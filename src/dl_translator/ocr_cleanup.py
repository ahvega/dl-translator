from __future__ import annotations

import itertools
import re

from rapidfuzz import fuzz
from wordfreq import zipf_frequency

_FENCED_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9@$§!|]{3,}")

_OCR_CONFUSIONS: dict[str, tuple[str, ...]] = {
    "0": ("o",),
    "1": ("i", "l"),
    "3": ("e",),
    "4": ("a",),
    "5": ("s",),
    "6": ("g",),
    "7": ("t",),
    "8": ("b",),
    "@": ("a",),
    "$": ("s",),
    "§": ("s",),
    "!": ("i", "l"),
    "|": ("i", "l"),
}


def _wordfreq_lang(language: str) -> str:
    upper = language.upper()
    if upper.startswith("ES"):
        return "es"
    return "en"


def _restore_case(original: str, candidate: str) -> str:
    if original.isupper():
        return candidate.upper()
    if original.istitle():
        return candidate.capitalize()
    return candidate


def _looks_suspicious(token: str, lang: str) -> bool:
    lowered = token.lower()
    if any(ch in _OCR_CONFUSIONS for ch in lowered):
        return True
    return zipf_frequency(lowered, lang) < 1.5 and any(ch.isdigit() for ch in token)


def _candidate_variants(token: str) -> set[str]:
    lowered = token.lower()
    options: list[tuple[str, ...]] = []
    changeable = 0
    for ch in lowered:
        if ch in _OCR_CONFUSIONS and changeable < 5:
            options.append((ch, *_OCR_CONFUSIONS[ch]))
            changeable += 1
        else:
            options.append((ch,))

    variants: set[str] = {lowered}
    for combo in itertools.product(*options):
        candidate = "".join(combo)
        if candidate != lowered and candidate.isalpha():
            variants.add(candidate)
        if len(variants) >= 32:
            break
    return variants


def clean_ocr_token(token: str, language: str) -> str:
    lang = _wordfreq_lang(language)
    if not _looks_suspicious(token, lang):
        return token

    original = token
    original_lower = original.lower()
    original_score = zipf_frequency(original_lower, lang)
    best = original_lower
    best_score = original_score

    for candidate in _candidate_variants(original):
        freq = zipf_frequency(candidate, lang)
        similarity = fuzz.ratio(original_lower, candidate) / 100.0
        score = freq + (similarity * 0.75)
        if score > best_score:
            best = candidate
            best_score = score

    if best == original_lower:
        return token

    best_freq = zipf_frequency(best, lang)
    original_freq = zipf_frequency(original_lower, lang)
    if best_freq < 2.0 or best_freq <= original_freq + 0.4:
        return token

    return _restore_case(original, best)


def _clean_text_segment(text: str, language: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return clean_ocr_token(match.group(0), language)

    return _TOKEN_RE.sub(replace, text)


def clean_ocr_markdown(
    markdown: str,
    language: str,
    fix_ocr: bool = False,
    source_filename: str | None = None,
) -> str:
    """Clean OCR text with local corrections and optional Gemini fix.

    Layer 1: rapidfuzz + wordfreq character-substitution fixes.
    Layer 2 (fix_ocr=True): Gemini Flash for semantic correction.
    """
    # Layer 1: local dictionary-based correction
    parts: list[str] = []
    last = 0
    for match in _FENCED_BLOCK.finditer(markdown):
        if match.start() > last:
            parts.append(_clean_text_segment(markdown[last : match.start()], language))
        parts.append(match.group(0))
        last = match.end()
    if last < len(markdown):
        parts.append(_clean_text_segment(markdown[last:], language))
    result = "".join(parts)

    # Layer 2: Gemini Flash post-correction
    if fix_ocr:
        from dl_translator.gemini_fix import fix_ocr_with_gemini

        result = fix_ocr_with_gemini(result, language, source_filename=source_filename)

    return result
