from __future__ import annotations

from docx.enum.section import WD_SECTION

from thesis_skill.docx_writer.header_footer_manager import apply_template_header_footer, clear_header_footer_links, suppress_header_on_cover
from thesis_skill.docx_writer.page_number_manager import add_page_number_to_footer, set_arabic_page_numbers, set_roman_page_numbers


def create_front_matter_section(document):
    section = document.add_section(WD_SECTION.NEW_PAGE)
    clear_header_footer_links(section)
    set_roman_page_numbers(section, 1)
    add_page_number_to_footer(section)
    return section


def create_body_section(document, short_title: str = ""):
    section = document.add_section(WD_SECTION.NEW_PAGE)
    clear_header_footer_links(section)
    apply_template_header_footer(section, short_title)
    set_arabic_page_numbers(section, 1)
    add_page_number_to_footer(section)
    return section


def configure_cover_section(document) -> None:
    if document.sections:
        suppress_header_on_cover(document.sections[0])
