from __future__ import annotations

from typing import List, Tuple

from thesis_skill.models import DatabaseColumn, DatabaseTable, ProjectProfile


def build_environment_table(project: ProjectProfile) -> List[List[str]]:
    stack = "、".join(project.technology_stack) if project.technology_stack else "【请补充技术栈】"
    return [
        ["项目", "说明"],
        ["开发语言与框架", stack],
        ["数据库", _guess_database(project)],
        ["运行环境", "本地开发环境/服务器环境【请核对实际部署环境】"],
        ["浏览器或客户端", "Chrome、Edge 等主流浏览器【请按实际情况修改】"],
    ]


def build_database_overview_table(project: ProjectProfile) -> List[List[str]]:
    rows = [["表名", "主要字段", "表说明", "来源"]]
    if not project.database_tables:
        rows.append(["【请补充表名】", "【请补充字段】", "【请补充表用途】", "database.sql"])
        return rows
    for table in project.database_tables:
        rows.append(
            [
                table.name,
                "、".join(_column_names(table)[:12]) or "【请补充字段】",
                table.comment or _table_description(table.name),
                table.source,
            ]
        )
    return rows


def build_database_field_tables(project: ProjectProfile) -> List[Tuple[str, List[List[str]]]]:
    tables: List[Tuple[str, List[List[str]]]] = []
    if not project.database_tables:
        return [
            (
                "数据表字段说明",
                [["字段名", "类型", "主键", "可为空", "默认值", "字段说明"], ["【字段名】", "【类型】", "否", "是", "", "【请补充字段说明】"]],
            )
        ]
    for table in project.database_tables:
        rows = [["字段名", "类型", "主键", "可为空", "默认值", "字段说明"]]
        details = table.field_details or [DatabaseColumn(name=name) for name in table.columns]
        for column in details:
            rows.append(
                [
                    column.name,
                    column.data_type or "【请补充类型】",
                    "是" if column.is_primary_key else "否",
                    "是" if column.nullable else "否",
                    column.default,
                    column.comment or _field_description(column.name),
                ]
            )
        tables.append((f"{table.name}表字段说明", rows))
    return tables


def build_endpoint_table(project: ProjectProfile) -> List[List[str]]:
    rows = [["请求方法", "接口路径", "接口说明", "来源"]]
    if not project.backend_endpoints:
        rows.append(["【方法】", "【接口路径】", "【请补充接口说明】", "source_code/backend/"])
        return rows
    for endpoint in project.backend_endpoints[:40]:
        rows.append(
            [
                endpoint.method or "ANY",
                endpoint.path,
                endpoint.description or "用于支撑相关业务功能【请核对说明】",
                endpoint.source,
            ]
        )
    return rows


def build_frontend_page_table(project: ProjectProfile) -> List[List[str]]:
    rows = [["页面名称", "路由路径", "对应模块", "来源文件"]]
    if not project.frontend_page_details:
        rows.append(["【请补充页面】", "【请补充路由】", "【请补充模块】", "source_code/frontend/"])
        return rows
    for page in project.frontend_page_details[:40]:
        rows.append([page.title or page.name, page.route_path or "【请补充路由】", page.matched_module or "【请核对模块】", page.file_path])
    return rows


def build_test_table(project: ProjectProfile) -> List[List[str]]:
    rows = [["测试功能", "测试内容", "预期结果"]]
    points = project.test_points or project.function_modules or ["核心功能"]
    for point in points[:12]:
        rows.append([point, f"验证{point}流程是否符合需求", "功能可正常使用，异常输入能够给出提示"])
    return rows


def _column_names(table: DatabaseTable) -> List[str]:
    if table.field_details:
        return [column.name for column in table.field_details]
    return table.columns


def _table_description(name: str) -> str:
    lower = name.lower()
    if "user" in lower or "member" in lower or "用户" in name:
        return "存储用户账号、身份和基础资料"
    if "order" in lower or "订单" in name:
        return "存储订单主信息和业务状态"
    if "product" in lower or "goods" in lower or "商品" in name:
        return "存储商品或业务对象信息"
    if "cart" in lower or "购物车" in name:
        return "存储用户临时选择的商品信息"
    if "comment" in lower or "message" in lower or "评论" in name or "留言" in name:
        return "存储用户评论、留言或反馈信息"
    if "log" in lower:
        return "存储系统运行或操作日志"
    return "存储系统业务数据【请核对表用途】"


def _field_description(name: str) -> str:
    lower = name.lower()
    mapping = {
        "id": "主键编号",
        "user_id": "用户编号",
        "username": "用户名",
        "password": "密码或密码摘要",
        "phone": "联系电话",
        "email": "电子邮箱",
        "name": "名称",
        "title": "标题",
        "content": "内容",
        "status": "状态",
        "create_time": "创建时间",
        "created_at": "创建时间",
        "update_time": "更新时间",
        "updated_at": "更新时间",
        "price": "价格",
        "total": "合计金额",
    }
    if lower in mapping:
        return mapping[lower]
    if lower.endswith("_id"):
        return "关联数据编号"
    if "time" in lower or "date" in lower:
        return "时间字段"
    return "【请补充字段说明】"


def _guess_database(project: ProjectProfile) -> str:
    stack = "、".join(project.technology_stack)
    for name in ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle", "MongoDB", "Redis"]:
        if name.lower() in stack.lower():
            return name
    return "关系型数据库【请核对实际数据库】" if project.database_tables else "【请补充数据库】"
