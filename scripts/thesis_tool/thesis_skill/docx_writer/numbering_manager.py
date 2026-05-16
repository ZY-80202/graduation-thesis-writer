from __future__ import annotations

from typing import Iterable, List

from thesis_skill.models import OutlineSection, SectionDraft

FRONT_MATTER_TITLES = {"毕业设计（论文）", "起讫日期", "摘    要", "摘要", "目    录", "目录"}
BACK_MATTER_TITLES = {"总结", "致谢", "参考文献"}


def normalize_outline_numbering(outline: List[OutlineSection], body_start_title: str = "概述") -> List[OutlineSection]:
    chapter_titles = [body_start_title or "概述", "设计分析", "总体设计", "设计实现", "系统运行与测试", "总结"]
    normalized: List[OutlineSection] = []
    for index, section in enumerate(outline[: len(chapter_titles)], start=1):
        title = chapter_titles[index - 1]
        number = "" if title in BACK_MATTER_TITLES else str(index)
        normalized.append(
            OutlineSection(
                level=1,
                number=number,
                title=title,
                purpose=section.purpose,
                children=_renumber_children(section.children, number),
            )
        )
    return normalized


def heading_text(number: str, title: str) -> str:
    return f"{number} {title}".strip()


def is_front_or_back_matter(title: str) -> bool:
    return title.strip() in FRONT_MATTER_TITLES or title.strip() in BACK_MATTER_TITLES


def iter_numbered_sections(sections: Iterable[SectionDraft]):
    for section in sections:
        if section.number:
            yield section
        yield from iter_numbered_sections(section.children)


def _renumber_children(children: List[OutlineSection], chapter_number: str) -> List[OutlineSection]:
    if not chapter_number:
        return [OutlineSection(level=child.level, number="", title=child.title, purpose=child.purpose, children=child.children) for child in children]
    result: List[OutlineSection] = []
    for index, child in enumerate(children, start=1):
        number = f"{chapter_number}.{index}"
        result.append(
            OutlineSection(
                level=child.level,
                number=number,
                title=_normalize_child_title(child.title, chapter_number, index),
                purpose=child.purpose,
                children=_renumber_grandchildren(child.children, number),
            )
        )
    return result


def _renumber_grandchildren(children: List[OutlineSection], parent_number: str) -> List[OutlineSection]:
    return [
        OutlineSection(level=child.level, number=f"{parent_number}.{index}", title=child.title, purpose=child.purpose, children=child.children)
        for index, child in enumerate(children, start=1)
    ]


def _normalize_child_title(title: str, chapter_number: str, index: int) -> str:
    defaults = {
        "1": ["项目背景", "项目意义", "相关开发技术", "研究内容", "论文组织结构"],
        "2": ["可行性分析", "需求分析", "业务流程分析", "非功能需求分析"],
        "3": ["系统架构设计", "功能结构设计", "数据库设计", "接口设计"],
        "4": ["登录注册模块", "核心功能模块", "后台管理模块", "关键代码实现"],
        "5": ["测试环境", "测试方法", "功能测试", "测试结果分析"],
    }
    choices = defaults.get(chapter_number, [])
    if index <= len(choices):
        return choices[index - 1]
    return title.replace("研究", "项目")
