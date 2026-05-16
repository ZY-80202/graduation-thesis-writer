from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence

from thesis_skill.models import OutlineSection, PreviousThesisProfile, ProjectProfile, TemplateProfile
from thesis_skill.utils.file_utils import ensure_dir, read_json, write_json


def build_outline(
    template_profile: TemplateProfile | Dict[str, Any] | str | Path | None,
    previous_profile: PreviousThesisProfile | Dict[str, Any] | str | Path | None,
    project_profile: ProjectProfile | Dict[str, Any] | str | Path,
    output_dir: str | Path = "outputs/profiles",
) -> List[OutlineSection]:
    project = _as_project_profile(project_profile)
    modules = _select_modules(project)
    outline = _default_outline(modules)
    ensure_dir(output_dir)
    write_json(Path(output_dir) / "outline.json", outline)
    return outline


def _default_outline(modules: Sequence[str]) -> List[OutlineSection]:
    chapter5_children = [
        OutlineSection(level=2, number=f"5.{index}", title=f"{module}模块", purpose="说明该功能模块的页面交互、业务逻辑、数据处理和实现结果。")
        for index, module in enumerate(modules[:7], start=1)
    ]
    if not chapter5_children:
        chapter5_children = [
            OutlineSection(level=2, number="5.1", title="核心功能模块", purpose="说明系统核心功能的实现流程和关键页面。"),
            OutlineSection(level=2, number="5.2", title="后台管理模块", purpose="说明后台管理功能的实现方式。"),
        ]
    return [
        OutlineSection(
            level=1,
            number="第1章",
            title="绪论",
            purpose="介绍课题背景、研究意义、研究内容和论文结构。",
            children=[
                OutlineSection(level=2, number="1.1", title="研究背景"),
                OutlineSection(level=2, number="1.2", title="研究意义"),
                OutlineSection(level=2, number="1.3", title="国内外研究现状"),
                OutlineSection(level=2, number="1.4", title="研究内容"),
                OutlineSection(level=2, number="1.5", title="论文组织结构"),
            ],
        ),
        OutlineSection(
            level=1,
            number="第2章",
            title="相关技术介绍",
            children=[
                OutlineSection(level=2, number="2.1", title="前端开发技术"),
                OutlineSection(level=2, number="2.2", title="后端开发技术"),
                OutlineSection(level=2, number="2.3", title="数据库技术"),
                OutlineSection(level=2, number="2.4", title="系统开发环境"),
            ],
        ),
        OutlineSection(
            level=1,
            number="第3章",
            title="系统需求分析",
            children=[
                OutlineSection(level=2, number="3.1", title="可行性分析"),
                OutlineSection(level=2, number="3.2", title="功能需求分析"),
                OutlineSection(level=2, number="3.3", title="非功能需求分析"),
                OutlineSection(level=2, number="3.4", title="系统业务流程分析"),
            ],
        ),
        OutlineSection(
            level=1,
            number="第4章",
            title="系统总体设计",
            children=[
                OutlineSection(level=2, number="4.1", title="系统架构设计"),
                OutlineSection(level=2, number="4.2", title="功能模块设计"),
                OutlineSection(level=2, number="4.3", title="数据库设计"),
                OutlineSection(level=2, number="4.4", title="接口设计"),
            ],
        ),
        OutlineSection(level=1, number="第5章", title="系统详细设计与实现", children=chapter5_children),
        OutlineSection(
            level=1,
            number="第6章",
            title="系统测试",
            children=[
                OutlineSection(level=2, number="6.1", title="测试环境"),
                OutlineSection(level=2, number="6.2", title="测试方法"),
                OutlineSection(level=2, number="6.3", title="功能测试"),
                OutlineSection(level=2, number="6.4", title="测试结果分析"),
            ],
        ),
        OutlineSection(
            level=1,
            number="第7章",
            title="总结与展望",
            children=[
                OutlineSection(level=2, number="7.1", title="工作总结"),
                OutlineSection(level=2, number="7.2", title="不足与展望"),
            ],
        ),
    ]


def _select_modules(project: ProjectProfile) -> List[str]:
    forbidden = {"Index", "Home", "Main", "App", "Layout", "页面"}
    result: List[str] = []
    for module in project.function_modules:
        clean = module.replace("模块", "").strip()
        if clean and clean not in forbidden and clean not in result:
            result.append(clean)
    return result


def _as_project_profile(value: ProjectProfile | Dict[str, Any] | str | Path) -> ProjectProfile:
    if isinstance(value, ProjectProfile):
        return value
    if isinstance(value, (str, Path)):
        value = read_json(value)
    return ProjectProfile(**value)
