---
title: "pdf_to_md_v3.py — PDF → Markdown extractor"
tags:
  - surf/script
  - surf/brain
  - surf/ingestion
status: docs
bucket: app/brain/ingestion
---

# `pdf_to_md_v3.py`

> Wikilinks: output is consumed by [[factsheet_cleaner]] for the factsheet pipeline. Will also be consumed by the future `lecture_ingest` pipeline.

## What it does

Converts a PDF file (factsheet, lecture deck, etc.) into a Markdown file. Uses **pdfplumber** for native text + table extraction, with **OCR fallback** (Tesseract via `pdf2image`) for scanned PDFs where text extraction yields empty pages.

**Analogy**: like a translator who reads the PDF page-by-page and types it back out as Markdown — keeping page numbers as section headers and detecting tables when present.

This is the **first stage of the factsheet pipeline**: `PDF → [pdf_to_md_v3] → MD → [factsheet_cleaner] → JSON → [factsheet_renderer] → student-facing MD`.

## How to call it

CLI:

```bash
python3 pdf_to_md_v3.py "path/to/file.pdf" --output-dir /tmp/out
```

Multiple PDFs:

```bash
python3 pdf_to_md_v3.py file1.pdf file2.pdf --output-dir /tmp/out
```

Force OCR (e.g. when a PDF has selectable but garbage text):

```bash
python3 pdf_to_md_v3.py file.pdf --output-dir /tmp/out --ocr --lang eng+deu
```

Imported from another Python script: not currently exposed as a clean library — call via `subprocess.run([...])` for now (see TODO).

## Dependencies

- **Python ≥ 3.9**
- **`pdfplumber`** — `pip install pdfplumber`
- **`pdf2image`** + system **`poppler`** — `brew install poppler`, `pip install pdf2image`
- **`pytesseract`** + system **`tesseract`** — `brew install tesseract`, `pip install pytesseract`

No Surf-internal dependencies.

## Inputs

| Argument | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `pdf_paths` (positional) | one or more paths | yes | — | PDF files to convert |
| `--output-dir` | path | no | parent dir of each input PDF | Where the `.md` (and metadata `.json`) files are written |
| `--ocr` | flag | no | off | Force OCR even when native extraction succeeds |
| `--lang` | string | no | `eng` | Tesseract language code(s), e.g. `eng+deu` |
| `--dpi` | int | no | `300` | Image DPI for OCR conversion |

## Outputs

For each input `<name>.pdf`, two files are written into `--output-dir`:

- **`<name>.md`** — the Markdown text. Page boundaries become `# Page N` headings.
- **`<name>.json`** — small metadata file (extraction method used, table counts).

## Still to do

- [ ] **Library API**: currently CLI-only. The factsheet-clean pipeline currently invokes via `subprocess.run`; cleaner would be a `convert_pdf_to_md(pdf_path: Path) -> str` function that returns the markdown directly. Refactor when wiring the Streamlit app.
- [ ] **Concatenated-word reconstruction**: pdfplumber sometimes drops spaces between adjacent text runs (e.g. `"ProbabilityTheoryandStatistics"`). The downstream factsheet cleaner currently fixes these via Claude. A pre-pass that re-inserts spaces using a dictionary check would reduce cleaner load and cost — open question whether it's worth the complexity.
- [ ] **Table fidelity**: pdfplumber's table detection works for clean tables but misses borderless / multi-column layouts (e.g. the "Attached courses" block in HSG factsheets is detected as zero tables). Acceptable for the factsheet use case (cleaner discards this section anyway), may need work for lecture decks.

---

## Code, section by section

> The full script is ~190 lines. The walkthrough below covers the load-bearing sections only; the OCR and CLI plumbing are standard.

### Imports

```python
import argparse
import re
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
import pytesseract
```

Standard library + the three external libraries described under Dependencies.

### Filename sanitisation

```python
def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\-\. ]+", "_", name).strip()
    return cleaned or "output"
```

Replaces unsafe filesystem characters before writing output. Falls back to `"output"` if the cleaned name is empty.

### Native text extraction (the happy path)

