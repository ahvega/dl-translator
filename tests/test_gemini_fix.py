import dl_translator.gemini_fix as gemini_fix


def test_fix_segment_counts_double_newline_separators(monkeypatch):
    captured: list[str] = []

    monkeypatch.setattr(gemini_fix, "_MAX_CHUNK", 10)

    def fake_call(client, prompt: str) -> str:
        segment = prompt.split("OCR text to correct:\n\n", 1)[-1]
        captured.append(segment)
        return segment

    monkeypatch.setattr(gemini_fix, "_call_gemini", fake_call)

    segment = "abcde\n\nfghij"
    out = gemini_fix._fix_segment(object(), "OCR text to correct:\n\n", segment)

    assert out == segment
    assert captured == ["abcde", "fghij"]
