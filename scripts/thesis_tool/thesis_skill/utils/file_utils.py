from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, List, Optional


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def require_file(path: str | Path, label: str = "文件") -> Path:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"{label}不存在: {file_path}")
    return file_path


def require_dir(path: str | Path, label: str = "目录") -> Path:
    dir_path = Path(path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"{label}不存在: {dir_path}")
    return dir_path


def read_text_file(path: str | Path, max_chars: Optional[int] = None) -> str:
    file_path = require_file(path)
    encodings = ("utf-8", "utf-8-sig", "gb18030", "gbk", "latin-1")
    last_error: Optional[Exception] = None
    for encoding in encodings:
        try:
            text = file_path.read_text(encoding=encoding, errors="strict")
            return text[:max_chars] if max_chars else text
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return text[:max_chars] if max_chars else text
    return ""


def write_text(path: str | Path, content: str) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def model_to_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [model_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: model_to_dict(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def write_json(path: str | Path, data: Any) -> Path:
    file_path = Path(path)
    ensure_dir(file_path.parent)
    file_path.write_text(json.dumps(model_to_dict(data), ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def read_json(path: str | Path) -> Any:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def list_files(root: str | Path, suffixes: Iterable[str] | None = None) -> List[Path]:
    root_path = require_dir(root)
    suffix_set = {suffix.lower() for suffix in suffixes} if suffixes else None
    files: List[Path] = []
    for item in root_path.rglob("*"):
        if not item.is_file():
            continue
        if suffix_set and item.suffix.lower() not in suffix_set:
            continue
        files.append(item)
    return sorted(files)


def safe_slug(text: str, default: str = "item") -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text.strip(), flags=re.UNICODE)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or default


def relative_to(path: str | Path, root: str | Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except Exception:
        return str(path)
