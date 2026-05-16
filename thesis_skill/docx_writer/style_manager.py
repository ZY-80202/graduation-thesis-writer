from __future__ import annotations

from typing import Any, Dict

from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt


def apply_document_styles(document: DocxDocument, config: Dict[str, Any] | None = None) -> None:
    config = config or {}
    fmt = config.get("format", {})
    chinese_font = fmt.get("chinese_font", "宋体")
    english_font = fmt.get("english_font", "Times New Roman")
    body_size = float(fmt.get("body_font_size_pt", 12))
    heading1_size = float(fmt.get("heading1_font_size_pt", 16))
    heading2_size = float(fmt.get("heading2_font_size_pt", 14))
    line_spacing = float(fmt.get("line_spacing", 1.5))

    _set_style_font(document, "Normal", chinese_font, english_font, body_size)
    for name in ["正文", "Body Text"]:
        if _has_style(document, name):
            _set_style_font(document, name, chinese_font, english_font, body_size)
    for name in ["Heading 1", "标题 1"]:
        if _has_style(document, name):
            _set_style_font(document, name, chinese_font, english_font, heading1_size, bold=True)
            document.styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for name in ["Heading 2", "标题 2"]:
        if _has_style(document, name):
            _set_style_font(document, name, chinese_font, english_font, heading2_size, bold=True)
    for name in ["Heading 3", "标题 3"]:
        if _has_style(document, name):
            _set_style_font(document, name, chinese_font, english_font, body_size, bold=True)

    normal = document.styles["Normal"]
    normal.paragraph_format.line_spacing = line_spacing
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)


def body_style(document: DocxDocument) -> str:
    return "正文" if _has_style(document, "正文") else "Normal"


def heading_style(document: DocxDocument, level: int) -> str:
    chinese = f"标题 {level}"
    english = f"Heading {level}"
    if _has_style(document, chinese):
        return chinese
    if _has_style(document, english):
        return english
    return "Normal"


def caption_style(document: DocxDocument) -> str:
    for name in ["图题", "表题", "Caption"]:
        if _has_style(document, name):
            return name
    return body_style(document)


def _set_style_font(
    document: DocxDocument,
    style_name: str,
    chinese_font: str,
    english_font: str,
    size_pt: float,
    bold: bool | None = None,
) -> None:
    if not _has_style(document, style_name):
        return
    style = document.styles[style_name]
    style.font.name = english_font
    style.font.size = Pt(size_pt)
    if bold is not None:
        style.font.bold = bold
    rpr = style._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), chinese_font)
    rfonts.set(qn("w:ascii"), english_font)
    rfonts.set(qn("w:hAnsi"), english_font)


def _has_style(document: DocxDocument, style_name: str) -> bool:
    try:
        document.styles[style_name]
        return True
    except Exception:
        return False
