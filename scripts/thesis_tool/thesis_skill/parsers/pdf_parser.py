from __future__ import annotations

from pathlib import Path
from typing import List

from thesis_skill.utils.file_utils import require_file
from thesis_skill.utils.text_utils import split_paragraphs


def read_pdf_text(path: str | Path) -> str:
    file_path = require_file(path, "PDF 文档")
    try:
        import fitz  # type: ignore

        text_parts: List[str] = []
        with fitz.open(str(file_path)) as document:
            for page in document:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts)
    except Exception:
        try:
            import pdfplumber  # type: ignore

            text_parts = []
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except Exception as exc:
            raise RuntimeError(f"无法读取 PDF: {file_path}. 请安装 PyMuPDF 或 pdfplumber。") from exc


def read_pdf_lines(path: str | Path) -> List[str]:
    return split_paragraphs(read_pdf_text(path))
