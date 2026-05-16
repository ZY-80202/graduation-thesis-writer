from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from thesis_skill.analyzer.layout_profile_builder import build_reference_layout_profile
from thesis_skill.parsers.pdf_layout_parser import parse_pdf_layout
from thesis_skill.utils.file_utils import ensure_dir, write_json


def analyze_pdf_reference(pdf_path: str | Path, output_dir: str | Path = "outputs/profiles") -> Dict[str, Any]:
    layout = parse_pdf_layout(pdf_path)
    profile = build_reference_layout_profile(layout)
    ensure_dir(output_dir)
    write_json(Path(output_dir) / "reference_layout_profile.json", profile)
    return profile
