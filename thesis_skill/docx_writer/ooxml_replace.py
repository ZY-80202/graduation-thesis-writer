from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict

from lxml import etree

WORD_XML_PREFIXES = (
    "word/document.xml",
    "word/header",
    "word/footer",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
)
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}


def replace_text_in_ooxml(docx_path: str | Path, replacements: Dict[str, str], output_path: str | Path | None = None) -> Path:
    """Replace text across document body, tables, text boxes, headers, and footers.

    Replacement keeps the first matched run's styling. When a placeholder spans
    multiple runs, the first run receives the replaced text and remaining runs
    in the paragraph are cleared. This is less invasive than rebuilding the
    paragraph and preserves the surrounding OOXML layout.
    """

    source = Path(docx_path)
    if not source.exists():
        raise FileNotFoundError(f"DOCX 不存在: {source}")
    if not replacements:
        return source
    target = Path(output_path) if output_path else source

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        with zipfile.ZipFile(source, "r") as zin:
            zin.extractall(tmp_dir)

        for xml_path in _iter_word_xml(tmp_dir):
            _replace_in_xml_file(xml_path, replacements)

        if target.exists() and target.resolve() != source.resolve():
            target.unlink()
        temp_docx = tmp_dir / "_patched.docx"
        with zipfile.ZipFile(temp_docx, "w", zipfile.ZIP_DEFLATED) as zout:
            for file_path in tmp_dir.rglob("*"):
                if file_path.is_file() and file_path.name != "_patched.docx":
                    zout.write(file_path, file_path.relative_to(tmp_dir).as_posix())
        shutil.copy2(temp_docx, target)
    return target


def _iter_word_xml(root: Path):
    word_dir = root / "word"
    if not word_dir.exists():
        return
    for file_path in word_dir.rglob("*.xml"):
        relative = file_path.relative_to(root).as_posix()
        if relative.startswith(WORD_XML_PREFIXES):
            yield file_path


def _replace_in_xml_file(xml_path: Path, replacements: Dict[str, str]) -> None:
    parser = etree.XMLParser(remove_blank_text=False, recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    changed = False
    for text_node in root.xpath(".//w:t", namespaces=NS):
        if text_node.text:
            new_text = _replace_text(text_node.text, replacements)
            if new_text != text_node.text:
                text_node.text = new_text
                changed = True

    for paragraph in root.xpath(".//w:p", namespaces=NS):
        text_nodes = paragraph.xpath(".//w:t", namespaces=NS)
        if len(text_nodes) <= 1:
            continue
        combined = "".join(node.text or "" for node in text_nodes)
        replaced = _replace_text(combined, replacements)
        if replaced != combined:
            text_nodes[0].text = replaced
            text_nodes[0].set(f"{{{XML_NS}}}space", "preserve")
            for node in text_nodes[1:]:
                node.text = ""
            changed = True

    if changed:
        tree.write(str(xml_path), encoding="UTF-8", xml_declaration=True, standalone=False)


def _replace_text(text: str, replacements: Dict[str, str]) -> str:
    result = text
    for old, new in replacements.items():
        if old:
            result = result.replace(old, new)
    return result
