from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from thesis_skill.analyzer.outline_mapper import build_outline
from thesis_skill.analyzer.pdf_reference_analyzer import analyze_pdf_reference
from thesis_skill.analyzer.previous_thesis_analyzer import analyze_previous
from thesis_skill.analyzer.template_analyzer import analyze_template
from thesis_skill.docx_writer.docx_builder import build_docx
from thesis_skill.docx_writer.numbering_manager import normalize_outline_numbering
from thesis_skill.docx_writer.pdf_layout_builder import build_pdf_layout_docx
from thesis_skill.docx_writer.template_clone import prepare_template_docx
from thesis_skill.generator.diagram_generator import generate_diagrams
from thesis_skill.generator.thesis_writer import build_thesis_draft
from thesis_skill.models import DiagramArtifact, ProjectProfile
from thesis_skill.parsers.project_parser import parse_project
from thesis_skill.utils.file_utils import ensure_dir, read_json
from thesis_skill.validators.format_validator import validate_docx
from thesis_skill.validators.plagiarism_guard import check_plagiarism_risk
from thesis_skill.validators.render_validator import validate_rendered_docx

try:
    from rich.console import Console
except Exception:  # pragma: no cover
    Console = None


console = Console() if Console else None


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    try:
        args.func(args)
    except Exception as exc:
        _error(str(exc))
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="graduation-thesis-writer", description="毕业设计论文自动生成工具")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径，默认 config.yaml")
    sub = parser.add_subparsers(dest="command")

    inspect_template = sub.add_parser("inspect-template", help="分析学校 Word 模板")
    inspect_template.add_argument("--template", required=True)
    inspect_template.add_argument("--out", default="outputs/profiles")
    inspect_template.set_defaults(func=cmd_inspect_template)

    inspect_previous = sub.add_parser("inspect-previous", help="分析上一届论文结构")
    inspect_previous.add_argument("--docx")
    inspect_previous.add_argument("--pdf")
    inspect_previous.add_argument("--out", default="outputs/profiles")
    inspect_previous.set_defaults(func=cmd_inspect_previous)

    inspect_project = sub.add_parser("inspect-project", help="分析项目资料目录")
    inspect_project.add_argument("--project", required=True)
    inspect_project.add_argument("--out", default="outputs/profiles")
    inspect_project.set_defaults(func=cmd_inspect_project)

    build_outline_cmd = sub.add_parser("build-outline", help="生成论文大纲")
    build_outline_cmd.add_argument("--template", required=True)
    build_outline_cmd.add_argument("--previous")
    build_outline_cmd.add_argument("--project", required=True)
    build_outline_cmd.add_argument("--out", default="outputs/profiles")
    build_outline_cmd.add_argument("--body-start-title", default="概述")
    build_outline_cmd.set_defaults(func=cmd_build_outline)

    build_diagrams = sub.add_parser("build-diagrams", help="生成流程图和结构图")
    build_diagrams.add_argument("--project", required=True)
    build_diagrams.add_argument("--out", default="outputs/diagrams")
    build_diagrams.add_argument("--black-white-diagrams", action="store_true", help="使用黑白论文图风格")
    build_diagrams.set_defaults(func=cmd_build_diagrams)

    build = sub.add_parser("build", help="生成完整论文 Word")
    build.add_argument("--template")
    build.add_argument("--template-reference", help="PDF 原始版参考文件，用于 match-pdf-layout 模式")
    build.add_argument("--previous-docx")
    build.add_argument("--previous-pdf")
    build.add_argument("--project", required=True)
    build.add_argument("--out", default="outputs/final_thesis.docx")
    build.add_argument("--strict-template", action="store_true", help="强制复用模板封面、样式、页眉页脚和分节")
    build.add_argument("--render-check", action="store_true", help="生成后调用 LibreOffice/PyMuPDF 做渲染视觉检查")
    build.add_argument("--max-pages", type=int, default=35, help="最大页数，默认 35")
    build.add_argument("--toc-mode", choices=["field", "static"], default="field", help="目录模式: Word 域或静态点引导符目录")
    build.add_argument("--cover-pages", type=int, default=2, help="模板前几页作为封面/起讫日期页复制")
    build.add_argument("--body-start-title", default="概述", help="正文第一章标题")
    build.add_argument("--no-number-front-matter", action="store_true", help="前置部分不编号")
    build.add_argument("--black-white-diagrams", action="store_true", help="流程图使用黑白风格")
    build.add_argument("--match-pdf-layout", action="store_true", help="按参考 PDF 原始版式生成封面、目录、中文章节和图文密集正文")
    build.add_argument("--target-pages", type=int, default=28, help="PDF 对齐模式目标页数，默认 28")
    build.add_argument("--toc-with-page-numbers", action="store_true", help="强制静态目录包含点引导符和页码")
    build.add_argument("--chinese-section-numbering", action="store_true", help="使用“一、”“（一）”中文章节编号")
    build.add_argument("--image-heavy-implementation", action="store_true", help="网站实现章节采用截图/代码图密集排版")
    build.set_defaults(func=cmd_build)

    validate = sub.add_parser("validate", help="检查论文格式")
    validate.add_argument("--docx", required=True)
    validate.add_argument("--template")
    validate.add_argument("--out", default="outputs")
    validate.add_argument("--render-check", action="store_true")
    validate.add_argument("--max-pages", type=int, default=35)
    validate.add_argument("--min-pages", type=int)
    validate.add_argument("--match-pdf-layout", action="store_true")
    validate.set_defaults(func=cmd_validate)
    return parser