The main extraction loop iterates over pages with pdfplumber, extracts text + tables per page, and merges them into a single Markdown string with `# Page N` headers. Tables that pdfplumber detects are rendered as Markdown tables; everything else flows as paragraph text.

### OCR fallback

```python
def ocr_pdf(pdf_path: Path, dpi: int = 300, lang: str = "eng") -> str:
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    text_chunks = []
    for page_number, page_image in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(page_image, lang=lang)
        header = f"\n\n# Page {page_number}\n\n"
        text_chunks.append(header + page_text)
    return "\n".join(text_chunks).strip()
```

When the native pdfplumber extraction returns an empty page (typical for scanned-image PDFs), this fallback rasterises the page at 300 DPI and runs Tesseract OCR. The `--ocr` flag forces this path for every page even when native extraction succeeds — useful when native text exists but is garbled.

### Heading detection heuristics

```python
def _looks_like_heading_caps(line: str) -> bool:
    if not line.isupper():
        return False
    words = line.split()
    return len(words) >= 3 and len(line) >= 12 and len(words) <= 10
```

Conservative heuristic: only treat a line as a heading if it's ALL CAPS, between 3 and 10 words, and at least 12 characters. Avoids false-positive promotion of short shouted phrases like `"OK"` or `"NOTE"` to headings.

### Line-merge buffer

The extractor sometimes splits a single sentence across multiple pdfplumber lines (visual line wrap, not semantic). A small buffer accumulates short lines (≤2 words) and joins them with the next non-short line, so paragraphs come out as continuous text instead of fragmented bullets. Imperfect — this is where most of the factsheet artifacts originate (concatenated-word issue noted in the TODO above).

### CLI plumbing

```python
parser = argparse.ArgumentParser(...)
parser.add_argument("pdf_paths", nargs="+", ...)
parser.add_argument("--output-dir", ...)
parser.add_argument("--ocr", action="store_true", ...)
parser.add_argument("--lang", default="eng", ...)
parser.add_argument("--dpi", type=int, default=300, ...)
```

Standard argparse setup. Multiple PDFs in a single invocation share the same output directory; each gets its own `.md` + `.json` pair.

---

## Full code

