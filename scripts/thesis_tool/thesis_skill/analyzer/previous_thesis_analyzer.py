from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from thesis_skill.models import ChapterItem, PreviousThesisProfile
from thesis_skill.parsers.docx_parser import read_docx_paragraphs
from thesis_skill.parsers.pdf_parser import read_pdf_lines
from thesis_skill.utils.file_utils import ensure_dir, write_json
from thesis_skill.utils.text_utils import extract_outline_from_lines, normalize_whitespace, strip_page_number_tail


def analyze_previous(
    docx_path: str | Path | None = None,
    pdf_path: str | Path | None = None,
    output_dir: str | Path = "outputs/profiles",
) -> PreviousThesisProfile:
    if not docx_path and not pdf_path:
        raise ValueError("请至少提供上一届论文的 Word 或 PDF 文件。")

    lines: List[str] = []
    warnings: List[str] = []
    if docx_path:
        docx_file = Path(docx_path)
        if not docx_file.exists():
            raise FileNotFoundError(f"上一届 Word 不存在: {docx_file}")
        lines.extend(item["text"] for item in read_docx_paragraphs(docx_file) if item["text"])
    if pdf_path:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"上一届 PDF 不存在: {pdf_file}")
        try:
            lines.extend(read_pdf_lines(pdf_file))
        except Exception as exc:
            warnings.append(f"PDF 读取失败，已跳过 PDF 分析: {exc}")

    toc_items = _extract_toc_items(lines)
    outline_items = [
        ChapterItem(level=level, number=number, title=title, source=source, purpose=_infer_purpose(title))
        for level, number, title, source in extract_outline_from_lines(lines, "previous")
    ]
    figure_patterns = sorted(set(re.findall(r"图\s*\d+\s*[-.－]\s*\d+", "\n".join(lines))))
    table_patterns = sorted(set(re.findall(r"表\s*\d+\s*[-.－]\s*\d+", "\n".join(lines))))
    profile = PreviousThesisProfile(
        docx_path=str(docx_path) if docx_path else None,
        pdf_path=str(pdf_path) if pdf_path else None,
        toc_items=toc_items,
        chapter_items=outline_items,
        figure_number_patterns=figure_patterns[:50],
        table_number_patterns=table_patterns[:50],
        writing_patterns=_build_writing_patterns(outline_items),
        warnings=warnings,
    )
    ensure_dir(output_dir)
    write_json(Path(output_dir) / "previous_profile.json", profile)
    return profile


def _extract_toc_items(lines: List[str]) -> List[ChapterItem]:
    toc: List[ChapterItem] = []
    in_toc = False
    for line in lines:
        value = normalize_whitespace(line)
        if not value:
            continue
        if value in {"目录", "目 录", "Contents"}:
            in_toc = True
            continue
        if in_toc and re.match(r"^(摘要|Abstract|第[一二三四五六七八九十\d]+章|\d+\.\d+|参考文献|致谢|附录)", value):
            stripped = strip_page_number_tail(value)
            heading = extract_outline_from_lines([stripped], "toc")
            if heading:
                level, number, title, source = heading[0]
                toc.append(ChapterItem(level=level, number=number, title=title, source=source, purpose=_infer_purpose(title)))
            elif stripped in {"参考文献", "致谢", "附录", "摘要"}:
                toc.append(ChapterItem(level=1, number="", title=stripped, source="toc", purpose=_infer_purpose(stripped)))
        if in_toc and len(toc) > 0 and value.startswith(("第1章", "第一章", "1 绪论")):
            break
    return toc


def _infer_purpose(title: str) -> str:
    mapping = {
        "摘要": "概括研究背景、项目目标、实现方法和主要成果。",
        "绪论": "交代课题背景、意义、研究内容和全文结构。",
        "相关技术": "说明系统开发所采用的主要技术、框架和运行环境。",
        "需求": "分析用户角色、功能需求、非功能需求与业务流程。",
        "总体设计": "描述系统架构、模块划分、数据库和接口设计。",
        "详细设计": "围绕核心功能说明实现流程、关键页面和关键代码逻辑。",
        "实现": "围绕核心功能说明实现流程、关键页面和关键代码逻辑。",
        "测试": "说明测试环境、测试方法、测试用例和结果分析。",
        "总结": "总结完成工作，说明不足与后续改进方向。",
        "参考文献": "列出论文写作和系统开发参考资料。",
        "致谢": "表达对指导教师和相关人员的感谢。",
        "附录": "补充代码、配置、截图或其他辅助材料。",
    }
    for key, value in mapping.items():
        if key in title:
            return value
    return "根据章节标题组织相应的说明性内容，强调结构清楚、层次完整。"


def _build_writing_patterns(items: List[ChapterItem]) -> Dict[str, str]:
    patterns: Dict[str, str] = {}
    for item in items:
        if item.level == 1:
            patterns[item.title] = item.purpose
    if not patterns:
        patterns["通用"] = "上一届论文仅用于参考章节层级、标题组织和图表编号方式，不输出正文内容。"
    return patterns
