from __future__ import annotations

import re
from pathlib import Path
from typing import List

from docx import Document

from thesis_skill.models import ValidationIssue, ValidationReport
from thesis_skill.utils.file_utils import ensure_dir, write_json, write_text
from thesis_skill.utils.text_utils import has_placeholder, normalize_whitespace


def validate_docx(
    docx_path: str | Path,
    template_path: str | Path | None = None,
    output_dir: str | Path = "outputs",
) -> ValidationReport:
    path = Path(docx_path)
    if not path.exists():
        raise FileNotFoundError(f"待检查 Word 不存在: {path}")
    document = Document(str(path))
    issues: List[ValidationIssue] = []
    paragraphs = [(index, normalize_whitespace(p.text), p.style.name if p.style else "") for index, p in enumerate(document.paragraphs)]

    _check_headings(paragraphs, issues)
    _check_placeholders(paragraphs, issues)
    _check_captions(paragraphs, issues)
    _check_tables(document, issues)
    _check_images(document, paragraphs, issues)

    summary = "通过基础格式检查。" if not issues else f"发现 {len(issues)} 个需要处理的问题。"
    report = ValidationReport(docx_path=str(path), issues=issues, summary=summary)
    ensure_dir(output_dir)
    write_json(Path(output_dir) / "format_check_report.json", report)
    write_text(Path(output_dir) / "format_check_report.md", _format_markdown(report))
    return report


def _check_headings(paragraphs, issues: List[ValidationIssue]) -> None:
    last_numbers = {}
    for index, text, style in paragraphs:
        if "Heading" not in style and "标题" not in style:
            continue
        if not text:
            issues.append(ValidationIssue(severity="error", message="存在空标题。", location=f"段落 {index}"))
        match = re.match(r"^(\d+)\.(\d+)", text)
        if match:
            chapter = int(match.group(1))
            number = int(match.group(2))
            last = last_numbers.get(chapter, 0)
            if number != last + 1 and number != 1:
                issues.append(ValidationIssue(severity="warning", message=f"章节编号可能跳跃: {text}", location=f"段落 {index}"))
            last_numbers[chapter] = number


def _check_placeholders(paragraphs, issues: List[ValidationIssue]) -> None:
    for index, text, _ in paragraphs:
        if has_placeholder(text):
            issues.append(ValidationIssue(severity="warning", message=f"存在未替换占位符: {text[:60]}", location=f"段落 {index}"))


def _check_captions(paragraphs, issues: List[ValidationIssue]) -> None:
    figure_seen = {}
    table_seen = {}
    for index, text, _ in paragraphs:
        fig = re.match(r"图\s*(\d+)[-.－](\d+)", text)
        tab = re.match(r"表\s*(\d+)[-.－](\d+)", text)
        if fig:
            chapter, number = int(fig.group(1)), int(fig.group(2))
            expected = figure_seen.get(chapter, 0) + 1
            if number != expected:
                issues.append(ValidationIssue(severity="warning", message=f"图题编号不连续: {text}", location=f"段落 {index}"))
            figure_seen[chapter] = max(figure_seen.get(chapter, 0), number)
        if tab:
            chapter, number = int(tab.group(1)), int(tab.group(2))
            expected = table_seen.get(chapter, 0) + 1
            if number != expected:
                issues.append(ValidationIssue(severity="warning", message=f"表题编号不连续: {text}", location=f"段落 {index}"))
            table_seen[chapter] = max(table_seen.get(chapter, 0), number)


def _check_tables(document, issues: List[ValidationIssue]) -> None:
    captions = [p.text for p in document.paragraphs if re.match(r"表\s*\d+[-.－]\d+", normalize_whitespace(p.text))]
    if len(captions) < len(document.tables):
        issues.append(ValidationIssue(severity="warning", message="存在表格标题缺失或表题未按“表 x-y”编号。"))


def _check_images(document, paragraphs, issues: List[ValidationIssue]) -> None:
    rels = document.part.rels
    image_count = sum(1 for rel in rels.values() if "image" in rel.reltype)
    figure_captions = sum(1 for _, text, _ in paragraphs if re.match(r"图\s*\d+[-.－]\d+", text))
    if figure_captions and image_count < figure_captions:
        issues.append(ValidationIssue(severity="warning", message="图题数量多于图片数量，可能存在图片未插入。"))


def _format_markdown(report: ValidationReport) -> str:
    lines = ["# 文档格式检查报告", "", report.summary, ""]
    if not report.issues:
        return "\n".join(lines) + "\n"
    for index, issue in enumerate(report.issues, start=1):
        location = f"（{issue.location}）" if issue.location else ""
        lines.append(f"{index}. [{issue.severity}] {issue.message}{location}")
    return "\n".join(lines) + "\n"
