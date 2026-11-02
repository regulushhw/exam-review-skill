# -*- coding: utf-8 -*-
"""Remove temporary extraction directories.

By default, deletes <root>/extracted and <root>/pdf_images when they exist.
Pass --extra for a throwaway script or another temp path. Markdown notes are
left alone. Paths inside this skill directory are refused.

Console output is ASCII.

    python cleanup.py --root .
    python cleanup.py --root . --extra tmp_build.py --dry-run
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from common import console, console_path, is_inside_skill

DEFAULT_NAMES = ("extracted", "pdf_images")


def gather_targets(root: Path, extra: list[str]) -> list[Path]:
    targets = [root / name for name in DEFAULT_NAMES]
    for raw in extra:
        targets.append(Path(raw) if Path(raw).is_absolute() else root / raw)
    return targets


def allowed(root: Path, target: Path) -> bool:
    if is_inside_skill(target):
        return False
    resolved_root = root.resolve()
    resolved = target.resolve()
    if resolved == resolved_root:
        return False
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        return False
    return True


def remove_path(target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete extracted/ and pdf_images/ under --root, plus optional --extra paths."
    )
    parser.add_argument("--root", default=".", help="Workspace root (default: current directory)")
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        help="Extra file or directory to remove, relative to --root unless absolute",
    )
    parser.add_argument("--dry-run", action="store_true", help="List counts without deleting")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        console("error=root_not_found")
        console_path("path", root)
        return 2

    removed = 0
    missing = 0
    refused = 0
    would = 0
    for target in gather_targets(root, args.extra):
        if not target.exists():
            missing += 1
            continue
        if not allowed(root, target):
            refused += 1
            console("error=refused")
            console_path("path", target)
            continue
        would += 1
        if args.dry_run:
            continue
        remove_path(target)
        removed += 1

    console("dry_run=" + ("1" if args.dry_run else "0"))
    console("removed=" + str(removed))
    console("would_remove=" + str(would if args.dry_run else removed))
    console("missing=" + str(missing))
    console("refused=" + str(refused))
    return 2 if refused else 0


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
