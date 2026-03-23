from dl_translator.md_translate import split_front_matter, translate_full_markdown


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
