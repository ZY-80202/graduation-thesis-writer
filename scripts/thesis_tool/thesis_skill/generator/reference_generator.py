from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List

DEFAULT_REFERENCE_SOURCES = [
    ("DCloud", "uni-app官方文档", "https://uniapp.dcloud.net.cn/"),
    ("Vue.js团队", "Vue.js官方文档", "https://cn.vuejs.org/"),
    ("Spring", "Spring Boot Reference Documentation", "https://docs.spring.io/spring-boot/reference/"),
]


def generate_references(technology_stack: Iterable[str], access_date: str | None = None) -> List[str]:
    access_date = access_date or date.today().isoformat()
    refs: List[str] = []
    stack = " ".join(technology_stack).lower()
    selected = list(DEFAULT_REFERENCE_SOURCES)
    if "mysql" in stack:
        selected.append(("Oracle", "MySQL Reference Manual", "https://dev.mysql.com/doc/"))
    if "element" in stack:
        selected.append(("Element Plus", "Element Plus官方文档", "https://element-plus.org/zh-CN/"))
    for author, title, url in selected:
        refs.append(format_online_reference(author, title, url, access_date))
    refs.append("张海藩. 软件工程导论[M]. 第6版. 北京: 清华大学出版社, 2013.")
    refs.append("王珊, 萨师煊. 数据库系统概论[M]. 第5版. 北京: 高等教育出版社, 2014.")
    return refs


def format_online_reference(author: str, title: str, url: str, access_date: str) -> str:
    return f"{author}. {title}[EB/OL]. [{access_date}]. {url.rstrip('/')}/."


def normalize_reference(reference: str, access_date: str | None = None) -> str:
    access_date = access_date or date.today().isoformat()
    text = reference.strip()
    if not text:
        return text
    if text.startswith("http://") or text.startswith("https://"):
        return format_online_reference("网络资料", "项目相关在线文档", text, access_date)
    if "[EB/OL]" in text or "[M]" in text or "[J]" in text:
        return text if text.endswith(".") else text + "."
    if "http://" in text or "https://" in text:
        parts = text.split()
        url = next((part for part in parts if part.startswith(("http://", "https://"))), "")
        title = text.replace(url, "").strip(" .")
        return format_online_reference("资料发布机构", title or "在线文档", url, access_date)
    return text if text.endswith(".") else text + "."


def normalize_references(references: Iterable[str], technology_stack: Iterable[str] = (), access_date: str | None = None) -> List[str]:
    refs = [normalize_reference(item, access_date) for item in references if str(item).strip()]
    if not refs:
        refs = generate_references(technology_stack, access_date)
    return refs
