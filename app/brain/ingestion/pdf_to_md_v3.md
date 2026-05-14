---
title: "pdf_to_md_v3.py — PDF to Markdown extractor"
tags:
  - surf/script
  - surf/brain
  - surf/ingestion
status: docs
bucket: app/brain/ingestion
---

# `app/brain/ingestion/pdf_to_md_v3.py`

Converts a class factsheet or lecture PDF into Markdown with page markers. It
uses native PDF text and table extraction first, then OCR only when requested by
the CLI or when native extraction is too sparse.

## Purpose

This is the first local ingestion step before prompt-backed generation:

```text
PDF upload
  → pdf_to_md_v3 extracts Markdown with --- PAGE N --- markers
  → page_splitter can split lecture pages
  → lecture ingestion sends text to LO and MCQ generation callers
```

The script itself does not call Anthropic, does not read API keys, and does not
write SQLite rows.

## Inputs / outputs

| Entry point | Input | Output |
|---|---|---|
| `extract_with_tables(pdf_path)` | A PDF path | `(markdown, tables_count, total_text_chars)` |
| `ocr_pdf(pdf_path, dpi=300, lang="eng")` | A PDF path and OCR settings | Markdown text with page markers |
| CLI `python app/brain/ingestion/pdf_to_md_v3.py file.pdf --output-dir out` | One or more PDF paths | `<name>.md` plus `<name>.json` metadata |

The Markdown output uses `--- PAGE N ---` markers that the page splitter and
lecture ingestion expect.

## Data flow

1. `main()` parses CLI arguments and loops through PDF paths.
2. `extract_with_tables(...)` opens each PDF with `pdfplumber`.
3. Each page emits a page marker, any detected tables as Markdown tables, then
   normalized page text outside those tables.
4. If native text is too sparse, the CLI falls back to `ocr_pdf(...)`.
5. `write_markdown(...)` writes the extracted Markdown; `write_metadata(...)`
   writes extraction metadata beside it.

## Connected code and tools

- `app/class_/lecture_ingest/lecture_ingest.py` imports
  `extract_with_tables(...)` for lecture upload processing.
- `app/brain/ingestion/page_splitter` consumes the page markers.
- External tools/libraries: `pdfplumber`, `pdf2image`, `pytesseract`, and the
  system `poppler`/`tesseract` utilities.

## Code walkthrough

### Shebang, docstring, and imports

The script is both importable and executable from the command line. Imports are
limited to argument parsing, paths, regular expressions, and PDF/OCR libraries.

### `sanitize_filename(...)`

Replaces unsafe filename characters before writing Markdown and metadata files,
falling back to `output` when the source name has no usable characters.

### `ocr_pdf(...)`

Rasterizes PDF pages at the requested DPI and runs Tesseract OCR. Each OCR page
gets the same page marker format as native extraction so downstream splitting
stays consistent.

### `_looks_like_heading_caps(...)` and `_normalize_page_text(...)`

These helpers clean native text. They collapse excess blank lines, merge very
short wrapped lines into surrounding text, and promote conservative all-caps
headings to Markdown headings.

### `_escape_cell(...)` and `_table_to_markdown(...)`

These helpers turn extracted table rows into Markdown tables while escaping pipe
characters and preserving line breaks inside cells.

### `extract_with_tables(...)`

This is the main importable path. It walks pages, collects tables and table
bounding boxes, extracts non-table text, normalizes text lines, and returns the
final Markdown plus simple extraction counts.

### `write_markdown(...)`, `build_output_paths(...)`, and `write_metadata(...)`

These file helpers create the output directory, choose the Markdown/metadata
paths, and write UTF-8 text/JSON.

### `main()`

The CLI validates PDF paths, selects native extraction or OCR, writes outputs,
and prints progress messages. It does not touch Surf's database or API key.

## Testing notes

Focused ingestion tests live with the lecture-ingest tests because this extractor
feeds that pipeline. For a focused ingestion check, run:

```bash
ruff check app/brain/ingestion --no-cache
```

## What could break if changed

- Changing page marker format breaks `page_splitter` and lecture source-page
  mapping.
- Removing sparse-text detection can send empty lecture content into generation.
- Writing output files outside the requested directory can leak uploaded PDFs or
  Markdown into the wrong location.
- Adding Anthropic or SQLite work here would mix local extraction with app
  generation/persistence boundaries.
