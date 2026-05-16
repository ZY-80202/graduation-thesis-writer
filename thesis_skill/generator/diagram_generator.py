from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from thesis_skill.generator.caption_generator import CaptionGenerator
from thesis_skill.models import DiagramArtifact, ProjectProfile
from thesis_skill.utils.file_utils import ensure_dir, read_json, safe_slug, write_json, write_text

Box = Tuple[int, int, int, int, str]
Line = Tuple[int, int, int, int]
UseCase = Tuple[int, int, int, int, str]
UseCaseDiagram = Tuple[str, str, List[UseCase], str]


def generate_diagrams(
    project_profile: ProjectProfile | Dict | str | Path,
    output_dir: str | Path = "outputs/diagrams",
) -> List[DiagramArtifact]:
    project = _as_project_profile(project_profile)
    out_dir = ensure_dir(output_dir)
    captions = CaptionGenerator()
    definitions = [
        ("architecture", "系统总体架构图", captions.figure(4, "系统总体架构图"), "box", _architecture(project)),
        ("function_structure", "系统功能结构图", captions.figure(4, "系统功能结构图"), "box", _function_structure(project)),
        ("business_flow", "系统业务流程图", captions.figure(3, "系统业务流程图"), "box", _business_flow(project)),
        ("user_flow", "用户用例图", captions.figure(5, "用户用例图"), "use_case", _user_flow(project)),
        ("admin_flow", "管理员用例图", captions.figure(5, "管理员用例图"), "use_case", _admin_flow(project)),
        ("er", "数据库 ER 图", captions.figure(4, "数据库 ER 图"), "box", _er_diagram(project)),
        ("frontend_backend", "前后端交互流程图", captions.figure(4, "前后端交互流程图"), "box", _frontend_backend(project)),
        ("test_flow", "系统测试流程图", captions.figure(6, "系统测试流程图"), "box", _test_flow(project)),
    ]
    artifacts: List[DiagramArtifact] = []
    for key, title, caption, kind, data in definitions:
        base = safe_slug(key)
        png_path = out_dir / f"{base}.png"
        svg_path = out_dir / f"{base}.svg"
        mmd_path = out_dir / f"{base}.mmd"
        if kind == "use_case":
            actor, boundary, use_cases, mermaid = data
            _draw_use_case_png(png_path, title, actor, boundary, use_cases)
            _write_use_case_svg(svg_path, title, actor, boundary, use_cases)
        else:
            boxes, lines, mermaid = data
            _draw_box_png(png_path, title, boxes, lines)
            _write_box_svg(svg_path, title, boxes, lines)
        write_text(mmd_path, mermaid)
        artifacts.append(
            DiagramArtifact(
                key=key,
                title=title,
                caption=caption,
                png_path=str(png_path),
                svg_path=str(svg_path),
                mermaid_path=str(mmd_path),
            )
        )
    write_json(out_dir / "diagram_manifest.json", artifacts)
    return artifacts


def generate_use_case_diagram(project_profile: ProjectProfile | Dict | str | Path, output_dir: str | Path = "outputs/diagrams") -> DiagramArtifact:
    return _artifact_by_key(generate_diagrams(project_profile, output_dir), "user_flow")


def generate_function_structure_diagram(project_profile: ProjectProfile | Dict | str | Path, output_dir: str | Path = "outputs/diagrams") -> DiagramArtifact:
    return _artifact_by_key(generate_diagrams(project_profile, output_dir), "function_structure")


def generate_system_architecture_diagram(project_profile: ProjectProfile | Dict | str | Path, output_dir: str | Path = "outputs/diagrams") -> DiagramArtifact:
    return _artifact_by_key(generate_diagrams(project_profile, output_dir), "architecture")


def generate_business_flow_diagram(project_profile: ProjectProfile | Dict | str | Path, output_dir: str | Path = "outputs/diagrams") -> DiagramArtifact:
    return _artifact_by_key(generate_diagrams(project_profile, output_dir), "business_flow")


def generate_er_diagram_from_sql(project_profile: ProjectProfile | Dict | str | Path, output_dir: str | Path = "outputs/diagrams") -> DiagramArtifact:
    return _artifact_by_key(generate_diagrams(project_profile, output_dir), "er")


