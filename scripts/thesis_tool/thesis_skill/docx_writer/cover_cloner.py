from __future__ import annotations

import copy
import shutil
from pathlib import Path
from typing import Dict

from docx import Document

from thesis_skill.docx_writer.ooxml_replace import replace_text_in_ooxml
from thesis_skill.utils.file_utils import ensure_dir


def clone_template_cover(
    template_docx: str | Path,
    output_docx: str | Path,
    replacements: Dict[str, str] | None = None,
    cover_pages: int = 2,
) -> Path:
    """Copy the template and keep only its front matter/cover pages.

    The function starts from the actual template package, so drawings, tables,
    text boxes, headers, footers, margins, and relationships remain intact.
    It trims body XML after the requested cover page breaks when possible.
    """

    source = Path(template_docx)
    target = Path(output_docx)
    ensure_dir(target.parent)
    shutil.copy2(source, target)
    if replacements:
        replace_text_in_ooxml(target, replacements)
    trim_document_after_cover_pages(target, cover_pages)
    return target


def trim_document_after_cover_pages(docx_path: str | Path, cover_pages: int = 2) -> None:
    document = Document(str(docx_path))
    body = document._element.body
    children = list(body)
    keep_until = _find_cover_boundary(children, cover_pages)
    if keep_until is None:
        document.save(str(docx_path))
        return
    sect_pr = None
    for child in children:
        if child.tag.endswith("sectPr"):
            sect_pr = copy.deepcopy(child)
    for child in children[keep_until + 1 :]:
        if child.tag.endswith("sectPr"):
            continue
        body.remove(child)
    if sect_pr is not None and not list(body)[-1].tag.endswith("sectPr"):
        body.append(sect_pr)
    document.save(str(docx_path))


def _find_cover_boundary(children, cover_pages: int) -> int | None:
    if cover_pages <= 0:
        return None
    page_breaks = 0
    last_candidate = None
    for index, child in enumerate(children):
        xml = child.xml
        if 'w:type="page"' in xml or "lastRenderedPageBreak" in xml:
            page_breaks += 1
            last_candidate = index
            if page_breaks >= cover_pages:
                return index
        if "w:sectPr" in xml:
            last_candidate = index
            if page_breaks + 1 >= cover_pages:
                return index
    return last_candidate


def build_cover_replacements(config: Dict) -> Dict[str, str]:
    thesis = config.get("thesis", {}) if config else {}
    cover = config.get("cover_replacements", {}) if config else {}
    replacements = {str(k): str(v) for k, v in cover.items()}

    aliases = {
        "请填写设计题目": thesis.get("title", ""),
        "请填写论文题目": thesis.get("title", ""),
        "{设计题目}": thesis.get("title", ""),
        "{论文题目}": thesis.get("title", ""),
        "请填写项目名称": thesis.get("project_name", thesis.get("title", "")),
        "请填写专业": thesis.get("major", ""),
        "请填写班级": thesis.get("class_name", thesis.get("class", "")),
        "请填写学号": thesis.get("student_id", ""),
        "请填写姓名": thesis.get("author", ""),
        "请填写作者姓名": thesis.get("author", ""),
        "请填写指导老师": thesis.get("supervisor", ""),
        "请填写指导教师": thesis.get("supervisor", ""),
        "请填写起讫日期": thesis.get("date_range", ""),
    }
    for old, new in aliases.items():
        if new:
            replacements.setdefault(old, str(new))
    return replacements
