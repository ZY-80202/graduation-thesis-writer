from __future__ import annotations

from typing import List

from thesis_skill.generator.table_generator import build_database_field_tables, build_database_overview_table
from thesis_skill.models import ProjectProfile


def generate_database_design_section(project: ProjectProfile) -> List[str]:
    if not project.database_tables:
        return [
            "项目资料中暂未识别到完整的 SQL 建表脚本，数据库设计部分需要根据实际 database.sql、init.sql 或 schema.sql 补充。",
            "后续生成文档会保留数据表说明表格占位，并在 missing_items.md 中提示需要人工核对表名、字段类型和字段说明。",
        ]
    table_names = "、".join(table.name for table in project.database_tables[:10])
    return [
        f"本系统数据库表结构根据 SQL 脚本自动解析，主要包含{table_names}等数据表。数据库设计围绕业务实体、用户身份、状态流转和操作记录展开，各表通过主键、外键或编号字段建立关联。",
        "数据表字段说明以 SQL 中的 CREATE TABLE 定义为基础提取，包括字段名、数据类型、长度、主键、可空约束、默认值和注释。对于 SQL 中未提供注释的字段，工具会依据字段命名生成初步说明，最终仍需结合实际业务含义人工核对。",
    ]


def database_overview_rows(project: ProjectProfile) -> List[List[str]]:
    return build_database_overview_table(project)


def database_field_tables(project: ProjectProfile):
    return build_database_field_tables(project)
