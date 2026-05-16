from __future__ import annotations

from pathlib import Path
from typing import List

from thesis_skill.models import ProjectProfile
from thesis_skill.utils.file_utils import ensure_dir, write_text


def find_content_gaps(project: ProjectProfile) -> List[str]:
    gaps: List[str] = []
    if not project.project_name:
        gaps.append("缺少项目名称，请在 config.yaml 或项目说明中补充。")
    if not project.technology_stack:
        gaps.append("缺少技术栈信息，请补充前端、后端、数据库和部署环境。")
    if not project.function_modules:
        gaps.append("缺少功能模块说明，请补充主要模块、用户角色和业务流程。")
    if not project.database_tables:
        gaps.append("缺少数据库表结构，请补充 database.sql、Excel 表结构或数据库设计说明。")
    if project.database_tables:
        for table in project.database_tables:
            if not table.field_details:
                gaps.append(f"{table.name} 表缺少字段明细，建议检查 CREATE TABLE 语句是否完整。")
                continue
            missing_comments = [column.name for column in table.field_details if not column.comment]
            if missing_comments:
                gaps.append(f"{table.name} 表以下字段缺少 COMMENT 说明，需要人工核对：{', '.join(missing_comments[:12])}")
    if not project.backend_endpoints:
        gaps.append("缺少后端接口信息，请检查 source_code/backend/ 下是否存在路由、Controller 或接口文件。")
    if not project.frontend_page_details:
        gaps.append("缺少前端页面信息，请检查 source_code/frontend/ 下是否存在 pages、views 或页面组件。")
    if not project.screenshot_assets:
        gaps.append("缺少系统截图，生成正文会保留截图插入占位符。")
    else:
        unmatched = [asset.file_name for asset in project.screenshot_assets if not asset.matched_module and asset.inferred_section == "系统详细设计与实现"]
        if unmatched:
            gaps.append(f"以下截图未能明确匹配到功能模块，需要人工确认插入位置：{', '.join(unmatched[:20])}")
    if not project.test_points:
        gaps.append("缺少测试内容，请补充测试用例、测试结果或功能验收记录。")
    return gaps


def write_content_gap_report(project: ProjectProfile, output_dir: str | Path = "outputs") -> Path:
    return _write_gap_report(project, output_dir, "content_gap_report.md", "# 内容缺失项提醒报告")


def write_missing_items_report(project: ProjectProfile, output_dir: str | Path = "outputs") -> Path:
    return _write_gap_report(project, output_dir, "missing_items.md", "# 需要人工补充的内容")


def _write_gap_report(project: ProjectProfile, output_dir: str | Path, filename: str, title: str) -> Path:
    gaps = find_content_gaps(project)
    lines = [title, ""]
    if not gaps:
        lines.append("未发现明显缺失项。仍建议人工核对项目名称、截图、表结构、接口说明和参考文献。")
    else:
        for index, gap in enumerate(gaps, start=1):
            lines.append(f"{index}. {gap}")
    lines.extend(["", "## 自动识别摘要", ""])
    lines.append(f"- 数据表数量：{len(project.database_tables)}")
    lines.append(f"- 后端接口数量：{len(project.backend_endpoints)}")
    lines.append(f"- 前端页面数量：{len(project.frontend_page_details)}")
    lines.append(f"- 截图数量：{len(project.screenshot_assets)}")
    ensure_dir(output_dir)
    return write_text(Path(output_dir) / filename, "\n".join(lines) + "\n")
