from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from thesis_skill.analyzer.content_gap_checker import write_content_gap_report, write_missing_items_report
from thesis_skill.generator.length_controller import enforce_page_budget, generate_length_report
from thesis_skill.generator.reference_generator import normalize_references
from thesis_skill.generator.section_generator import collect_placeholders, generate_sections
from thesis_skill.models import OutlineSection, ProjectProfile, ThesisDocument
from thesis_skill.utils.file_utils import ensure_dir, read_json, write_json


def build_thesis_draft(
    project_profile: ProjectProfile | Dict[str, Any] | str | Path,
    outline: List[OutlineSection],
    config: Dict[str, Any] | None = None,
    output_dir: str | Path = "outputs",
) -> ThesisDocument:
    project = _as_project_profile(project_profile)
    config = config or {}
    thesis_config = config.get("thesis", {})
    title = thesis_config.get("title") or f"{project.project_name or '项目'}的设计与实现"
    project_name = thesis_config.get("project_name") or project.project_name or "本系统"
    keywords = thesis_config.get("keywords") or _default_keywords(project)
    sections = generate_sections(outline, project)
    document = ThesisDocument(
        title=title,
        author=thesis_config.get("author", ""),
        student_id=thesis_config.get("student_id", ""),
        college=thesis_config.get("college", ""),
        major=thesis_config.get("major", ""),
        supervisor=thesis_config.get("supervisor", ""),
        abstract_cn=_abstract_cn(project_name, project),
        abstract_en=_abstract_en(project_name, project),
        keywords=keywords,
        sections=sections,
        references=normalize_references(_references(config), project.technology_stack),
        acknowledgements=_acknowledgements(),
        appendices=["主要代码片段、配置文件或补充截图可放入附录。【请按学校要求补充】"],
        placeholders=collect_placeholders(sections),
    )
    max_pages = int(config.get("format", {}).get("max_pages", config.get("max_pages", 35)))
    document = enforce_page_budget(document, max_pages=max_pages)
    document.placeholders = collect_placeholders(document.sections)
    ensure_dir(output_dir)
    write_json(Path(output_dir) / "thesis_draft.json", document)
    generate_length_report(document, output_dir, max_pages=max_pages)
    write_content_gap_report(project, output_dir)
    write_missing_items_report(project, output_dir)
    return document


def _abstract_cn(project_name: str, project: ProjectProfile) -> str:
    stack = "、".join(project.technology_stack) or "相关开发技术"
    modules = "、".join(project.function_modules[:6]) or "核心业务功能"
    return (
        f"本文围绕{project_name}的设计与实现展开研究。针对项目业务处理中信息维护、流程管理和数据查询等需求，"
        f"系统采用{stack}完成开发，主要实现{modules}等功能。论文首先分析系统的研究背景和实际需求，"
        f"随后给出总体架构、功能模块、数据库和接口设计，并对核心功能的实现过程进行说明。最后通过功能测试验证系统主要流程的可用性。"
        f"研究结果表明，该系统能够满足项目资料中提出的基本业务需求，并为后续功能扩展和部署优化提供基础。"
    )


def _abstract_en(project_name: str, project: ProjectProfile) -> str:
    stack = ", ".join(project.technology_stack) or "related development technologies"
    return (
        f"This thesis presents the design and implementation of {project_name}. "
        f"Based on the collected project materials, the system is developed with {stack} and focuses on user operations, "
        f"business data management, database design and functional testing. The thesis analyzes requirements, designs the architecture, "
        f"implements core modules, and verifies the main workflows through functional tests. The result provides a practical basis for further improvement."
    )


def _default_keywords(project: ProjectProfile) -> List[str]:
    result = ["毕业设计", "系统设计", "软件开发"]
    result.extend(project.technology_stack[:3])
    return result[:6]


def _references(config: Dict[str, Any]) -> List[str]:
    if not config.get("project", {}).get("generate_references", True):
        return []
    return [
        "软件工程导论相关教材或课程资料【请替换为学校要求格式】",
        "数据库系统概论相关教材或课程资料【请替换为学校要求格式】",
        "所用框架官方文档【请补充访问日期和版本】",
    ]


def _acknowledgements() -> str:
    return "在本课题完成过程中，指导教师在选题、需求分析、系统设计和论文写作方面给予了帮助和指导，在此表示感谢。同时感谢同学和家人在资料整理、系统测试和论文修改过程中提供的支持。"


def _as_project_profile(value: ProjectProfile | Dict[str, Any] | str | Path) -> ProjectProfile:
    if isinstance(value, ProjectProfile):
        return value
    if isinstance(value, (str, Path)):
        value = read_json(value)
    return ProjectProfile(**value)
