from __future__ import annotations

from pathlib import Path
from typing import List

from .file_utils import list_files

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tif", ".tiff"}


def scan_images(root: str | Path) -> List[Path]:
    return list_files(root, IMAGE_SUFFIXES)


def copy_image_for_docx(src: str | Path, dst_dir: str | Path) -> Path:
    from shutil import copy2

    source = Path(src)
    target_dir = Path(dst_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    copy2(source, target)
    return target
