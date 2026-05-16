from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from thesis_skill.docx_writer.figure_manager import add_figure
from thesis_skill.docx_writer.style_manager import apply_document_styles, body_style, heading_style
from thesis_skill.docx_writer.table_manager import add_data_table
from thesis_skill.docx_writer.toc_manager import add_toc
from thesis_skill.generator.caption_generator import CaptionGenerator
from thesis_skill.generator.table_generator import (
    build_database_field_tables,
    build_database_overview_table,
    build_endpoint_table,
    build_environment_table,
    build_frontend_page_table,
    build_test_table,
)
from thesis_skill.models import DiagramArtifact, ProjectProfile, ScreenshotAsset, SectionDraft, ThesisDocument
from thesis_skill.utils.file_utils import ensure_dir


def build_docx(
    template_path: str | Path,
    thesis: ThesisDocument,
    project: ProjectProfile,
    diagrams: List[DiagramArtifact] | None,
    out_path: str | Path = "outputs/final_thesis.docx",
    config: Dict[str, Any] | None = None,
) -> Path:
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"学校模板不存在: {template}")
    document = Document(str(template))
    _clear_body(document)
    apply_document_styles(document, config)
    _set_default_section(document, config)
    _add_cover(document, thesis)
    _add_abstract(document, thesis)
    _add_toc(document)
    diagram_map = {diagram.key: diagram for diagram in diagrams or []}
    inserted_diagrams: Set[str] = set()
    inserted_screenshots: Set[str] = set()
    captions = CaptionGenerator()
    for section in thesis.sections:
        _add_section(document, section, project, diagram_map, inserted_diagrams, inserted_screenshots, captions)
    _add_references(document, thesis)
    _add_acknowledgements(document, thesis)
    _add_appendices(document, thesis)
    output = Path(out_path)
    ensure_dir(output.parent)
    document.save(str(output))
    return output


def _clear_body(document) -> None:
    body = document._element.body
    for child in list(body):
        if child.tag.endswith("sectPr"):
            continue
        body.remove(child)


def _set_default_section(document, config: Dict[str, Any] | None) -> None:
    fmt = (config or {}).get("format", {})
    for section in document.sections:
        section.top_margin = Cm(float(fmt.get("top_margin_cm", 2.54)))
        section.bottom_margin = Cm(float(fmt.get("bottom_margin_cm", 2.54)))
        section.left_margin = Cm(float(fmt.get("left_margin_cm", 3.0)))
        section.right_margin = Cm(float(fmt.get("right_margin_cm", 2.6)))


def _add_cover(document, thesis: ThesisDocument) -> None:
    for _ in range(3):
        document.add_paragraph("")
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(thesis.title)
    run.bold = True
    run.font.size = Pt(22)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), "黑体")
    for _ in range(4):
        document.add_paragraph("")
    rows = [
        ("学生姓名", thesis.author or "【请填写作者姓名】"),
        ("学号", thesis.student_id or "【请填写学号】"),
        ("学院", thesis.college or "【请填写学院】"),
        ("专业", thesis.major or "【请填写专业】"),
        ("指导教师", thesis.supervisor or "【请填写指导教师】"),
    ]
    for label, value in rows:
        paragraph = document.add_paragraph(style=body_style(document))
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run(f"{label}：{value}")
    document.add_page_break()


def _add_abstract(document, thesis: ThesisDocument) -> None:
    _heading(document, "摘要", 1)
    _body_paragraph(document, thesis.abstract_cn)
    _body_paragraph(document, "关键词：" + "；".join(thesis.keywords))
    _heading(document, "Abstract", 1)
    _body_paragraph(document, thesis.abstract_en)
    _body_paragraph(document, "Key words: " + "; ".join(thesis.keywords))
    document.add_page_break()


def _add_toc(document) -> None:
    _heading(document, "目录", 1)
    paragraph = document.add_paragraph()
    add_toc(paragraph)
    _body_paragraph(document, "提示：在 Microsoft Word 中右键目录并选择“更新域”，即可刷新页码。")
    document.add_page_break()


def _add_section(
    document,
    section: SectionDraft,
    project: ProjectProfile,
    diagram_map: Dict[str, DiagramArtifact],
    inserted_diagrams: Set[str],
    inserted_screenshots: Set[str],
    captions: CaptionGenerator,
) -> None:
    text = f"{section.number} {section.title}".strip()
    _heading(document, text, min(section.level, 3))
    for paragraph in section.paragraphs:
        _body_paragraph(document, paragraph)
    _insert_section_assets(document, section, project, diagram_map, inserted_diagrams, inserted_screenshots, captions)
    for child in section.children:
        _add_section(document, child, project, diagram_map, inserted_diagrams, inserted_screenshots, captions)