def cmd_inspect_template(args: argparse.Namespace) -> None:
    template = prepare_template_docx(args.template)
    profile = analyze_template(template, args.out)
    _ok(f"模板分析完成: {Path(args.out) / 'template_profile.json'}")
    _json_hint(profile)


def cmd_inspect_previous(args: argparse.Namespace) -> None:
    profile = analyze_previous(args.docx, args.pdf, args.out)
    _ok(f"上一届论文结构分析完成: {Path(args.out) / 'previous_profile.json'}")
    _info(f"识别章节数: {len(profile.chapter_items)}")


def cmd_inspect_project(args: argparse.Namespace) -> None:
    profile = parse_project(args.project, args.out)
    _ok(f"项目资料分析完成: {Path(args.out) / 'project_profile.json'}")
    _info(f"识别模块: {', '.join(profile.function_modules[:8]) or '暂无'}")


def cmd_build_outline(args: argparse.Namespace) -> None:
    template = prepare_template_docx(args.template)
    template_profile = analyze_template(template, args.out)
    previous_profile = analyze_previous(args.previous, None, args.out) if args.previous else None
    project_profile = parse_project(args.project, args.out)
    outline = build_outline(template_profile, previous_profile, project_profile, args.out)
    outline = normalize_outline_numbering(outline, body_start_title=args.body_start_title)
    _ok(f"论文大纲生成完成: {Path(args.out) / 'outline.json'}")
    _info(f"一级章节数: {len(outline)}")


def cmd_build_diagrams(args: argparse.Namespace) -> None:
    profile = _project_from_path_or_profile(args.project)
    artifacts = generate_diagrams(profile, args.out)
    _ok(f"流程图生成完成: {args.out}")
    _info(f"生成图表数: {len(artifacts)}")


