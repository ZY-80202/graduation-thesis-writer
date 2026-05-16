from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from docx.document import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

from thesis_skill.models import ValidationIssue


@dataclass
class StyleMap:
    body: str = "Normal"
    heading1: str = "Heading 1"
    heading2: str = "Heading 2"
    heading3: str = "Heading 3"
    caption: str = "Caption"
    table_body: str = "Normal"
    reference: str = "Normal"
    cover_field: str = "Normal"


def apply_document_styles(
    document: DocxDocument,
    config: Dict[str, Any] | None = None,
    template_path: str | Path | None = None,
) -> StyleMap:
    style_map = resolve_template_styles(document)
    _ensure_fallback_styles(document, config or {}, style_map)
    return style_map


def resolve_template_styles(document: DocxDocument) -> StyleMap:
    names = {style.name for style in document.styles if style.type == WD_STYLE_TYPE.PARAGRAPH}
    return StyleMap(
        body=_first_existing(names, ["正文", "Body Text", "Normal"]),
        heading1=_first_existing(names, ["标题 1", "Heading 1", "一级标题", "Normal"]),
        heading2=_first_existing(names, ["标题 2", "Heading 2", "二级标题", "Normal"]),
        heading3=_first_existing(names, ["标题 3", "Heading 3", "三级标题", "Normal"]),
        caption=_first_existing(names, ["题注", "Caption", "图题", "表题", "Normal"]),
        table_body=_first_existing(names, ["表格正文", "Table Text", "Normal"]),
        reference=_first_existing(names, ["参考文献", "Bibliography", "Normal"]),
        cover_field=_first_existing(names, ["封面字段", "Cover Field", "Normal"]),
    )


def body_style(document: DocxDocument) -> str:
    return resolve_template_styles(document).body


def heading_style(document: DocxDocument, level: int) -> str:
    style_map = resolve_template_styles(document)
    return {1: style_map.heading1, 2: style_map.heading2, 3: style_map.heading3}.get(level, style_map.body)


def caption_style(document: DocxDocument) -> str:
    return resolve_template_styles(document).caption


def reference_style(document: DocxDocument) -> str:
    return resolve_template_styles(document).reference


def validate_style_usage(docx_path: str) -> List[ValidationIssue]:
    from docx import Document

    document = Document(docx_path)
    issues: List[ValidationIssue] = []
    paragraphs = [p for p in document.paragraphs if p.text.strip()]
    if not paragraphs:
        return [ValidationIssue(severity="error", message="文档没有可检查段落。")]
    none_like = [p for p in paragraphs if not p.style or p.style.name in {"", "Normal"}]
    if len(none_like) / len(paragraphs) > 0.05:
        issues.append(ValidationIssue(severity="warning", message="正文段落使用 Normal/空样式比例超过 5%，建议继续复用模板正文样式。"))
    for p in paragraphs:
        text = p.text.strip()
        style = p.style.name if p.style else ""
        if text.startswith(("图 ", "表 ")) and not any(key in style for key in ["Caption", "题注", "图题", "表题"]):
            issues.append(ValidationIssue(severity="warning", message=f"图表题未使用题注样式: {text[:30]}"))
        if text.startswith(("1 ", "2 ", "3 ", "4 ", "5 ")) and "Heading" not in style and "标题" not in style:
            issues.append(ValidationIssue(severity="warning", message=f"标题未使用 Heading/标题样式: {text[:30]}"))
    return issues


def _ensure_fallback_styles(document: DocxDocument, config: Dict[str, Any], style_map: StyleMap) -> None:
    fmt = config.get("format", {})
    chinese_font = fmt.get("chinese_font", "宋体")
    english_font = fmt.get("english_font", "Times New Roman")
    body_size = float(fmt.get("body_font_size_pt", 12))
    line_spacing = float(fmt.get("line_spacing", 1.5))
    if style_map.body == "Normal":
        style = document.styles["Normal"]
        style.font.name = english_font
        style.font.size = Pt(body_size)
        rpr = style._element.get_or_add_rPr()
        rfonts = rpr.get_or_add_rFonts()
        rfonts.set(qn("w:eastAsia"), chinese_font)
        rfonts.set(qn("w:ascii"), english_font)
        rfonts.set(qn("w:hAnsi"), english_font)
        style.paragraph_format.line_spacing = line_spacing
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)


def _first_existing(names: set[str], choices: List[str]) -> str:
    for choice in choices:
        if choice in names:
            return choice
    return "Normal"
