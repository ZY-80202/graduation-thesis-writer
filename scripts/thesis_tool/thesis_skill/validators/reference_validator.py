from __future__ import annotations

from typing import List


def validate_references(references: List[str]) -> List[str]:
    issues: List[str] = []
    if not references:
        issues.append("参考文献为空。")
    for index, reference in enumerate(references, start=1):
        if "【" in reference:
            issues.append(f"第 {index} 条参考文献仍包含待替换标记。")
        if len(reference) < 8:
            issues.append(f"第 {index} 条参考文献信息过短。")
    return issues
