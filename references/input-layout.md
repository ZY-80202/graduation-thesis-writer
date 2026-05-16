# Input Layout Notes

Use this reference only when the user asks how to prepare files.

## Project Directory

```text
inputs/project/
├── project_note.md
├── database.sql
├── screenshots/
└── source_code/
    ├── backend/
    └── frontend/
```

## Recognition Hints

- Put `CREATE TABLE` statements in `database.sql`; MySQL-style `COMMENT` values become field descriptions.
- Put route/controller/API files under `source_code/backend/`; common Flask, FastAPI, Express, Spring, and NestJS patterns are scanned.
- Put pages/components under `source_code/frontend/`; common `.vue`, `.tsx`, `.jsx`, `.html`, and `.svelte` page files are scanned.
- Name screenshots with functional keywords: `login`, `register`, `user`, `product`, `order`, `cart`, `comment`, `admin`, `dashboard`, `test`.