```python
#!/usr/bin/env python3
"""PDF -> Markdown converter (v3). Adds pdfplumber-based table detection on top of v2's gentler heading heuristics."""
import argparse
import re
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
import pytesseract


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\-\. ]+", "_", name).strip()
    return cleaned or "output"


def ocr_pdf(pdf_path: Path, dpi: int = 300, lang: str = "eng") -> str:
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    text_chunks = []
    for page_number, page_image in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(page_image, lang=lang)
        header = f"\n\n# Page {page_number}\n\n"
        text_chunks.append(header + page_text)
    return "\n".join(text_chunks).strip()


def _looks_like_heading_caps(line: str) -> bool:
    if not line.isupper():
        return False
    words = line.split()
    return len(words) >= 3 and len(line) >= 12 and len(words) <= 10


def _normalize_page_text(page_text: str) -> list[str]:
    page_text = re.sub(r"\n{3,}", "\n\n", page_text)
    raw_lines = [ln.strip() for ln in page_text.split("\n")]

    merged: list[str] = []
    buffer: list[str] = []

    def flush_buffer():
        if buffer:
            merged.append(" ".join(buffer))
            buffer.clear()

    for ln in raw_lines:
        if not ln:
            flush_buffer()
            merged.append("")
            continue
        words = ln.split()
        if len(words) <= 2 and not _looks_like_heading_caps(ln):
            buffer.append(ln)
        else:
            flush_buffer()
            merged.append(ln)
    flush_buffer()

    out: list[str] = []
    for ln in merged:
        if not ln:
            out.append("")
            continue
        if _looks_like_heading_caps(ln):
            out.append(f"## {ln}")
        else:
            out.append(ln)
    return out


def _escape_cell(cell: str | None) -> str:
    if cell is None:
        return ""
    text = str(cell).replace("|", "\\|").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "<br>")
    return text.strip()


def _table_to_markdown(table: list[list[str | None]]) -> str:
    rows = [r for r in table if r is not None and any((c or "").strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [list(r) + [""] * (width - len(r)) for r in rows]
    header = [_escape_cell(c) or " " for c in rows[0]]
    sep = ["---"] * width
    body = [[_escape_cell(c) for c in r] for r in rows[1:]]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def extract_with_tables(pdf_path: Path) -> tuple[str, int, int]:
    out_lines: list[str] = []
    tables_count = 0
    total_text_chars = 0

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            if out_lines:
                out_lines.append("")
            out_lines.append(f"# Page {page_index}")
            out_lines.append("")

            found_tables = page.find_tables() or []
            table_md_blocks: list[str] = []
            table_bboxes: list[tuple[float, float, float, float]] = []
            for t in found_tables:
                data = t.extract()
                md = _table_to_markdown(data)
                if not md:
                    continue
                table_md_blocks.append(md)
                table_bboxes.append(t.bbox)
                tables_count += 1

            for md in table_md_blocks:
                out_lines.append(md)
                out_lines.append("")

            def _outside_tables(obj):
                x0, top, x1, bottom = obj["x0"], obj["top"], obj["x1"], obj["bottom"]
                cx = (x0 + x1) / 2
                cy = (top + bottom) / 2
                for bx0, btop, bx1, bbottom in table_bboxes:
                    if bx0 <= cx <= bx1 and btop <= cy <= bbottom:
                        return False
                return True

            if table_bboxes:
                filtered = page.filter(_outside_tables)
                page_text = filtered.extract_text() or ""
            else:
                page_text = page.extract_text() or ""

            total_text_chars += len(page_text)
            for ln in _normalize_page_text(page_text):
                out_lines.append(ln)

    cleaned = "\n".join(out_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip(), tables_count, total_text_chars


def write_markdown(output_path: Path, content: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def build_output_paths(pdf_path: Path, output_dir: Path) -> tuple[Path, Path]:
    base_name = sanitize_filename(pdf_path.stem)
    md_path = output_dir / f"{base_name}.md"
    json_path = output_dir / f"{base_name}.json"
    return md_path, json_path


def write_metadata(output_path: Path, meta: dict) -> None:
    import json
    output_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown (v3 — pdfplumber table detection)."
    )
    parser.add_argument("pdf_paths", nargs="+", help="PDF file(s) to convert")
    parser.add_argument("--output-dir", default="output_md", help="Directory to store generated Markdown files")
    parser.add_argument("--ocr", action="store_true", help="Force OCR for all pages, even when text extraction succeeds")
    parser.add_argument("--lang", default="eng", help="Tesseract OCR language code(s), e.g. eng or eng+fra")
    parser.add_argument("--dpi", type=int, default=300, help="Image DPI for OCR conversion")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in args.pdf_paths:
        pdf_path = Path(pdf_file)
        if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
            print(f"Skipping invalid PDF path: {pdf_path}")
            continue

        print(f"Processing {pdf_path}")
        tables_count = 0
        if args.ocr:
            print("  -> Using OCR extraction (forced)")
            markdown = ocr_pdf(pdf_path, dpi=args.dpi, lang=args.lang)
            use_ocr = True
        else:
            markdown, tables_count, text_chars = extract_with_tables(pdf_path)
            if text_chars < 150:
                print("  -> Native extraction too sparse, falling back to OCR")
                markdown = ocr_pdf(pdf_path, dpi=args.dpi, lang=args.lang)
                use_ocr = True
                tables_count = 0
            else:
                print(f"  -> Using native text extraction (tables found: {tables_count})")
                use_ocr = False

        md_path, json_path = build_output_paths(pdf_path, output_dir)
        write_markdown(md_path, markdown)

        metadata = {
            "source_pdf": str(pdf_path.resolve()),
            "output_markdown": str(md_path.resolve()),
            "output_metadata": str(json_path.resolve()),
            "used_ocr": use_ocr,
            "language": args.lang,
            "dpi": args.dpi,
            "script_version": "v3",
            "tables_extracted": tables_count,
        }
        write_metadata(json_path, metadata)
        print(f"  -> Saved {md_path} and metadata {json_path}")


if __name__ == "__main__":
    main()
```
