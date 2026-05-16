from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from thesis_skill.parsers.docx_parser import read_docx_paragraphs
from thesis_skill.parsers.pdf_parser import read_pdf_lines
from thesis_skill.utils.file_utils import ensure_dir, write_text
from thesis_skill.utils.text_utils import normalize_whitespace, paragraph_similarity


def check_plagiarism_risk(
    generated_docx: str | Path,
    previous_docx: str | Path | None = None,
    previous_pdf: str | Path | None = None,
    output_dir: str | Path = "outputs",
    threshold: float = 0.76,
) -> List[Tuple[str, str, float]]:
    generated = _docx_paragraphs(generated_docx, min_len=55)
    previous: List[str] = []
    if previous_docx and Path(previous_docx).exists():
        previous.extend(_docx_paragraphs(previous_docx, min_len=55))
    if previous_pdf and Path(previous_pdf).exists():
        try:
            previous.extend([line for line in read_pdf_lines(previous_pdf) if len(line) >= 55])
        except Exception:
            pass
    risks: List[Tuple[str, str, float]] = []
    for paragraph in generated:
        for prev in previous:
            score = paragraph_similarity(paragraph, prev)
            if score >= threshold:
                risks.append((paragraph[:120], prev[:120], round(score, 3)))
                break
    ensure_dir(output_dir)
    write_text(Path(output_dir) / "plagiarism_risk_report.md", _report(risks))
    return risks


def _docx_paragraphs(path: str | Path, min_len: int) -> List[str]:
    return [
        normalize_whitespace(item["text"])
        for item in read_docx_paragraphs(path)
        if len(normalize_whitespace(item["text"])) >= min_len
    ]


def _report(risks: List[Tuple[str, str, float]]) -> str:
    lines = ["# 查重风险控制报告", ""]
    if not risks:
        lines.append("未发现与上一届论文高度相似的大段文本。仍建议提交前使用学校指定系统进行正式查重。")
        return "\n".join(lines) + "\n"
    lines.append("以下段落与上一届论文存在较高相似度，建议人工改写或补充项目实际细节：")
    lines.append("")
    for index, (current, previous, score) in enumerate(risks, start=1):
        lines.append(f"{index}. 相似度 {score}")
        lines.append(f"   - 生成段落：{current}")
        lines.append(f"   - 参考段落：{previous}")
    return "\n".join(lines) + "\n"