def _insert_section_assets(
    document,
    section: SectionDraft,
    project: ProjectProfile,
    diagram_map: Dict[str, DiagramArtifact],
    inserted_diagrams: Set[str],
    inserted_screenshots: Set[str],
    captions: CaptionGenerator,
) -> None:
    title = section.title
    chapter = _chapter_number(section)
    asset_key = _diagram_key_for_section(title)
    if asset_key and asset_key in diagram_map and asset_key not in inserted_diagrams:
        diagram = diagram_map[asset_key]
        add_figure(document, diagram.png_path, captions.figure(chapter, diagram.title))
        inserted_diagrams.add(asset_key)

    _insert_screenshots_for_section(document, section, project, inserted_screenshots, captions)

    if title == "系统开发环境":
        add_data_table(document, captions.table(chapter, "系统开发环境表"), build_environment_table(project))
    elif title == "功能模块设计":
        add_data_table(document, captions.table(chapter, "系统功能页面说明"), build_frontend_page_table(project))
    elif title == "数据库设计":
        add_data_table(document, captions.table(chapter, "数据库表汇总"), build_database_overview_table(project))
        for caption_text, rows in build_database_field_tables(project):
            add_data_table(document, captions.table(chapter, caption_text), rows)
    elif title == "接口设计":
        add_data_table(document, captions.table(chapter, "核心接口设计"), build_endpoint_table(project))
    elif title == "功能测试":
        add_data_table(document, captions.table(chapter, "功能测试用例表"), build_test_table(project))


def _diagram_key_for_section(title: str) -> str | None:
    if "业务流程" in title:
        return "business_flow"
    if "架构" in title:
        return "architecture"
    if "功能模块" in title:
        return "function_structure"
    if title == "数据库设计":
        return "er"
    if "接口" in title:
        return "frontend_backend"
    if "测试方法" in title:
        return "test_flow"
    if "后台" in title or "管理" in title:
        return "admin_flow"
    if "模块" in title and "用户" in title:
        return "user_flow"
    return None


def _insert_screenshots_for_section(
    document,
    section: SectionDraft,
    project: ProjectProfile,
    inserted: Set[str],
    captions: CaptionGenerator,
) -> None:
    if not project.screenshot_assets:
        return
    chapter = _chapter_number(section)
    section_text = f"{section.title} {section.number}"
    for asset in project.screenshot_assets:
        if asset.path in inserted:
            continue
        if not _screenshot_matches_section(asset, section_text):
            continue
        image_path = Path(project.project_path) / asset.path
        add_figure(document, image_path, captions.figure(chapter, asset.caption or "系统页面运行效果"))
        inserted.add(asset.path)


def _screenshot_matches_section(asset: ScreenshotAsset, section_text: str) -> bool:
    target = f"{asset.inferred_section} {asset.matched_module}".strip()
    if not target:
        return False
    if asset.inferred_section and asset.inferred_section in section_text:
        return True
    if asset.matched_module and asset.matched_module.replace("模块", "") in section_text:
        return True
    if "系统测试" in asset.inferred_section and "测试" in section_text:
        return True
    if "数据库设计" in asset.inferred_section and "数据库" in section_text:
        return True
    if asset.inferred_section == "系统详细设计与实现" and "模块" in section_text:
        return False
    return False


def _chapter_number(section: SectionDraft) -> int:
    if section.number.startswith("第"):
        match = re.search(r"第(\d+)章", section.number)
        if match:
            return int(match.group(1))
        chinese_digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
        for key, value in chinese_digits.items():
            if key in section.number:
                return value
    match = re.match(r"(\d+)", section.number)
    return int(match.group(1)) if match else 1


def _add_references(document, thesis: ThesisDocument) -> None:
    _heading(document, "参考文献", 1)
    if not thesis.references:
        _body_paragraph(document, "【请补充参考文献】")
        return
    for index, reference in enumerate(thesis.references, start=1):
        _body_paragraph(document, f"[{index}] {reference}")


def _add_acknowledgements(document, thesis: ThesisDocument) -> None:
    _heading(document, "致谢", 1)
    _body_paragraph(document, thesis.acknowledgements or "【请补充致谢内容】")


def _add_appendices(document, thesis: ThesisDocument) -> None:
    _heading(document, "附录", 1)
    for appendix in thesis.appendices or ["【请补充附录】"]:
        _body_paragraph(document, appendix)


def _heading(document, text: str, level: int) -> None:
    paragraph = document.add_paragraph(text, style=heading_style(document, level))
    if level == 1:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _body_paragraph(document, text: str) -> None:
    paragraph = document.add_paragraph(text, style=body_style(document))
    paragraph.paragraph_format.first_line_indent = Cm(0.74)
    paragraph.paragraph_format.line_spacing = 1.5