def cmd_build(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    config.setdefault("format", {})["max_pages"] = args.max_pages
    ensure_dir("outputs/profiles")
    ensure_dir("outputs/diagrams")

    if args.match_pdf_layout:
        project_profile = parse_project(args.project, "outputs/profiles")
        layout_profile = analyze_pdf_reference(args.template_reference, "outputs/profiles") if args.template_reference else None
        requested_out = Path(args.out)
        build_target = _draft_path(requested_out)
        out_path = build_pdf_layout_docx(
            project_profile,
            config,
            build_target,
            layout_profile=layout_profile,
            target_pages=args.target_pages,
            toc_with_page_numbers=args.toc_with_page_numbers or True,
            image_heavy_implementation=args.image_heavy_implementation or True,
            output_dir="outputs",
        )
        validate_docx(out_path, args.template, "outputs")
        render_issues = validate_rendered_docx(
            out_path,
            "outputs",
            max_pages=args.target_pages + 2,
            min_pages=max(1, args.target_pages - 2),
            match_pdf_layout=True,
        )
        blocking = [issue for issue in render_issues if issue.severity == "error"]
        if blocking:
            _error(f"PDF 版式渲染检查未通过，已保留草稿: {out_path}")
            _info("请查看 outputs/render_check_report.md、outputs/format_check_report.md 和 outputs/missing_items.md")
            return
        ensure_dir(requested_out.parent)
        shutil.copy2(out_path, requested_out)
        _ok(f"PDF 原始版对齐论文生成完成: {requested_out}")
        _info("已生成 outputs/reference_layout_profile.json、outputs/missing_items.md、outputs/render_check_report.md")
        return

    if not args.template:
        raise ValueError("普通 build 模式需要提供 --template；PDF 对齐模式请使用 --match-pdf-layout --template-reference reference.pdf。")

    template = prepare_template_docx(args.template)
    template_profile = analyze_template(template, "outputs/profiles")
    previous_profile = analyze_previous(args.previous_docx, args.previous_pdf, "outputs/profiles") if args.previous_docx or args.previous_pdf else None
    project_profile = parse_project(args.project, "outputs/profiles")
    outline = build_outline(template_profile, previous_profile, project_profile, "outputs/profiles")
    outline = normalize_outline_numbering(outline, body_start_title=args.body_start_title)

    diagrams: List[DiagramArtifact] = []
    if config.get("project", {}).get("generate_diagrams", True):
        diagrams = generate_diagrams(project_profile, "outputs/diagrams")

    thesis = build_thesis_draft(project_profile, outline, config, "outputs")
    requested_out = Path(args.out)
    build_target = _draft_path(requested_out) if args.render_check else requested_out
    out_path = build_docx(
        template,
        thesis,
        project_profile,
        diagrams,
        build_target,
        config,
        strict_template=args.strict_template,
        cover_pages=args.cover_pages,
        toc_mode=args.toc_mode,
        body_start_title=args.body_start_title,
        max_pages=args.max_pages,
    )

    validate_docx(out_path, template, "outputs")
    render_issues = validate_rendered_docx(out_path, "outputs", max_pages=args.max_pages) if args.render_check else []
    blocking = [issue for issue in render_issues if issue.severity == "error"]
    if args.previous_docx or args.previous_pdf:
        check_plagiarism_risk(out_path, args.previous_docx, args.previous_pdf, "outputs")

    if args.render_check and blocking:
        _error(f"渲染检查未通过，已保留草稿: {out_path}")
        _info("请查看 outputs/render_check_report.md 和 outputs/format_check_report.md")
        return
    if args.render_check:
        ensure_dir(requested_out.parent)
        shutil.copy2(out_path, requested_out)
        out_path = requested_out

    _ok(f"完整论文生成完成: {out_path}")
    _info("已生成 outputs/thesis_draft.json、outputs/missing_items.md、outputs/content_gap_report.md、outputs/format_check_report.md")


def cmd_validate(args: argparse.Namespace) -> None:
    report = validate_docx(args.docx, args.template, args.out)
    if args.render_check:
        validate_rendered_docx(args.docx, args.out, max_pages=args.max_pages, min_pages=args.min_pages, match_pdf_layout=args.match_pdf_layout)
    _ok(f"格式检查完成: {Path(args.out) / 'format_check_report.md'}")
    _info(report.summary)


def load_config(path: str | Path) -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    if config_path.suffix.lower() == ".json":
        return json.loads(config_path.read_text(encoding="utf-8"))
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return data or {}
    except Exception:
        return _tiny_yaml(config_path.read_text(encoding="utf-8"))


def _tiny_yaml(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    current: Dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            key = line[:-1].strip()
            result[key] = {}
            current = result[key]
        elif current is not None and ":" in line:
            key, value = line.strip().split(":", 1)
            current[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _project_from_path_or_profile(path: str | Path) -> ProjectProfile:
    value = Path(path)
    if value.is_file() and value.suffix.lower() == ".json":
        return ProjectProfile(**read_json(value))
    if value.is_dir():
        profile_path = value / "project_profile.json"
        if profile_path.exists():
            return ProjectProfile(**read_json(profile_path))
        return parse_project(value, "outputs/profiles")
    raise FileNotFoundError(f"项目目录或 project_profile.json 不存在: {value}")


def _draft_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}_draft{path.suffix}")


def _json_hint(value: Any) -> None:
    if hasattr(value, "model_dump"):
        data = value.model_dump()
        _info(json.dumps({key: data[key] for key in list(data)[:3]}, ensure_ascii=False, indent=2)[:600])


def _ok(message: str) -> None:
    if console:
        console.print(f"[bold green]OK[/] {message}")
    else:
        print(f"OK {message}")


def _info(message: str) -> None:
    if console:
        console.print(message)
    else:
        print(message)


def _error(message: str) -> None:
    if console:
        console.print(f"[bold red]ERROR[/] {message}")
    else:
        print(f"ERROR {message}")
