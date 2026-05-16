from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List


def parse_pdf_layout(pdf_path: str | Path) -> Dict[str, Any]:
    """Extract lightweight visual/text layout information from a reference PDF."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"参考 PDF 不存在: {path}")
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("解析 PDF 版式需要 PyMuPDF。请先安装 requirements.txt。") from exc

    document = fitz.open(str(path))
    pages: List[Dict[str, Any]] = []
    for index, page in enumerate(document, start=1):
        text = page.get_text("text") or ""
        blocks = page.get_text("dict").get("blocks", [])
        image_blocks = [block for block in blocks if block.get("type") == 1]
        images = []
        for block in image_blocks:
            bbox = block.get("bbox", [0, 0, 0, 0])
            images.append(
                {
                    "bbox": bbox,
                    "width_pt": round(float(bbox[2] - bbox[0]), 2),
                    "height_pt": round(float(bbox[3] - bbox[1]), 2),
                }
            )
        pages.append(
            {
                "page_number": index,
                "text": text,
                "clean_text": _clean_text(text),
                "image_count": len(images),
                "images": images,
                "size": {"width_pt": page.rect.width, "height_pt": page.rect.height},
            }
        )
    page_count = document.page_count
    document.close()
    return {
        "pdf_path": str(path),
        "page_count": page_count,
        "pages": pages,
        "full_text": "\n".join(page["text"] for page in pages),
    }


def extract_toc_items(layout: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    toc_pages = _find_pages_containing(layout, ["目", "录"])
    candidates = toc_pages or layout.get("pages", [])[:5]
    pattern = re.compile(r"^(.+?)(?:\.{2,}|…{2,})(\d+)\s*$")
    for page in candidates:
        for raw in page.get("text", "").splitlines():
            line = raw.strip()
            match = pattern.match(line)
            if not match:
                continue
            title = match.group(1).strip()
            items.append({"title": title, "page": match.group(2), "level": 2 if title.startswith("（") else 1})
    return items


def extract_caption_items(layout: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    figure_pattern = re.compile(r"图\s*(\d+)[-.](\d+)\s*(.+)")
    table_pattern = re.compile(r"表\s*(\d+)[-.](\d+)\s*(.+)")
    figures: List[Dict[str, Any]] = []
    tables: List[Dict[str, Any]] = []
    for page in layout.get("pages", []):
        for raw in page.get("text", "").splitlines():
            text = raw.strip()
            fig = figure_pattern.search(text)
            tab = table_pattern.search(text)
            if fig:
                figures.append({"page": page["page_number"], "chapter": fig.group(1), "index": fig.group(2), "caption": fig.group(3)})
            if tab:
                tables.append({"page": page["page_number"], "chapter": tab.group(1), "index": tab.group(2), "caption": tab.group(3)})
    return {"figures": figures, "tables": tables}


def detect_reference_regions(layout: Dict[str, Any]) -> Dict[str, Any]:
    pages = layout.get("pages", [])
    cover = pages[0]["clean_text"] if pages else ""
    integrity_pages = [page["page_number"] for page in pages if "诚信声明" in page.get("text", "") or "郑重声明" in page.get("text", "")]
    toc_pages = [page["page_number"] for page in pages if re.search(r"目\s*录", page.get("text", ""))]
    body_start_pages = [page["page_number"] for page in pages if "一、项目概述" in page.get("text", "")]
    return {
        "cover_text": cover,
        "integrity_pages": integrity_pages,
        "toc_pages": toc_pages,
        "body_start_pages": body_start_pages,
    }


def _find_pages_containing(layout: Dict[str, Any], tokens: List[str]) -> List[Dict[str, Any]]:
    result = []
    for page in layout.get("pages", []):
        text = page.get("text", "")
        if all(token in text for token in tokens):
            result.append(page)
    return result


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
