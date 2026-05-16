from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict


class CaptionGenerator:
    def __init__(self, figure_rule: str = "图 {chapter}-{index} {caption}", table_rule: str = "表 {chapter}-{index} {caption}") -> None:
        self.figure_rule = figure_rule
        self.table_rule = table_rule
        self.figure_counts: DefaultDict[int, int] = defaultdict(int)
        self.table_counts: DefaultDict[int, int] = defaultdict(int)

    def figure(self, chapter: int, caption: str) -> str:
        self.figure_counts[chapter] += 1
        return self.figure_rule.format(chapter=chapter, index=self.figure_counts[chapter], caption=caption)

    def table(self, chapter: int, caption: str) -> str:
        self.table_counts[chapter] += 1
        return self.table_rule.format(chapter=chapter, index=self.table_counts[chapter], caption=caption)
