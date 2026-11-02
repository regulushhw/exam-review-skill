# -*- coding: utf-8 -*-
"""Extract PDF text with pdfplumber and flag weak extracts.

Character count is len(text.strip()) of the whole file. Below 500 characters
the file is flagged below_500 and likely_image_pdf (switch to visual
analysis). The decision tree's other mark, 2000 characters per chapter, is
recorded on the report for the agent to apply; this script does not invent a
third cutoff.

Writes UTF-8 text plus extracted/quality_report.json. Console output is ASCII.

    python extract_and_check.py lecture.pdf notes.pdf --out extracted
    python extract_and_check.py slides_dir --out extracted
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import console, console_path, safe_stem, write_json, write_text

LOW_CHARS = 500
USABLE_CHARS_PER_CHAPTER = 2000


def collect_pdfs(inputs: list[str]) -> list[Path]:
    found: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            found.extend(sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"))
        elif path.is_file():
            found.append(path)
        else:
            console("error=file_not_found")
            console_path("path", path)
            raise SystemExit(2)
    return found


def text_name(stem: str, used: set[str]) -> str:
    base = safe_stem(stem)
    name = base + ".txt"
    n = 2
    while name in used:
        name = base + "_" + str(n) + ".txt"
        n += 1
    used.add(name)
    return name


def extract_one(pdf_path: Path, out_dir: Path, used: set[str]) -> dict:
    import pdfplumber

    page_texts: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")
    full = "\n\n".join(page_texts)
    char_count = len(full.strip())
    page_char_counts = [len(part.strip()) for part in page_texts]
    below = char_count < LOW_CHARS
    filename = text_name(pdf_path.stem, used)
    text_path = out_dir / filename
    write_text(text_path, full)
    if below:
        note = "不足 500 字，按决策树视为图片型 PDF，改用视觉分析。"
    else:
        note = "已达到或超过 500 字。每章是否够用，仍按不少于 2000 字判断。"
    return {
        "source": str(pdf_path),
        "pages": len(page_texts),
        "char_count": char_count,
        "page_char_counts": page_char_counts,
        "below_500": below,
        "likely_image_pdf": below,
        "text_file": str(text_path),
        "note": note,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract PDF text with pdfplumber and flag extracts under 500 characters."
    )
    parser.add_argument("inputs", nargs="+", help="PDF files or a directory of PDF files")
    parser.add_argument("--out", default="extracted", help="Output directory (default: extracted)")
    args = parser.parse_args(argv)

    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        console("error=missing_package package=pdfplumber")
        return 2

    pdfs = collect_pdfs(args.inputs)
    if not pdfs:
        console("error=no_input")
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    files: list[dict] = []
    failed = 0
    for pdf_path in pdfs:
        try:
            files.append(extract_one(pdf_path, out_dir, used))
        except Exception as exc:
            failed += 1
            entry = {
                "source": str(pdf_path),
                "pages": 0,
                "char_count": 0,
                "page_char_counts": [],
                "below_500": True,
                "likely_image_pdf": True,
                "error": "open_failed",
                "note": "文件打不开，不能当成已提取的正文。",
            }
            detail = str(exc)
            if detail.isascii():
                entry["error_detail"] = detail[:300]
            files.append(entry)

    report = {
        "threshold_low_chars": LOW_CHARS,
        "usable_chars_per_chapter": USABLE_CHARS_PER_CHAPTER,
        "files": files,
    }
    report_path = out_dir / "quality_report.json"
    write_json(report_path, report)
    flagged = sum(1 for item in files if item.get("likely_image_pdf"))
    console("files=" + str(len(files)))
    console("flagged=" + str(flagged))
    console("failed=" + str(failed))
    console_path("report", report_path)
    return 2 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        console("error=unexpected")
        detail = str(exc)
        if detail.isascii():
            console("detail=" + detail.replace("\n", " ")[:200])
        sys.exit(1)
