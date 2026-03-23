from docx import Document

from dl_translator.output_docx import _enforce_arial_font


def test_enforce_arial_font_updates_existing_runs(tmp_path):
    path = tmp_path / "sample.docx"
    doc = Document()
    paragraph = doc.add_paragraph()
    run = paragraph.add_run("Hello")
    run.font.name = "Times New Roman"
    doc.save(path)

    _enforce_arial_font(path)

    updated = Document(path)
    assert updated.paragraphs[0].runs[0].font.name == "Arial"


def test_enforce_arial_font_updates_nested_table_runs(tmp_path):
    path = tmp_path / "nested.docx"
    doc = Document()
    outer = doc.add_table(rows=1, cols=1)
    cell = outer.cell(0, 0)
    nested = cell.add_table(rows=1, cols=1)
    run = nested.cell(0, 0).paragraphs[0].add_run("Nested")
    run.font.name = "Calibri"
    doc.save(path)

    _enforce_arial_font(path)

    updated = Document(path)
    nested_run = updated.tables[0].cell(0, 0).tables[0].cell(0, 0).paragraphs[0].runs[0]
    assert nested_run.font.name == "Arial"
