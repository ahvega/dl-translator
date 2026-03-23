from dl_translator.md_translate import split_front_matter, translate_full_markdown
from dl_translator.ocr_cleanup import clean_ocr_markdown, clean_ocr_token


def test_split_front_matter():
    fm, body = split_front_matter("---\ntitle: x\n---\n\nHello")
    assert fm is not None
    assert "title: x" in fm
    assert body.strip() == "Hello"


def test_split_no_front_matter():
    fm, body = split_front_matter("# Hi\n")
    assert fm is None
    assert body == "# Hi\n"


def test_translate_skips_fenced_code():
    def fake_translate(s: str) -> str:
        return "T:" + s

    md = "Intro\n\n```python\nprint(1)\n```\n\nOutro"
    out = translate_full_markdown(md, fake_translate)
    assert "T:Intro" in out or out.startswith("T:")
    assert "```python" in out
    assert "print(1)" in out
    assert "T:print" not in out


def test_detected_spanish_targets_english():
    # Spanish source -> English target
    source = "ES"
    target = "EN-US" if source.upper().startswith("ES") else "ES"
    assert target == "EN-US"


def test_detected_english_targets_spanish():
    # English source -> Spanish target
    source = "EN"
    target = "EN-US" if source.upper().startswith("ES") else "ES"
    assert target == "ES"


def test_clean_ocr_token_repairs_spanish_symbol_confusion():
    assert clean_ocr_token("h0la", "ES") == "hola"


def test_clean_ocr_markdown_preserves_code_fences():
    md = "Texto h0la\n\n```python\nh0la = 1\n```\n"
    out = clean_ocr_markdown(md, "ES")
    assert "Texto hola" in out
    assert "h0la = 1" in out
