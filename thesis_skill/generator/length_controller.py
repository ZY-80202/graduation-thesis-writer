from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from thesis_skill.models import SectionDraft, ThesisDocument
from thesis_skill.utils.file_utils import ensure_dir, write_text

SECTION_BUDGETS: Dict[str, Tuple[int, int]] = {
    "摘要": (300, 500),
    "概述": (1200, 1800),
    "设计分析": (1500, 2200),
    "总体设计": (2500, 4000),
    "设计实现": (5000, 8000),
    "系统运行与测试": (1500, 2500),
    "测试": (1500, 2500),
    "总结": (600, 900),
    "致谢": (400, 700),
}


def estimate_section_length(section: SectionDraft) -> int:
    return sum(_chinese_length(paragraph) for paragraph in section.paragraphs) + sum(estimate_section_length(child) for child in section.children)


def compress_overlong_section(section: SectionDraft, max_chars: int | None = None) -> SectionDraft:
    budget = max_chars or _budget_for(section.title)[1]
    if estimate_section_length(section) <= budget:
        return section

    compressed = SectionDraft(number=section.number, title=section.title, level=section.level, paragraphs=[], children=section.children)
    remaining = max(240, budget - sum(estimate_section_length(child) for child in section.children))
    for paragraph in section.paragraphs[:4]:
        if remaining <= 0:
            break
        text = _compress_paragraph(paragraph, min(remaining, 420))
        compressed.paragraphs.append(text)
        remaining -= _chinese_length(text)
    if not compressed.paragraphs and section.paragraphs:
        compressed.paragraphs.append(_compress_paragraph(section.paragraphs[0], 360))
    return compressed


def enforce_page_budget(document: ThesisDocument, max_pages: int = 35) -> ThesisDocument:
    # A Chinese thesis page usually carries roughly 650-800 Chinese chars after
    # headings, figures, and tables. Use a conservative estimate to keep output
    # close to the requested 25-35 page range.
    max_chars = max_pages * 760
    current = _document_length(document)
    if current <= max_chars:
        return document

    ratio = max(0.55, max_chars / max(current, 1))
    sections = [_compress_tree(section, ratio) for section in document.sections]
    document.sections = sections
    document.abstract_cn = _compress_paragraph(document.abstract_cn, SECTION_BUDGETS["摘要"][1])
    document.acknowledgements = _compress_paragraph(document.acknowledgements, SECTION_BUDGETS["致谢"][1])
    return document


def generate_length_report(document: ThesisDocument, output_dir: str | Path = "outputs", max_pages: int = 35) -> Path:
    ensure_dir(output_dir)
    lines = [
        "# 篇幅控制报告",
        "",
        f"- 目标最大页数: {max_pages}",
        f"- 估算总字数: {_document_length(document)}",
        "",
        "| 章节 | 估算字数 | 建议范围 | 状态 |",
        "| --- | ---: | --- | --- |",
    ]
    for section in _iter_sections(document.sections):
        length = estimate_section_length(section)
        low, high = _budget_for(section.title)
        status = "正常" if low <= length <= high or section.level > 1 else ("偏长" if length > high else "偏短")
        lines.append(f"| {section.number} {section.title}".strip() + f" | {length} | {low}-{high} | {status} |")
    path = Path(output_dir) / "length_report.md"
    write_text(path, "\n".join(lines) + "\n")
    return path


def _compress_tree(section: SectionDraft, ratio: float) -> SectionDraft:
    _, high = _budget_for(section.title)
    target = int(high * ratio)
    compressed = compress_overlong_section(section, target)
    compressed.children = [_compress_tree(child, ratio) for child in section.children]
    return compressed


def _document_length(document: ThesisDocument) -> int:
    return (
        _chinese_length(document.abstract_cn)
        + _chinese_length(document.abstract_en)
        + _chinese_length(document.acknowledgements)
        + sum(estimate_section_length(section) for section in document.sections)
    )


def _iter_sections(sections: Iterable[SectionDraft]) -> Iterable[SectionDraft]:
    for section in sections:
        yield section
        yield from _iter_sections(section.children)


def _budget_for(title: str) -> Tuple[int, int]:
    for keyword, budget in SECTION_BUDGETS.items():
        if keyword in title:
            return budget
    return (300, 900)


def _compress_paragraph(text: str, limit: int) -> str:
    clean = str(text).strip()
    if _chinese_length(clean) <= limit:
        return clean
    end = max(80, limit)
    clipped = clean[:end]
    for mark in ["。", "；", ";", "."]:
        pos = clipped.rfind(mark)
        if pos > int(end * 0.55):
            return clipped[: pos + 1]
    return clipped.rstrip("，,；;") + "。"


def _chinese_length(text: str) -> int:
    return len(str(text).replace(" ", "").replace("\n", ""))
