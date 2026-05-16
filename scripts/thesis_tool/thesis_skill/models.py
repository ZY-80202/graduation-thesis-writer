from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - exercised only when pydantic is absent.
    from pydantic import BaseModel, Field
except Exception:  # Lightweight fallback keeps the CLI usable before dependencies are installed.
    class _Field:
        def __init__(self, default: Any = None, default_factory: Any = None, **_: Any) -> None:
            self.default = default
            self.default_factory = default_factory

        def value(self) -> Any:
            if self.default_factory is not None:
                return self.default_factory()
            return self.default

    def Field(default: Any = None, default_factory: Any = None, **kwargs: Any) -> Any:
        return _Field(default, default_factory, **kwargs)

    class BaseModel:
        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                raw_default = getattr(self.__class__, name, None)
                if name in data:
                    value = data[name]
                elif isinstance(raw_default, _Field):
                    value = raw_default.value()
                else:
                    value = raw_default
                setattr(self, name, value)
            for name, value in data.items():
                if not hasattr(self, name):
                    setattr(self, name, value)

        def model_dump(self, **_: Any) -> Dict[str, Any]:
            def dump(value: Any) -> Any:
                if isinstance(value, BaseModel):
                    return value.model_dump()
                if isinstance(value, list):
                    return [dump(item) for item in value]
                if isinstance(value, dict):
                    return {key: dump(item) for key, item in value.items()}
                if isinstance(value, Path):
                    return str(value)
                return value

            return {key: dump(value) for key, value in vars(self).items()}

        def model_dump_json(self, **_: Any) -> str:
            return json.dumps(self.model_dump(), ensure_ascii=False, indent=2)


class PageSettings(BaseModel):
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    top_margin_cm: Optional[float] = None
    bottom_margin_cm: Optional[float] = None
    left_margin_cm: Optional[float] = None
    right_margin_cm: Optional[float] = None
    header_distance_cm: Optional[float] = None
    footer_distance_cm: Optional[float] = None
    header_text: str = ""
    footer_text: str = ""


class ParagraphStyleProfile(BaseModel):
    style_name: str
    font_name: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    alignment: Optional[str] = None
    line_spacing: Optional[str] = None
    first_line_indent_pt: Optional[float] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None


class TemplateRegion(BaseModel):
    name: str
    keyword: str
    paragraph_index: int


class TemplateProfile(BaseModel):
    template_path: str
    page_settings: List[PageSettings] = Field(default_factory=list)
    styles: Dict[str, ParagraphStyleProfile] = Field(default_factory=dict)
    regions: List[TemplateRegion] = Field(default_factory=list)
    detected_keywords: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ChapterItem(BaseModel):
    level: int
    number: str = ""
    title: str
    source: str = ""
    purpose: str = ""


class PreviousThesisProfile(BaseModel):
    docx_path: Optional[str] = None
    pdf_path: Optional[str] = None
    toc_items: List[ChapterItem] = Field(default_factory=list)
    chapter_items: List[ChapterItem] = Field(default_factory=list)
    figure_number_patterns: List[str] = Field(default_factory=list)
    table_number_patterns: List[str] = Field(default_factory=list)
    writing_patterns: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class DatabaseColumn(BaseModel):
    name: str
    data_type: str = ""
    is_primary_key: bool = False
    nullable: bool = True
    default: str = ""
    comment: str = ""


class DatabaseTable(BaseModel):
    name: str
    columns: List[str] = Field(default_factory=list)
    field_details: List[DatabaseColumn] = Field(default_factory=list)
    comment: str = ""
    source: str = ""


class BackendEndpoint(BaseModel):
    method: str = ""
    path: str
    name: str = ""
    description: str = ""
    source: str = ""


class FrontendPage(BaseModel):
    name: str
    file_path: str
    route_path: str = ""
    title: str = ""
    matched_module: str = ""


class ScreenshotAsset(BaseModel):
    path: str
    file_name: str
    inferred_section: str = ""
    matched_module: str = ""
    caption: str = ""


class ProjectProfile(BaseModel):
    project_path: str
    project_name: str = ""
    technology_stack: List[str] = Field(default_factory=list)
    function_modules: List[str] = Field(default_factory=list)
    user_roles: List[str] = Field(default_factory=list)
    database_tables: List[DatabaseTable] = Field(default_factory=list)
    business_flows: List[str] = Field(default_factory=list)
    frontend_pages: List[str] = Field(default_factory=list)
    frontend_page_details: List[FrontendPage] = Field(default_factory=list)
    backend_endpoints: List[BackendEndpoint] = Field(default_factory=list)
    test_points: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    screenshot_assets: List[ScreenshotAsset] = Field(default_factory=list)
    source_materials: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class OutlineSection(BaseModel):
    level: int
    number: str
    title: str
    purpose: str = ""
    children: List["OutlineSection"] = Field(default_factory=list)


class DiagramArtifact(BaseModel):
    key: str
    title: str
    caption: str
    png_path: str
    svg_path: str
    mermaid_path: Optional[str] = None


class SectionDraft(BaseModel):
    number: str
    title: str
    level: int
    paragraphs: List[str] = Field(default_factory=list)
    children: List["SectionDraft"] = Field(default_factory=list)


class ThesisDocument(BaseModel):
    title: str
    author: str = ""
    student_id: str = ""
    college: str = ""
    major: str = ""
    supervisor: str = ""
    abstract_cn: str = ""
    abstract_en: str = ""
    keywords: List[str] = Field(default_factory=list)
    sections: List[SectionDraft] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    acknowledgements: str = ""
    appendices: List[str] = Field(default_factory=list)
    placeholders: List[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    severity: str
    message: str
    location: str = ""


class ValidationReport(BaseModel):
    docx_path: str
    issues: List[ValidationIssue] = Field(default_factory=list)
    summary: str = ""


OutlineSection.model_rebuild() if hasattr(OutlineSection, "model_rebuild") else None
SectionDraft.model_rebuild() if hasattr(SectionDraft, "model_rebuild") else None
