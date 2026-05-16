from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from thesis_skill.utils.file_utils import ensure_dir


def prepare_template_docx(template_path: str | Path, work_dir: str | Path = "outputs/profiles") -> Path:
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"模板文件不存在: {template}")
    if template.suffix.lower() == ".docx":
        return template
    if template.suffix.lower() != ".doc":
        raise ValueError(f"仅支持 .doc 或 .docx 模板: {template}")
    return convert_doc_to_docx(template, work_dir)


def convert_doc_to_docx(doc_path: str | Path, output_dir: str | Path = "outputs/profiles") -> Path:
    doc = Path(doc_path)
    out_dir = ensure_dir(output_dir)
    converted = out_dir / f"{doc.stem}.docx"
    if converted.exists() and converted.stat().st_mtime >= doc.stat().st_mtime:
        return converted

    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError("未找到 LibreOffice/soffice，无法将 .doc 模板转换为 .docx。请安装 LibreOffice 或提供 .docx 模板。")
    cmd = [soffice, "--headless", "--convert-to", "docx", "--outdir", str(out_dir), str(doc)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice 转换失败: {result.stderr or result.stdout}")
    if not converted.exists():
        candidates = list(out_dir.glob(f"{doc.stem}*.docx"))
        if not candidates:
            raise RuntimeError(f"LibreOffice 未生成 docx: {doc}")
        shutil.move(str(candidates[0]), converted)
    return converted


def _find_libreoffice() -> str | None:
    for name in ["soffice", "libreoffice"]:
        path = shutil.which(name)
        if path:
            return path
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None
