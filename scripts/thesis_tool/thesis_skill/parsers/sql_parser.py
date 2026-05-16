from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from thesis_skill.models import DatabaseColumn, DatabaseTable
from thesis_skill.parsers.project_parser import _extract_table_comment, _iter_create_table_blocks, _parse_table_body
from thesis_skill.utils.file_utils import read_text_file, relative_to

SQL_NAMES = {"database.sql", "init.sql", "schema.sql"}


def find_sql_files(project_path: str | Path) -> List[Path]:
    root = Path(project_path)
    if not root.exists():
        return []
    preferred = [path for path in root.rglob("*.sql") if path.name.lower() in SQL_NAMES]
    others = [path for path in root.rglob("*.sql") if path not in preferred]
    return preferred + others


def parse_sql_file(sql_path: str | Path, root: str | Path | None = None) -> List[DatabaseTable]:
    path = Path(sql_path)
    text = read_text_file(path, max_chars=200000)
    source_root = Path(root) if root else path.parent
    return list(_parse_tables_from_text(text, path, source_root))


def parse_sql_project(project_path: str | Path) -> List[DatabaseTable]:
    root = Path(project_path)
    tables: List[DatabaseTable] = []
    seen: set[str] = set()
    for sql_file in find_sql_files(root):
        for table in parse_sql_file(sql_file, root):
            if table.name in seen:
                continue
            seen.add(table.name)
            tables.append(table)
    return tables


def _parse_tables_from_text(text: str, path: Path, root: Path) -> Iterable[DatabaseTable]:
    for table_name, body, tail in _iter_create_table_blocks(text):
        columns, primary_keys = _parse_table_body(body)
        for column in columns:
            if column.name in primary_keys:
                column.is_primary_key = True
                column.nullable = False
            if not column.comment:
                column.comment = infer_column_comment(column)
        yield DatabaseTable(
            name=table_name,
            columns=[column.name for column in columns],
            field_details=columns,
            comment=_extract_table_comment(tail),
            source=relative_to(path, root),
        )


def infer_column_comment(column: DatabaseColumn) -> str:
    name = column.name.lower()
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
    }
    if name in mapping:
        return mapping[name]
    if name.endswith("_id"):
        return "关联数据编号【请核对】"
    if "time" in name or "date" in name:
        return "时间字段【请核对】"
    return "【请补充字段说明】"
