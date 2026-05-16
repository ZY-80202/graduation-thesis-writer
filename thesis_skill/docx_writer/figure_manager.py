from __future__ import annotations

from pathlib import Path

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches

from thesis_skill.docx_writer.style_manager import caption_style


def add_figure(document: DocxDocument, image_path: str | Path, caption: str, width_inches: float = 5.6) -> bool:
    path = Path(image_path)
    if not path.exists():
        paragraph = document.add_paragraph(f"【图片未找到：{path}】")
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return False
    document.add_picture(str(path), width=Inches(width_inches))
    last = document.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_para = document.add_paragraph(caption, style=caption_style(document))
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return True