def _architecture(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    boxes = [
        (260, 70, 620, 130, "表示层\n前端页面/用户交互"),
        (260, 210, 620, 270, "业务逻辑层\n接口服务/业务处理"),
        (260, 350, 620, 410, "数据访问层\n数据库/文件资源"),
    ]
    lines = [(440, 130, 440, 210), (440, 270, 440, 350)]
    mermaid = "flowchart TB\n  A[表示层] --> B[业务逻辑层]\n  B --> C[数据访问层]\n"
    return boxes, lines, mermaid


def _function_structure(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    modules = project.function_modules[:8] or ["登录认证", "信息管理", "查询统计", "后台管理"]
    boxes: List[Box] = [(330, 40, 550, 95, project.project_name or "系统功能")]
    lines: List[Line] = []
    for index, module in enumerate(modules):
        row = index // 4
        col = index % 4
        x1 = 70 + col * 205
        y1 = 170 + row * 120
        boxes.append((x1, y1, x1 + 150, y1 + 55, module))
        lines.append((440, 95, x1 + 75, y1))
    mermaid = "flowchart TB\n  Root[系统功能]\n" + "\n".join(f"  Root --> M{idx}[{module}]" for idx, module in enumerate(modules, 1))
    return boxes, lines, mermaid


def _business_flow(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    steps = project.business_flows[:6] or ["用户登录", "选择功能", "提交数据", "系统校验", "保存数据", "返回结果"]
    return _horizontal_flow(steps, "flowchart LR")


def _user_flow(project: ProjectProfile) -> UseCaseDiagram:
    modules = [item for item in project.function_modules if not _is_admin_module(item)][:4]
    use_cases = _use_case_items(["登录系统", "重置密码", *(modules or ["使用核心功能"]), "退出系统"])
    mermaid = _use_case_mermaid("用户", project.project_name or "系统", [item[4] for item in use_cases])
    return "用户", project.project_name or "系统", use_cases, mermaid


def _admin_flow(project: ProjectProfile) -> UseCaseDiagram:
    modules = [item for item in project.function_modules if _is_admin_module(item)][:4]
    use_cases = _use_case_items(["登录后台", *(modules or ["维护基础数据", "审核业务信息", "查看统计结果"]), "退出后台"])
    mermaid = _use_case_mermaid("管理员", project.project_name or "后台管理系统", [item[4] for item in use_cases])
    return "管理员", project.project_name or "后台管理系统", use_cases, mermaid


def _er_diagram(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    tables = project.database_tables[:8]
    if not tables:
        labels = ["用户表", "业务主表", "业务明细表", "日志表"]
    else:
        labels = [f"{table.name}\n" + "\n".join(_table_columns(table)[:4]) for table in tables]
    boxes: List[Box] = []
    lines: List[Line] = []
    center = (440, 240)
    radius_x = 285
    radius_y = 155
    for index, label in enumerate(labels):
        angle = 2 * math.pi * index / len(labels)
        cx = int(center[0] + math.cos(angle) * radius_x)
        cy = int(center[1] + math.sin(angle) * radius_y)
        boxes.append((cx - 75, cy - 45, cx + 75, cy + 45, label))
        if index:
            prev = boxes[index - 1]
            lines.append(((prev[0] + prev[2]) // 2, (prev[1] + prev[3]) // 2, cx, cy))
    if len(boxes) > 2:
        first = boxes[0]
        last = boxes[-1]
        lines.append(((first[0] + first[2]) // 2, (first[1] + first[3]) // 2, (last[0] + last[2]) // 2, (last[1] + last[3]) // 2))
    mermaid = "erDiagram\n" + "\n".join(f"  {safe_slug(label.splitlines()[0], 'TABLE').upper()} {{\n    string id\n  }}" for label in labels)
    return boxes, lines, mermaid


def _frontend_backend(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    boxes = [
        (60, 205, 210, 270, "用户浏览器"),
        (270, 205, 420, 270, "前端页面"),
        (480, 205, 630, 270, "后端接口"),
        (690, 205, 840, 270, "数据库"),
    ]
    lines = [(210, 238, 270, 238), (420, 238, 480, 238), (630, 238, 690, 238)]
    mermaid = (
        "sequenceDiagram\n"
        "  participant U as 用户\n"
        "  participant F as 前端\n"
        "  participant B as 后端\n"
        "  participant D as 数据库\n"
        "  U->>F: 操作页面\n"
        "  F->>B: 调用接口\n"
        "  B->>D: 读写数据\n"
        "  D-->>B: 返回结果\n"
        "  B-->>F: 响应数据\n"
    )
    return boxes, lines, mermaid


def _test_flow(project: ProjectProfile) -> Tuple[List[Box], List[Line], str]:
    return _horizontal_flow(["制定测试计划", "准备测试数据", "执行功能测试", "记录测试结果", "修复问题", "回归验证"], "flowchart LR")


def _horizontal_flow(steps: Sequence[str], header: str) -> Tuple[List[Box], List[Line], str]:
    boxes: List[Box] = []
    lines: List[Line] = []
    gap = 25
    width = 130
    start_x = max(40, int((900 - (len(steps) * width + (len(steps) - 1) * gap)) / 2))
    y1 = 215
    for index, step in enumerate(steps):
        x1 = start_x + index * (width + gap)
        boxes.append((x1, y1, x1 + width, y1 + 60, step))
        if index:
            lines.append((x1 - gap, y1 + 30, x1, y1 + 30))
    mermaid = header + "\n" + "\n".join(f"  N{idx}[{step}]" for idx, step in enumerate(steps, 1))
    mermaid += "\n" + "\n".join(f"  N{idx} --> N{idx + 1}" for idx in range(1, len(steps)))
    return boxes, lines, mermaid


def _use_case_items(labels: Sequence[str]) -> List[UseCase]:
    unique = _unique_labels(labels, limit=6)
    count = len(unique)
    start_y = 155 if count <= 4 else 130
    gap = 86 if count <= 4 else 70
    items: List[UseCase] = []
    for index, label in enumerate(unique):
        cy = start_y + index * gap
        items.append((510, cy - 32, 730, cy + 32, label))
    return items


def _unique_labels(labels: Sequence[str], limit: int) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for label in labels:
        clean = label.replace("模块", "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _use_case_mermaid(actor: str, boundary: str, labels: Sequence[str]) -> str:
    lines = ["flowchart LR", f"  A((\"{actor}\"))"]
    lines.append(f"  subgraph S[\"{boundary}\"]")
    for index, label in enumerate(labels, start=1):
        lines.append(f"    U{index}([\"{label}\"])")
    lines.append("  end")
    for index in range(1, len(labels) + 1):
        lines.append(f"  A --> U{index}")
    return "\n".join(lines) + "\n"


def _draw_box_png(path: Path, title: str, boxes: Iterable[Box], lines: Iterable[Line]) -> None:
    image = Image.new("RGB", (900, 520), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(24)
    body_font = _font(17)
    draw.text((450, 28), title, fill="black", anchor="mm", font=title_font)
    for x1, y1, x2, y2 in lines:
        draw.line((x1, y1, x2, y2), fill="black", width=2)
        _arrow(draw, x1, y1, x2, y2)
    for box in boxes:
        x1, y1, x2, y2, label = box
        draw.rectangle((x1, y1, x2, y2), outline="black", width=2)
        _draw_wrapped_text(draw, label, (x1, y1, x2, y2), body_font)
    image.save(path)


def _write_box_svg(path: Path, title: str, boxes: Iterable[Box], lines: Iterable[Line]) -> None:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520">',
        '<rect width="900" height="520" fill="white"/>',
        f'<text x="450" y="36" text-anchor="middle" font-size="24" font-family="SimSun, Microsoft YaHei, serif">{_escape(title)}</text>',
        _svg_marker(),
    ]
    for x1, y1, x2, y2 in lines:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="2" marker-end="url(#arrow)"/>')
    for x1, y1, x2, y2, label in boxes:
        parts.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="white" stroke="black" stroke-width="2"/>')
        rows = label.splitlines()
        start_y = y1 + (y2 - y1) / 2 - (len(rows) - 1) * 10
        for offset, row in enumerate(rows):
            parts.append(f'<text x="{(x1 + x2) / 2}" y="{start_y + offset * 22}" text-anchor="middle" font-size="16" font-family="SimSun, Microsoft YaHei, serif">{_escape(row)}</text>')
    parts.append("</svg>")
    write_text(path, "\n".join(parts))


def _draw_use_case_png(path: Path, title: str, actor: str, boundary: str, use_cases: List[UseCase]) -> None:
    image = Image.new("RGB", (900, 620), "white")
    draw = ImageDraw.Draw(image)
    label_font = _font(20)
    body_font = _font(18)
    line = "black"
    boundary_box = (430, 90, 790, 565)
    draw.rectangle(boundary_box, outline=line, width=2)
    actor_anchor = _draw_actor(draw, 200, 315, actor, label_font)
    for x1, y1, x2, y2, label in use_cases:
        draw.ellipse((x1, y1, x2, y2), outline=line, width=2)
        _draw_wrapped_text(draw, label, (x1 + 10, y1 + 8, x2 - 10, y2 - 8), body_font, max_chars=8)
        target = (x1, (y1 + y2) // 2)
        draw.line((actor_anchor[0], actor_anchor[1], target[0], target[1]), fill=line, width=2)
        _arrow(draw, actor_anchor[0], actor_anchor[1], target[0], target[1])
    image.save(path)


def _write_use_case_svg(path: Path, title: str, actor: str, boundary: str, use_cases: List[UseCase]) -> None:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620">',
        '<rect width="900" height="620" fill="white"/>',
        _svg_marker(),
        '<rect x="430" y="90" width="360" height="475" fill="white" stroke="black" stroke-width="2"/>',
        '<circle cx="200" cy="230" r="18" fill="white" stroke="black" stroke-width="2"/>',
        '<line x1="200" y1="248" x2="200" y2="325" stroke="black" stroke-width="2"/>',
        '<line x1="170" y1="278" x2="230" y2="278" stroke="black" stroke-width="2"/>',
        '<line x1="200" y1="325" x2="170" y2="375" stroke="black" stroke-width="2"/>',
        '<line x1="200" y1="325" x2="230" y2="375" stroke="black" stroke-width="2"/>',
        f'<text x="200" y="420" text-anchor="middle" font-size="20" font-weight="bold" font-family="SimSun, Microsoft YaHei, serif">{_escape(actor)}</text>',
    ]
    actor_x, actor_y = 230, 278
    for x1, y1, x2, y2, label in use_cases:
        cy = (y1 + y2) // 2
        parts.append(f'<line x1="{actor_x}" y1="{actor_y}" x2="{x1}" y2="{cy}" stroke="black" stroke-width="2" marker-end="url(#arrow)"/>')
        parts.append(f'<ellipse cx="{(x1 + x2) / 2}" cy="{cy}" rx="{(x2 - x1) / 2}" ry="{(y2 - y1) / 2}" fill="white" stroke="black" stroke-width="2"/>')
        parts.append(f'<text x="{(x1 + x2) / 2}" y="{cy + 6}" text-anchor="middle" font-size="18" font-family="SimSun, Microsoft YaHei, serif">{_escape(label)}</text>')
    parts.append("</svg>")
    write_text(path, "\n".join(parts))


def _draw_actor(draw: ImageDraw.ImageDraw, cx: int, cy: int, label: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    line = "black"
    head_y = cy - 85
    draw.ellipse((cx - 18, head_y - 18, cx + 18, head_y + 18), outline=line, width=2)
    draw.line((cx, head_y + 18, cx, cy), fill=line, width=2)
    draw.line((cx - 38, head_y + 52, cx + 38, head_y + 52), fill=line, width=2)
    draw.line((cx, cy, cx - 32, cy + 58), fill=line, width=2)
    draw.line((cx, cy, cx + 32, cy + 58), fill=line, width=2)
    draw.text((cx, cy + 98), label, fill=line, anchor="mm", font=font)
    return cx + 38, head_y + 52


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    label: str,
    box: Tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    max_chars: int = 10,
) -> None:
    x1, y1, x2, y2 = box
    rows: List[str] = []
    for raw in label.splitlines():
        if len(raw) <= max_chars:
            rows.append(raw)
        else:
            rows.extend([raw[index : index + max_chars] for index in range(0, len(raw), max_chars)])
    line_height = 22
    start_y = y1 + (y2 - y1 - len(rows) * line_height) / 2 + 10
    for index, row in enumerate(rows):
        draw.text(((x1 + x2) / 2, start_y + index * line_height), row, fill="black", anchor="mm", font=font)


def _arrow(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int) -> None:
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 10
    for delta in (math.pi * 0.85, -math.pi * 0.85):
        x = x2 + length * math.cos(angle + delta)
        y = y2 + length * math.sin(angle + delta)
        draw.line((x2, y2, x, y), fill="black", width=2)


def _svg_marker() -> str:
    return '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="black"/></marker></defs>'


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def _table_columns(table) -> List[str]:
    if getattr(table, "field_details", None):
        return [column.name for column in table.field_details]
    return table.columns


def _is_admin_module(value: str) -> bool:
    return any(keyword in value for keyword in ["后台", "管理", "权限", "统计", "审核"])


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _as_project_profile(value: ProjectProfile | Dict | str | Path) -> ProjectProfile:
    if isinstance(value, ProjectProfile):
        return value
    if isinstance(value, (str, Path)):
        value = read_json(value)
    return ProjectProfile(**value)


def _artifact_by_key(artifacts: List[DiagramArtifact], key: str) -> DiagramArtifact:
    for artifact in artifacts:
        if artifact.key == key:
            return artifact
    raise KeyError(f"diagram artifact not found: {key}")
