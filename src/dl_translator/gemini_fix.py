"""Gemini Flash OCR post-correction for low-confidence text."""

from __future__ import annotations

import os
import re

_FENCED_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)

_SYSTEM_PROMPT = """\
You are an OCR post-correction assistant. The user will give you text \
that was extracted from a scanned document using OCR. The OCR engine \
may have misread characters, especially from ornamental or decorative \
fonts.

Your task:
1. Fix obvious OCR errors (wrong characters, merged/split words, \
   garbled sequences).
2. Preserve the original meaning and structure.
3. Keep Markdown formatting (headings, lists, tables) intact.
4. Do NOT translate — keep the text in its original language.
5. Do NOT add, remove, or rephrase content beyond fixing OCR errors.
6. If a word looks correct, leave it unchanged.

Return ONLY the corrected text, nothing else."""

_REVIEW_PROMPT = """\
You are a translation quality reviewer. The user will give you text \
that was translated from OCR-extracted content. The original OCR may \
have had errors that propagated into the translation.

Your task:
1. Fix semantic inconsistencies caused by OCR errors in the source.
2. Fix awkward phrasing that resulted from translating garbled input.
3. Ensure the text reads naturally in the target language.
4. Keep Markdown formatting (headings, lists, tables) intact.
5. Do NOT change the target language or translate back.
6. If the text reads well, return it unchanged.

Return ONLY the reviewed text, nothing else."""

_MAX_CHUNK = 4000


def _get_language_hint(language: str) -> str:
    u = language.upper()
    if u.startswith("ES"):
        return "Spanish"
    return "English"


def _get_gemini_model():
    """Return a configured Gemini GenerativeModel, or None."""
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=key)
        return client
    except Exception:
        return None


def fix_ocr_with_gemini(
    text: str,
    language: str,
    low_confidence_hint: str | None = None,
    source_filename: str | None = None,
) -> str:
    """Send OCR text to Gemini Flash for correction.

    Returns the original text unchanged if Gemini is unavailable.
    """
    client = _get_gemini_model()
    if client is None:
        return text

    lang_hint = _get_language_hint(language)
    user_msg = f"Language: {lang_hint}\n\n"
    if source_filename:
        user_msg += (
            f'The document filename is "{source_filename}".'
            " This is likely the title of the document and"
            " can help you recover garbled title text.\n\n"
        )
    if low_confidence_hint:
        user_msg += (
            "The following words had low OCR confidence"
            f" and likely contain errors: {low_confidence_hint}\n\n"
        )
    user_msg += "OCR text to correct:\n\n"

    # Process text in chunks, skipping fenced code blocks
    parts: list[str] = []
    last = 0
    for m in _FENCED_BLOCK.finditer(text):
        if m.start() > last:
            segment = text[last : m.start()]
            parts.append(_fix_segment(client, user_msg, segment))
        parts.append(m.group(0))
        last = m.end()
    if last < len(text):
        segment = text[last:]
        parts.append(_fix_segment(client, user_msg, segment))
    return "".join(parts)


def _fix_segment(client, user_prefix: str, segment: str) -> str:
    """Fix a single text segment, chunking if needed."""
    if not segment.strip():
        return segment

    if len(segment) <= _MAX_CHUNK:
        return _call_gemini(client, user_prefix + segment)

    # Split on double newlines for chunking
    paragraphs = segment.split("\n\n")
    fixed: list[str] = []
    buf: list[str] = []
    buf_len = 0

    for para in paragraphs:
        added_len = len(para) if not buf else len("\n\n") + len(para)
        if buf_len + added_len > _MAX_CHUNK and buf:
            chunk = "\n\n".join(buf)
            fixed.append(_call_gemini(client, user_prefix + chunk))
            buf = [para]
            buf_len = len(para)
        else:
            buf.append(para)
            buf_len += added_len

    if buf:
        chunk = "\n\n".join(buf)
        fixed.append(_call_gemini(client, user_prefix + chunk))

    return "\n\n".join(fixed)


def _call_gemini(client, prompt: str) -> str:
    """Make a single Gemini API call."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "system_instruction": _SYSTEM_PROMPT,
                "temperature": 0.1,
                "max_output_tokens": 8192,
            },
        )
        result = response.text
        if result and result.strip():
            return result.strip()
    except Exception:
        pass
    # Return original (strip the user_prefix back out)
    # The prompt includes the prefix, so we can't easily recover.
    # Caller handles this by passing segment separately.
    return prompt.split("OCR text to correct:\n\n", 1)[-1]


def review_translation_with_gemini(text: str, language: str) -> str:
    """Review translated text for semantic consistency.

    Returns the original text unchanged if Gemini is unavailable.
    """
    client = _get_gemini_model()
    if client is None:
        return text

    lang_hint = _get_language_hint(language)
    user_msg = f"Target language: {lang_hint}\n\n" "Translated text to review:\n\n"

    parts: list[str] = []
    last = 0
    for m in _FENCED_BLOCK.finditer(text):
        if m.start() > last:
            segment = text[last : m.start()]
            parts.append(_review_segment(client, user_msg, segment))
        parts.append(m.group(0))
        last = m.end()
    if last < len(text):
        segment = text[last:]
        parts.append(_review_segment(client, user_msg, segment))
    return "".join(parts)


def _review_segment(client, user_prefix: str, segment: str) -> str:
    """Review a single text segment for semantic consistency."""
    if not segment.strip():
        return segment

    if len(segment) <= _MAX_CHUNK:
        return _call_gemini_review(client, user_prefix + segment)

    paragraphs = segment.split("\n\n")
    fixed: list[str] = []
    buf: list[str] = []
    buf_len = 0

    for para in paragraphs:
        added_len = len(para) if not buf else len("\n\n") + len(para)
        if buf_len + added_len > _MAX_CHUNK and buf:
            chunk = "\n\n".join(buf)
            fixed.append(_call_gemini_review(client, user_prefix + chunk))
            buf = [para]
            buf_len = len(para)
        else:
            buf.append(para)
            buf_len += added_len

    if buf:
        chunk = "\n\n".join(buf)
        fixed.append(_call_gemini_review(client, user_prefix + chunk))

    return "\n\n".join(fixed)


def _call_gemini_review(client, prompt: str) -> str:
    """Make a Gemini API call for translation review."""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "system_instruction": _REVIEW_PROMPT,
                "temperature": 0.1,
                "max_output_tokens": 8192,
            },
        )
        result = response.text
        if result and result.strip():
            return result.strip()
    except Exception:
        pass
    return prompt.split("Translated text to review:\n\n", 1)[-1]
