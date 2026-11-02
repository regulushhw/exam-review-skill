# -*- coding: utf-8 -*-
"""Shared helpers: ASCII on the console, UTF-8 on disk.

Windows consoles often cannot print Chinese or emoji. Scripts write those
details to UTF-8 files and keep stdout/stderr ASCII.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def console(message: str) -> None:
    """Print one ASCII line. Non-ASCII characters become '?'."""
    text = message.encode("ascii", errors="replace").decode("ascii")
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read_json(path: Path) -> object:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        console("error=read_failed")
        console_path("path", path)
        raise SystemExit(2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        console("error=invalid_json")
        console_path("path", path)
        raise SystemExit(2)


def console_path(label: str, path: Path) -> None:
    shown = str(path)
    if shown.isascii():
        console(label + "=" + shown)
    else:
        console(label + "=non_ascii")


def safe_stem(stem: str) -> str:
    """File-name stem that Windows can store. Keeps non-ASCII letters."""
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update("COM" + str(i) for i in range(1, 10))
    reserved.update("LPT" + str(i) for i in range(1, 10))
    chars: list[str] = []
    for ch in stem.strip():
        if ch in '<>:"/\\|?*' or ord(ch) < 32:
            chars.append("_")
        else:
            chars.append(ch)
    name = "".join(chars).strip(" .")
    if not name:
        name = "pdf"
    if name.upper() in reserved:
        name = name + "_pdf"
    return name


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_inside_skill(path: Path) -> bool:
    resolved = path.resolve()
    root = skill_root()
    try:
        resolved.relative_to(root)
    except ValueError:
        return False
    return True
