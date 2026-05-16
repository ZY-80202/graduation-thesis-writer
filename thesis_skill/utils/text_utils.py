from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable, List, Sequence, Tuple


HEADING_PATTERNS = [
    (1, re.compile(r"^\s*(第[一二三四五六七八九十百\d]+章)\s+(.+?)\s*$")),
    (2, re.compile(r"^\s*(\d+\.\d+)\s+(.+?)\s*$")),
    (3, re.compile(r"^\s*(\d+\.\d+\.\d+)\s+(.+?)\s*$")),
    (1, re.compile(r"^\s*(\d+)[、.]\s*(.+?)\s*$")),
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_paragraphs(text: str, min_len: int = 1) -> List[str]:
    paragraphs = [normalize_whitespace(item) for item in re.split(r"[\r\n]+", text or "")]
    return [item for item in paragraphs if len(item) >= min_len]


def detect_heading(text: str) -> Tuple[int, str, str] | None:
    value = normalize_whitespace(text)
    if not value or len(value) > 80:
        return None
    for level, pattern in HEADING_PATTERNS:
        match = pattern.match(value)
        if match:
            return level, match.group(1), match.group(2).strip()
    common = {
        "摘要": (1, "", "摘要"),
        "Abstract": (1, "", "Abstract"),
        "目录": (1, "", "目录"),
        "参考文献": (1, "", "参考文献"),
        "致谢": (1, "", "致谢"),
        "附录": (1, "", "附录"),
    }
    return common.get(value)


def extract_outline_from_lines(lines: Sequence[str], source: str = "") -> List[Tuple[int, str, str, str]]:
    items: List[Tuple[int, str, str, str]] = []
    seen: set[Tuple[int, str, str]] = set()
    for line in lines:
        heading = detect_heading(line)
        if not heading:
            continue
        level, number, title = heading
        key = (level, number, title)
        if key in seen:
            continue
        seen.add(key)
        items.append((level, number, title, source))
    return items


def compact_keywords(items: Iterable[str], limit: int = 12) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = normalize_whitespace(str(item))
        if not value or value.lower() in seen:
            continue
        seen.add(value.lower())
        result.append(value)
        if len(result) >= limit:
            break
    return result


def paragraph_similarity(a: str, b: str) -> float:
    left = normalize_whitespace(a)
    right = normalize_whitespace(b)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def has_placeholder(text: str) -> bool:
    return bool(re.search(r"【[^】]+】|\{\{[^}]+\}\}|TODO|待补充", text or "", re.IGNORECASE))


def strip_page_number_tail(text: str) -> str:
    return re.sub(r"\s+\.{2,}\s*\d+\s*$", "", text or "").strip()
