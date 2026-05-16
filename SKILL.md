---
name: graduation-thesis-writer
description: Generate Chinese graduation-design thesis drafts from a school Word template, previous thesis reference files, and local project materials. Use when Codex needs to inspect DOCX/PDF thesis templates, parse database.sql, analyze source_code/backend routes and source_code/frontend pages, insert screenshots from screenshots, generate diagrams, build final_thesis.docx, or produce missing_items/content/format/plagiarism reports for undergraduate or junior-college software-project theses.
---

# Graduation Thesis Writer

Use the bundled Python CLI to generate a repeatable Chinese graduation thesis workspace. The previous thesis is only a structure and style reference; never copy its body text into the new thesis.

## Bundled Tool

Tool root:

```text
<this skill>/scripts/thesis_tool
```

Run from the user's thesis workspace, not from the skill directory, so inputs and outputs are created in the user's project folder.

PowerShell pattern:

```powershell
$env:PYTHONPATH="C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool"
py -m graduation_thesis_writer --help
```

Install dependencies when needed:

```powershell
py -m pip install -r C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool\requirements.txt
```

If the workspace lacks config.yaml, copy the bundled template from scripts/thesis_tool/config.yaml and ask the user to fill title, author, student id, college, major, supervisor, and project name.

## Expected Inputs

Preferred layout in the user's workspace:

```text
inputs/
|-- template.docx or template.doc
|-- previous.docx
|-- previous.pdf
`-- project/
    |-- project_note.md
    |-- database.sql
    |-- screenshots/
    `-- source_code/
        |-- backend/
        `-- frontend/
```

Screenshot filenames should include functional keywords when possible, such as login_page.png, user_manage.png, product_list.png, order_detail.png, admin_dashboard.png, or test_result.png.

## Main Workflow

1. Check or create inputs/ and config.yaml.
2. Run project inspection first when debugging recognition:

```powershell
$env:PYTHONPATH="C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool"
py -m graduation_thesis_writer inspect-project --project inputs/project/
```

3. Generate the full thesis:

```powershell
$env:PYTHONPATH="C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool"
py -m graduation_thesis_writer build `
  --template inputs/template.docx `
  --previous-docx inputs/previous.docx `
  --previous-pdf inputs/previous.pdf `
  --project inputs/project/ `
  --out outputs/final_thesis.docx `
  --strict-template `
  --toc-mode static
```

Omit --previous-pdf if no PDF is available.

4. For strict school-template reproduction, prefer:

```powershell
$env:PYTHONPATH="C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool"
py -m graduation_thesis_writer build `
  --template inputs/template.doc `
  --project inputs/project/ `
  --config config.yaml `
  --out outputs/final_thesis.docx `
  --strict-template `
  --render-check `
  --max-pages 35 `
  --toc-mode static `
  --cover-pages 2 `
  --no-number-front-matter `
  --black-white-diagrams
```

5. For a previous-PDF layout match, especially website theses that use Chinese numbering and many screenshots/code screenshots, use:

```powershell
$env:PYTHONPATH="C:\Users\t1937\.codex\skills\graduation-thesis-writer\scripts\thesis_tool"
py -m graduation_thesis_writer build `
  --template-reference reference.pdf `
  --project inputs/project `
  --config config.yaml `
  --out outputs/final_thesis.docx `
  --match-pdf-layout `
  --target-pages 28 `
  --toc-with-page-numbers `
  --chinese-section-numbering `
  --image-heavy-implementation
```

This mode creates the reference-style cover, an independent integrity statement page, a static dot-leader TOC with page numbers, Chinese section headings, and an image-heavy implementation chapter. It must not copy body text from the reference PDF.

6. If using `--toc-mode field`, tell the user to open Word and update the TOC field manually. If render/layout checks fail, inspect the generated `_draft.docx` and reports instead of treating it as final.
7. Review these outputs with the user:

```text
outputs/final_thesis.docx
outputs/missing_items.md
outputs/content_gap_report.md
outputs/format_check_report.md
outputs/render_check_report.md
outputs/reference_check_report.md
outputs/length_report.md
outputs/profiles/reference_layout_profile.json
outputs/plagiarism_risk_report.md
outputs/profiles/project_profile.json
outputs/diagrams/
```

## Capabilities

- Extract school template page settings, header/footer text, styles, and region keywords.
- In strict-template mode, clone the template cover/front matter OOXML instead of redrawing it, preserving logos, underlines, tables, text boxes, footers, and section settings where possible.
- In PDF layout mode, parse reference.pdf into reference_layout_profile.json and match cover/front matter, Chinese heading numbering, static TOC, figure/table caption style, and image-heavy implementation layout.
- Extract previous thesis outline and figure/table numbering patterns without reusing body text.
- Parse database.sql/init.sql/schema.sql into database tables and field-detail tables with field name, type, length, primary key, nullable, default, and comment.
- Extract API design rows from route/controller files in source_code/backend.
- Extract frontend page rows from page files in source_code/frontend.
- Classify screenshots by filename and insert them into matching sections with continuous figure captions.
- Generate user/admin UML-style use case diagrams with a stick-figure actor, system boundary rectangle, oval use cases, and arrowed associations.
- Generate black-and-white PNG/SVG/Mermaid diagrams and Word table captions.
- Keep abstract/table of contents unnumbered, start body at `1 概述`, restart Arabic body page numbering, and generate either a Word TOC field or a static dot-leader TOC.
- For website projects, generate the fixed Chinese-numbered body structure, plus independent references and acknowledgements, with detailed database tables and testing tables.
- Map screenshots and code screenshots from `screenshots/` and `code_screenshots/`; preserve figure numbers with placeholders when files are missing and report them in missing_items.md.
- Run optional LibreOffice/PyMuPDF render checks and emit render_check_report.md.
- Emit missing_items.md for fields, screenshots, interface details, tests, references, and other content requiring human completion.

## Useful Commands

```powershell
py -m graduation_thesis_writer inspect-template --template inputs/template.docx
py -m graduation_thesis_writer inspect-previous --docx inputs/previous.docx --pdf inputs/previous.pdf
py -m graduation_thesis_writer build-outline --template inputs/template.docx --previous inputs/previous.docx --project inputs/project/
py -m graduation_thesis_writer build-diagrams --project inputs/project/ --out outputs/diagrams/
py -m graduation_thesis_writer validate --docx outputs/final_thesis.docx --template inputs/template.docx
```

Always prefix commands with the PYTHONPATH assignment above unless the tool has been copied into the workspace.
