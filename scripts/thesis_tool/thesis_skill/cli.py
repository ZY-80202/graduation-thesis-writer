from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from thesis_skill.analyzer.outline_mapper import build_outline
from thesis_skill.analyzer.previous_thesis_analyzer import analyze_previous
from thesis_skill.analyzer.template_analyzer import analyze_template
from thesis_skill.docx_writer.docx_builder import build_docx
from thesis_skill.generator.diagram_generator import generate_diagrams
from thesis_skill.generator.thesis_writer import build_thesis_draft
from thesis_skill.models import DiagramArtifact, OutlineSection, ProjectProfile, TemplateProfile
from thesis_skill.parsers.project_parser import parse_project
from thesis_skill.utils.file_utils import ensure_dir, read_json, write_json
from thesis_skill.validators.format_validator import validate_docx
from thesis_skill.validators.plagiarism_guard import check_plagiarism_risk

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
    build_outline_cmd.set_defaults(func=cmd_build_outline)

    build_diagrams = sub.add_parser("build-diagrams", help="生成流程图和结构图")
    build_diagrams.add_argument("--project", required=True)
    build_diagrams.add_argument("--out", default="outputs/diagrams")
    build_diagrams.set_defaults(func=cmd_build_diagrams)

    build = sub.add_parser("build", help="生成完整论文 Word")
    build.add_argument("--template", required=True)
    build.add_argument("--previous-docx")
    build.add_argument("--previous-pdf")
    build.add_argument("--project", required=True)
    build.add_argument("--out", default="outputs/final_thesis.docx")
    build.set_defaults(func=cmd_build)

    validate = sub.add_parser("validate", help="检查论文格式")
    validate.add_argument("--docx", required=True)
    validate.add_argument("--template")
    validate.add_argument("--out", default="outputs")
    validate.set_defaults(func=cmd_validate)
    return parser


def cmd_inspect_template(args: argparse.Namespace) -> None:
    profile = analyze_template(args.template, args.out)
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
    template_profile = analyze_template(args.template, args.out)
    previous_profile = analyze_previous(args.previous, None, args.out) if args.previous else None
    project_profile = parse_project(args.project, args.out)
    outline = build_outline(template_profile, previous_profile, project_profile, args.out)
    _ok(f"论文大纲生成完成: {Path(args.out) / 'outline.json'}")
    _info(f"一级章节数: {len(outline)}")


def cmd_build_diagrams(args: argparse.Namespace) -> None:
    profile = _project_from_path_or_profile(args.project)
    artifacts = generate_diagrams(profile, args.out)
    _ok(f"流程图生成完成: {args.out}")
    _info(f"生成图表数: {len(artifacts)}")


def cmd_build(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    ensure_dir("outputs/profiles")
    ensure_dir("outputs/diagrams")
    template_profile = analyze_template(args.template, "outputs/profiles")
    previous_profile = analyze_previous(args.previous_docx, args.previous_pdf, "outputs/profiles") if args.previous_docx or args.previous_pdf else None
    project_profile = parse_project(args.project, "outputs/profiles")
    outline = build_outline(template_profile, previous_profile, project_profile, "outputs/profiles")
    diagrams: List[DiagramArtifact] = []
    if config.get("project", {}).get("generate_diagrams", True):
        diagrams = generate_diagrams(project_profile, "outputs/diagrams")
    thesis = build_thesis_draft(project_profile, outline, config, "outputs")
    out_path = build_docx(args.template, thesis, project_profile, diagrams, args.out, config)
    validate_docx(out_path, args.template, "outputs")
    if args.previous_docx or args.previous_pdf:
        check_plagiarism_risk(out_path, args.previous_docx, args.previous_pdf, "outputs")
    _ok(f"完整论文生成完成: {out_path}")
    _info("已生成 outputs/thesis_draft.json、outputs/content_gap_report.md、outputs/missing_items.md、outputs/format_check_report.md")


def cmd_validate(args: argparse.Namespace) -> None:
    report = validate_docx(args.docx, args.template, args.out)
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
    current_key = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current_key = line[:-1].strip()
            result[current_key] = {}
            current = result[current_key]
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
