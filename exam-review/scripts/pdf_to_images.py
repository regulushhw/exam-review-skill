# -*- coding: utf-8 -*-
"""Render PDF pages to PNG with PyMuPDF.

Default is 150 dpi. Each PDF is written to its own folder:

    pdf_images/<stem>/page_001.png

A UTF-8 manifest.json in the output root lists every file. Console output
stays ASCII. Do not rewrite this script per course; call it.

    python pdf_to_images.py lecture.pdf --out pdf_images
    python pdf_to_images.py slides_dir --out pdf_images --dpi 150
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import console, console_path, safe_stem, write_json


def load_fitz():
    """PyMuPDF. Package name is pymupdf; older installs also expose fitz."""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            return None
    return fitz


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


def folder_name(stem: str, used: set[str]) -> str:
    base = safe_stem(stem)
    name = base
    n = 2
    while name in used:
        name = base + "_" + str(n)
        n += 1
    used.add(name)
    return name


def render_pdf(pdf_path: Path, out_root: Path, dpi: int, used: set[str]) -> dict:
    fitz = load_fitz()
    dest = out_root / folder_name(pdf_path.stem, used)
    dest.mkdir(parents=True, exist_ok=True)
    pages: list[dict] = []
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            filename = "page_{:03d}.png".format(i + 1)
            pix.save(str(dest / filename))
            pages.append(
                {
                    "file": filename,
                    "width_px": pix.width,
                    "height_px": pix.height,
                }
            )
    finally:
        doc.close()
    return {
        "source": str(pdf_path),
        "output_dir": str(dest),
        "pages": pages,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render PDF pages to PNG folders with PyMuPDF (default 150 dpi)."
    )
    parser.add_argument("inputs", nargs="+", help="PDF files or a directory of PDF files")
    parser.add_argument(
        "--out",
        default="pdf_images",
        help="Output root. One subfolder per PDF (default: pdf_images)",
    )
    parser.add_argument("--dpi", type=int, default=150, help="Raster DPI (default: 150)")
    args = parser.parse_args(argv)

    if args.dpi <= 0:
        console("error=bad_dpi")
        return 2

    if load_fitz() is None:
        console("error=missing_package package=pymupdf")
        return 2

    pdfs = collect_pdfs(args.inputs)
    if not pdfs:
        console("error=no_input")
        return 2

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    files: list[dict] = []
    failed = 0
    for pdf_path in pdfs:
        try:
            files.append(render_pdf(pdf_path, out_root, args.dpi, used))
        except Exception as exc:
            failed += 1
            entry = {"source": str(pdf_path), "error": "open_failed", "pages": []}
            detail = str(exc)
            if detail.isascii():
                entry["error_detail"] = detail[:300]
            files.append(entry)

    report = {"dpi": args.dpi, "files": files}
    report_path = out_root / "manifest.json"
    write_json(report_path, report)
    page_count = sum(len(item.get("pages") or []) for item in files)
    console("files=" + str(len(files)))
    console("pages=" + str(page_count))
    console("dpi=" + str(args.dpi))
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
