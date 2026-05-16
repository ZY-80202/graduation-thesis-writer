from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List

from thesis_skill.utils.file_utils import ensure_dir, write_text


def validate_references(references: Iterable[str], output_dir: str | Path | None = None) -> List[str]:
    issues: List[str] = []
    refs = [str(item).strip() for item in references if str(item).strip()]
    if not refs:
        issues.append("参考文献为空。")
    for index, reference in enumerate(refs, start=1):
        issues.extend(_validate_one(index, reference))
    if output_dir is not None:
        write_reference_report(refs, issues, output_dir)
    return issues


def extract_references_from_docx(docx_path: str | Path) -> List[str]:
    from docx import Document

    document = Document(str(docx_path))
    refs: List[str] = []
    in_refs = False
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text in {"参考文献", "参考文献："}:
            in_refs = True
            continue
        if in_refs and text.startswith("["):
            refs.append(re.sub(r"^\[\d+\]\s*", "", text))
        elif in_refs and text in {"致谢", "附录", "附    录"}:
            break
    return refs


def write_reference_report(references: Iterable[str], issues: List[str], output_dir: str | Path) -> Path:
    ensure_dir(output_dir)
    lines = ["# 参考文献检查报告", ""]
    if issues:
        lines.append(f"发现 {len(issues)} 项需要处理的问题。")
        lines.append("")
        lines.extend(f"{idx}. {issue}" for idx, issue in enumerate(issues, start=1))
    else:
        lines.append("参考文献基础格式检查通过。")
    lines.append("")
    lines.append("## 已检查条目")
    for index, reference in enumerate(references, start=1):
        lines.append(f"- [{index}] {reference}")
    path = Path(output_dir) / "reference_check_report.md"
    write_text(path, "\n".join(lines) + "\n")
    return path


def _validate_one(index: int, reference: str) -> List[str]:
    issues: List[str] = []
    if reference.startswith("http://") or reference.startswith("https://"):
        issues.append(f"第 {index} 条参考文献不能只是原始 URL。")
    if "【" in reference or "】" in reference:
        issues.append(f"第 {index} 条参考文献仍包含待替换标记。")
    if not re.search(r"\[(EB/OL|M|J|D|C|R)\]", reference):
        issues.append(f"第 {index} 条参考文献缺少文献类型标识，如 [EB/OL]、[M] 或 [J]。")
    if "[EB/OL]" in reference:
        if not re.search(r"\[\d{4}-\d{2}-\d{2}\]", reference):
            issues.append(f"第 {index} 条在线文献缺少访问日期。")
        if not re.search(r"https?://", reference):
            issues.append(f"第 {index} 条在线文献缺少 URL。")
    if "[M]" in reference and not re.search(r",\s*\d{4}\.?", reference):
        issues.append(f"第 {index} 条图书文献缺少年份。")
    if "[J]" in reference and not re.search(r"\d{4}", reference):
        issues.append(f"第 {index} 条期刊文献缺少年份。")
    if len(reference) < 12:
        issues.append(f"第 {index} 条参考文献信息过短。")
    return issues
