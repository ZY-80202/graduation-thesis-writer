from __future__ import annotations

from typing import Sequence

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH

from thesis_skill.docx_writer.style_manager import caption_style


def add_data_table(document: DocxDocument, caption: str, rows: Sequence[Sequence[str]]) -> None:
    caption_para = document.add_paragraph(caption, style=caption_style(document))
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if not rows:
        return
    table = document.add_table(rows=len(rows), cols=max(len(row) for row in rows))
    table.style = "Table Grid"
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            table.cell(row_index, col_index).text = str(value)
    document.add_paragraph("")
