from __future__ import annotations

import re
from statistics import mean
from typing import Any, Dict, List

from thesis_skill.parsers.pdf_layout_parser import detect_reference_regions, extract_caption_items, extract_toc_items


def build_reference_layout_profile(layout: Dict[str, Any]) -> Dict[str, Any]:
    captions = extract_caption_items(layout)
    toc_items = extract_toc_items(layout)
    regions = detect_reference_regions(layout)
    image_widths = [
        image.get("width_pt", 0)
        for page in layout.get("pages", [])
        for image in page.get("images", [])
        if image.get("width_pt", 0) > 0
    ]
    full_text = layout.get("full_text", "")
    level1 = re.findall(r"^[一二三四五六七八九十]+、[^\n]+", full_text, flags=re.M)
    level2 = re.findall(r"^（[一二三四五六七八九十]+）[^\n]+", full_text, flags=re.M)
    figure_pages = _count_by_chapter(captions["figures"])
    table_pages = _count_by_chapter(captions["tables"])

    return {
        "source_pdf": layout.get("pdf_path", ""),
        "page_count": layout.get("page_count", 0),
        "cover": {
            "title_prefix": "毕业设计说明书",
            "title_label": "题目：",
            "project_title_format": "“{project_name}”设计与实现",
            "fields": ["提交时间", "姓 名", "班 级", "系 部", "专 业", "指导教师"],
            "detected_text": regions.get("cover_text", "")[:800],
        },
        "front_matter": ["封面", "诚信声明", "目录"],
        "detected_regions": regions,
        "heading_numbering": "chinese" if level1 or "一、" in full_text else "unknown",
        "level1_pattern": "一、{title}",
        "level2_pattern": "（一）{title}",
        "detected_level1_headings": level1[:20],
        "detected_level2_headings": level2[:40],
        "toc": {
            "has_dot_leaders": any("..." in item.get("title", "") or "…" in item.get("title", "") for item in toc_items)
            or bool(toc_items),
            "has_page_numbers": bool(toc_items),
            "max_level": max([item["level"] for item in toc_items], default=2),
            "items": toc_items[:80],
        },
        "figures": {
            "caption_position": "below",
            "caption_pattern": "图 {chapter}-{index} {caption}",
            "count": len(captions["figures"]),
            "by_chapter": figure_pages,
            "average_width_pt": round(mean(image_widths), 2) if image_widths else 0,
            "implementation_chapter_figure_count_target": max(20, figure_pages.get("4", 0)),
            "items": captions["figures"][:80],
        },
        "tables": {
            "caption_position": "above",
            "caption_pattern": "表 {chapter}-{index} {caption}",
            "count": len(captions["tables"]),
            "by_chapter": table_pages,
            "items": captions["tables"][:80],
        },
        "target_page_range": [26, 30],
    }


def _count_by_chapter(items: List[Dict[str, Any]]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for item in items:
        chapter = str(item.get("chapter", ""))
        if not chapter:
            continue
        result[chapter] = result.get(chapter, 0) + 1
    return result
