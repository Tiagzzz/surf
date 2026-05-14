#!/usr/bin/env python3
"""PDF -> Markdown converter (v3).

Adds pdfplumber-based table detection on top of v2's gentler heading heuristics.
"""
# --------------------------------------------------------------------------- #
# IMPORTS
# --------------------------------------------------------------------------- #
# Simple explanation:
# This script reads a PDF file and writes out a clean Markdown file plus a
# small JSON metadata file. It supports both native text extraction (fast,
# accurate for digital PDFs) and OCR fallback (slow, used when the PDF is
# actually scanned images).
#
# Important code pieces:
# - `argparse`: parses command-line flags when this file is run as a CLI.
# - `pathlib.Path`: file/folder paths with helpful methods like `.stem`
#   (filename without extension) and `.write_text`.
# - `pdfplumber`: third-party library for extracting text and tables from
#   "real" digital PDFs without rasterizing first.
# - `pytesseract`: Python wrapper around the Tesseract OCR engine, used
#   when native text extraction yields almost nothing.
# - `pdf2image.convert_from_path`: turns each PDF page into a PIL image
#   so Tesseract can OCR it.
import argparse
import re
from pathlib import Path

import pdfplumber
import pytesseract
from pdf2image import convert_from_path


# --------------------------------------------------------------------------- #
# SANITIZE_FILENAME — KEEP OUTPUT NAMES SAFE FOR THE FILESYSTEM
# --------------------------------------------------------------------------- #
# Simple explanation:
# Replaces anything that is not a letter, number, underscore, hyphen,
# dot, or space with an underscore so the output file name is always
# safe to write to disk.
def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\-\. ]+", "_", name).strip()
    return cleaned or "output"


# --------------------------------------------------------------------------- #
# OCR_PDF — FALLBACK PATH FOR SCANNED OR IMAGE-ONLY PDFs
# --------------------------------------------------------------------------- #
# Simple explanation:
# When a PDF is just scanned images (no embedded text layer), native
# extraction returns almost nothing. This function rasterizes each page
# at the chosen DPI and asks Tesseract to read characters out of the
# pixels, then stitches the per-page text together with the same
# `--- PAGE N ---` markers the native path uses.
#
# Key detail:
# - `convert_from_path(...)`: returns a list of PIL Images, one per page.
# - `pytesseract.image_to_string(...)`: runs OCR on one image.
def ocr_pdf(pdf_path: Path, dpi: int = 300, lang: str = "eng") -> str:
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    text_chunks = []
    for page_number, page_image in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(page_image, lang=lang)
        header = f"\n\n--- PAGE {page_number} ---\n\n"
        text_chunks.append(header + page_text)
    return "\n".join(text_chunks).strip()


# --------------------------------------------------------------------------- #
# TEXT-NORMALIZATION HELPERS — HEADINGS, LINE MERGING, CELL ESCAPING
# --------------------------------------------------------------------------- #
# Simple explanation:
# Helpers used by the native extraction path to make the raw text look
# more like clean Markdown. They guess which lines are headings (all-caps
# multi-word lines), merge short broken lines back into paragraphs, and
# escape characters that would otherwise break Markdown tables.
#
# Important code pieces:
# - `_looks_like_heading_caps`: heuristic — short all-caps phrases of 3-10
#   words look like slide titles and become `## Heading` lines.
# - `_normalize_page_text`: rebuilds paragraphs and tags headings.
# - `_escape_cell`: replaces `|` with `\|` and newlines with `<br>` so a
#   cell never breaks the surrounding pipe-style markdown table.
# - `_table_to_markdown`: converts a list-of-lists table into a Markdown
#   table with a header row and separator row.
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


# --------------------------------------------------------------------------- #
# EXTRACT_WITH_TABLES — NATIVE PDF EXTRACTION WITH TABLE DETECTION
# --------------------------------------------------------------------------- #
# Simple explanation:
# The main entry point used by Surf's lecture-ingest pipeline. It opens
# the PDF with pdfplumber, finds tables on each page (rendering them as
# Markdown tables), and then extracts the remaining body text outside
# those table bounding boxes. Each page is prefixed with the standard
# `--- PAGE N ---` marker so the downstream page splitter can chop the
# output up again.
#
# Important code pieces:
# - `pdfplumber.open(...) as pdf`: opens the PDF and guarantees it is
#   closed afterwards (the `with` block).
# - `page.find_tables()`: best-effort table detection from line/grid hints.
# - `page.filter(_outside_tables)`: produces a "virtual page" containing
#   only the objects that sit outside the table boxes, so table text is
#   not duplicated in the body.
# - Returns a 3-tuple `(markdown_text, tables_count, total_text_chars)` so
#   the caller can decide whether the result looks sparse enough to need
#   an OCR fallback.
def extract_with_tables(pdf_path: Path) -> tuple[str, int, int]:
    out_lines: list[str] = []
    tables_count = 0
    total_text_chars = 0

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            if out_lines:
                out_lines.append("")
            out_lines.append(f"--- PAGE {page_index} ---")
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


# --------------------------------------------------------------------------- #
# OUTPUT HELPERS — WRITE MARKDOWN, METADATA, AND COMPUTE OUTPUT PATHS
# --------------------------------------------------------------------------- #
# Simple explanation:
# Three small file helpers used by the CLI: write the Markdown body,
# decide where the `.md` and `.json` outputs should go, and write the
# JSON metadata sidecar that records how the conversion happened.
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


# --------------------------------------------------------------------------- #
# MAIN — CLI ENTRY POINT
# --------------------------------------------------------------------------- #
# Simple explanation:
# When this file is run directly (`python pdf_to_md_v3.py file.pdf ...`),
# `main()` parses the command-line flags, processes each PDF, and decides
# whether to use the native extractor or the OCR fallback. If native
# extraction returns less than ~150 characters of text the script
# automatically retries with OCR.
#
# Important code pieces:
# - `argparse.ArgumentParser(...)`: declares the CLI flags and produces
#   `--help` output for the user.
# - `if __name__ == "__main__": main()`: Python idiom that runs `main()`
#   only when this file is executed directly, not when it is imported.
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown (v3 — pdfplumber table detection)."
    )
    parser.add_argument("pdf_paths", nargs="+", help="PDF file(s) to convert")
    parser.add_argument(
        "--output-dir",
        default="output_md",
        help="Directory to store generated Markdown files",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Force OCR for all pages, even when text extraction succeeds",
    )
    parser.add_argument(
        "--lang",
        default="eng",
        help="Tesseract OCR language code(s), e.g. eng or eng+fra",
    )
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
