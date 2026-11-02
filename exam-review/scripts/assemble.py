# -*- coding: utf-8 -*-
"""Fill assets/template.html from content JSON and practice_chN.json.

LaTeX stays in JSON. This file never writes a formula as a Python literal, and
it does not build formula strings with f-strings. HTML is escaped; backslashes
from JSON are copied through unchanged.

    python assemble.py --content content.json --out review.html
    python assemble.py --content content.json --out ch1.html --only ch1
    python assemble.py --patch review.html --chapter ch1 --practice practice_ch1.json

--patch replaces one <div class="practice-box"> using the nested-div depth
counter. The rest of the file is left as it was.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from common import console, console_path, read_json, skill_root, write_text

PRACTICE_OPEN = '<div class="practice-box">'
CHAPTER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
STAR = "\u2b50"


def default_template() -> Path:
    return skill_root() / "assets" / "template.html"


def matching_div_end(source: str, open_pos: int) -> int:
    """End index (exclusive) of the div that starts at open_pos.

    Same nested-depth counter as references/architecture.md.
    """
    depth = 0
    pos = open_pos
    end = -1
    while pos < len(source):
        if source[pos : pos + 4] == "<div":
            depth += 1
        elif source[pos : pos + 6] == "</div>":
            depth -= 1
            if depth == 0:
                end = pos + 6
                break
        pos += 1
    if end < 0:
        raise ValueError("unbalanced practice-box")
    return end


def find_practice_span(source: str, chapter_id: str) -> tuple[int, int]:
    marker = 'id="' + chapter_id + '"'
    chapter_at = source.find(marker)
    if chapter_at < 0:
        raise ValueError("chapter id not in html")
    next_chapter = source.find('<section class="chapter"', chapter_at + len(marker))
    region_end = next_chapter if next_chapter >= 0 else len(source)
    open_pos = source.find(PRACTICE_OPEN, chapter_at, region_end)
    if open_pos < 0:
        raise ValueError("practice-box not found")
    return open_pos, matching_div_end(source, open_pos)


def require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        console("error=bad_content field=" + field)
        raise SystemExit(2)
    return value


def as_list(value: object, field: str) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        console("error=bad_content field=" + field)
        raise SystemExit(2)
    return value


def load_practice(raw: object, field: str) -> list[dict]:
    items = as_list(raw, field)
    questions: list[dict] = []
    for index, item in enumerate(items):
        item_field = field + "[" + str(index) + "]"
        if not isinstance(item, dict):
            console("error=bad_content field=" + item_field)
            raise SystemExit(2)
        question = require_str(item.get("q"), item_field + ".q")
        answer = require_str(item.get("a"), item_field + ".a")
        entry = {"q": question, "a": answer}
        if "difficulty" in item and item["difficulty"] is not None:
            difficulty = item["difficulty"]
            if not isinstance(difficulty, int) or isinstance(difficulty, bool):
                console("error=bad_content field=" + item_field + ".difficulty")
                raise SystemExit(2)
            entry["difficulty"] = difficulty
        questions.append(entry)
    return questions


def practice_for_chapter(chapter: dict, content_dir: Path, field: str) -> list[dict]:
    if chapter.get("practice_file"):
        rel = require_str(chapter["practice_file"], field + ".practice_file")
        path = Path(rel)
        if not path.is_absolute():
            path = content_dir / path
        data = read_json(path)
        return load_practice(data, field + ".practice_file")
    if "practice" in chapter and chapter["practice"] is not None:
        return load_practice(chapter["practice"], field + ".practice")
    return []


def paragraphs(text: str) -> str:
    blocks = text.split("\n\n")
    parts: list[str] = []
    for block in blocks:
        escaped = html.escape(block, quote=False).replace("\n", "<br>\n")
        parts.append("<p>" + escaped + "</p>")
    return "".join(parts)


def difficulty_html(value: object) -> str:
    if not isinstance(value, int) or isinstance(value, bool):
        return ""
    if value < 1 or value > 4:
        return ""
    return '<p class="difficulty">' + (STAR * value) + "</p>"


def answer_block(inner_html: str) -> str:
    return (
        '<div class="answer-btn-wrap">'
        '<button type="button" '
        'onclick="this.parentElement.nextElementSibling.style.display='
        "this.parentElement.nextElementSibling.style.display==='block'?'none':'block'\">"
        "显示 / 隐藏</button></div>\n"
        '<div class="answer" style="display:none">' + inner_html + "</div>"
    )


def practice_box(questions: list[dict]) -> str:
    parts = [PRACTICE_OPEN]
    for item in questions:
        parts.append('<div class="question">')
        parts.append(paragraphs(item["q"]))
        parts.append(difficulty_html(item.get("difficulty")))
        parts.append(answer_block(paragraphs(item["a"])))
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts)


def formula_table(formulas: list[dict], field: str) -> str:
    if not formulas:
        return ""
    parts = [
        '<table class="formula-table"><thead><tr>',
        "<th>名称</th><th>公式</th><th>说明</th>",
        "</tr></thead><tbody>",
    ]
    for index, item in enumerate(formulas):
        item_field = field + "[" + str(index) + "]"
        if not isinstance(item, dict):
            console("error=bad_content field=" + item_field)
            raise SystemExit(2)
        name = html.escape(require_str(item.get("name", ""), item_field + ".name"), quote=False)
        expr = html.escape(require_str(item.get("expr", ""), item_field + ".expr"), quote=False)
        note = html.escape(require_str(item.get("note", ""), item_field + ".note"), quote=False)
        parts.append("<tr><td>" + name + "</td><td><pre class=\"codebox\">" + expr + "</pre></td><td>" + note + "</td></tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def knowledge_html(items: list, field: str) -> str:
    if not items:
        return ""
    parts = ['<section class="knowledge">']
    for index, item in enumerate(items):
        item_field = field + "[" + str(index) + "]"
        if not isinstance(item, dict):
            console("error=bad_content field=" + item_field)
            raise SystemExit(2)
        heading = require_str(item.get("heading", ""), item_field + ".heading")
        body = require_str(item.get("body", ""), item_field + ".body")
        if heading:
            parts.append("<h3>" + html.escape(heading, quote=False) + "</h3>")
        parts.append(paragraphs(body))
    parts.append("</section>")
    return "\n".join(parts)


def traps_html(items: list, field: str) -> str:
    if not items:
        return ""
    parts = ['<div class="trap"><p class="trap-label">陷阱警告</p><ul>']
    for index, item in enumerate(items):
        text = require_str(item, field + "[" + str(index) + "]")
        parts.append("<li>" + html.escape(text, quote=False) + "</li>")
    parts.append("</ul></div>")
    return "\n".join(parts)


def past_papers_html(items: list, field: str) -> str:
    if not items:
        return ""
    parts = ['<section class="past-papers"><h3>真题还原</h3>']
    for index, item in enumerate(items):
        item_field = field + "[" + str(index) + "]"
        if not isinstance(item, dict):
            console("error=bad_content field=" + item_field)
            raise SystemExit(2)
        question = require_str(item.get("q", ""), item_field + ".q")
        answer = require_str(item.get("a", ""), item_field + ".a")
        analysis = require_str(item.get("analysis", ""), item_field + ".analysis")
        parts.append('<div class="past-paper">')
        parts.append(paragraphs(question))
        hidden = paragraphs("答案：" + answer)
        if analysis:
            hidden += paragraphs("解析：" + analysis)
        parts.append(answer_block(hidden))
        parts.append("</div>")
    parts.append("</section>")
    return "\n".join(parts)


def chapter_controls() -> str:
    show = (
        "var root=this.parentElement.parentElement;"
        "root.querySelectorAll('.answer').forEach(function(node){node.style.display='block';});"
    )
    hide = (
        "var root=this.parentElement.parentElement;"
        "root.querySelectorAll('.answer').forEach(function(node){node.style.display='none';});"
    )
    return (
        '<div class="chapter-controls">'
        '<button type="button" onclick="' + show + '">显示全部</button>'
        '<button type="button" onclick="' + hide + '">隐藏全部</button>'
        "</div>"
    )


def chapter_html(chapter: dict, content_dir: Path, field: str) -> tuple[str, int]:
    if not isinstance(chapter, dict):
        console("error=bad_content field=" + field)
        raise SystemExit(2)
    chapter_id = require_str(chapter.get("id"), field + ".id")
    if not CHAPTER_ID_RE.fullmatch(chapter_id):
        console("error=bad_chapter_id")
        raise SystemExit(2)
    title = require_str(chapter.get("title"), field + ".title")
    questions = practice_for_chapter(chapter, content_dir, field)
    parts = [
        '<section class="chapter" id="' + chapter_id + '">',
        "<h2>" + html.escape(title, quote=False) + "</h2>",
        chapter_controls(),
        knowledge_html(as_list(chapter.get("knowledge"), field + ".knowledge"), field + ".knowledge"),
        formula_table(as_list(chapter.get("formulas"), field + ".formulas"), field + ".formulas"),
        traps_html(as_list(chapter.get("traps"), field + ".traps"), field + ".traps"),
        past_papers_html(as_list(chapter.get("past_papers"), field + ".past_papers"), field + ".past_papers"),
        "<h3>巩固练习</h3>",
        practice_box(questions),
        "</section>",
    ]
    return "\n".join(parts), len(questions)


def fill_template(template: str, course: str, exam_type: str, chapters_html: str) -> str:
    exam_line = ""
    if exam_type:
        exam_line = '<p class="meta">' + html.escape(exam_type, quote=False) + "</p>"
    out = template
    out = out.replace("{{COURSE_TITLE}}", html.escape(course, quote=False))
    out = out.replace("{{EXAM_LINE}}", exam_line)
    out = out.replace("{{CHAPTERS}}", chapters_html)
    for token in ("{{COURSE_TITLE}}", "{{EXAM_LINE}}", "{{CHAPTERS}}"):
        if token in out:
            console("error=unfilled_placeholder")
            raise SystemExit(2)
    return out


def assert_no_control_escapes(page: str) -> None:
    # A real backslash+letter must not have been turned into these controls.
    for control in ("\x08", "\x07", "\x0c", "\x0b"):
        if control in page:
            console("error=latex_escape")
            raise SystemExit(2)


def load_chapters(content_path: Path, only: str | None) -> tuple[dict, list]:
    data = read_json(content_path)
    if not isinstance(data, dict):
        console("error=bad_content field=root")
        raise SystemExit(2)
    course = require_str(data.get("course"), "course")
    exam_type = data.get("exam_type", "")
    if exam_type is None:
        exam_type = ""
    exam_type = require_str(exam_type, "exam_type")
    chapters = as_list(data.get("chapters"), "chapters")
    if only:
        if not CHAPTER_ID_RE.fullmatch(only):
            console("error=bad_chapter_id")
            raise SystemExit(2)
        chapters = [item for item in chapters if isinstance(item, dict) and item.get("id") == only]
        if not chapters:
            console("error=chapter_not_found")
            raise SystemExit(2)
    if not chapters:
        console("error=bad_content field=chapters")
        raise SystemExit(2)
    return {"course": course, "exam_type": exam_type}, chapters


def build(content_path: Path, template_path: Path, out_path: Path, only: str | None) -> int:
    meta, chapters = load_chapters(content_path, only)
    template = template_path.read_text(encoding="utf-8")
    bodies: list[str] = []
    question_count = 0
    content_dir = content_path.parent
    for index, chapter in enumerate(chapters):
        body, count = chapter_html(chapter, content_dir, "chapters[" + str(index) + "]")
        bodies.append(body)
        question_count += count
    page = fill_template(template, meta["course"], meta["exam_type"], "\n".join(bodies))
    assert_no_control_escapes(page)
    write_text(out_path, page)
    console("ok=1")
    console("chapters=" + str(len(chapters)))
    console("questions=" + str(question_count))
    console_path("out", out_path)
    return 0


def patch(html_path: Path, practice_path: Path, chapter_id: str, out_path: Path) -> int:
    if not CHAPTER_ID_RE.fullmatch(chapter_id):
        console("error=bad_chapter_id")
        return 2
    questions = load_practice(read_json(practice_path), "practice")
    source = html_path.read_text(encoding="utf-8")
    try:
        start, end = find_practice_span(source, chapter_id)
    except ValueError:
        console("error=practice_box_not_found")
        return 2
    updated = source[:start] + practice_box(questions) + source[end:]
    assert_no_control_escapes(updated)
    write_text(out_path, updated)
    console("ok=1")
    console("chapters=1")
    console("questions=" + str(len(questions)))
    console_path("out", out_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fill the review HTML template from JSON, or patch one practice-box."
    )
    parser.add_argument("--content", help="Content JSON (course, chapters, formula text)")
    parser.add_argument("--out", help="HTML file to write")
    parser.add_argument("--template", help="Template HTML (default: assets/template.html)")
    parser.add_argument("--only", help="Write a single chapter id")
    parser.add_argument("--patch", help="Existing HTML; replace one practice-box in place")
    parser.add_argument("--chapter", help="Chapter id for --patch")
    parser.add_argument("--practice", help="practice_chN.json for --patch")
    args = parser.parse_args(argv)

    if args.patch:
        if not args.chapter or not args.practice:
            console("error=patch_needs_chapter_and_practice")
            return 2
        if args.content:
            console("error=patch_and_content")
            return 2
        out_path = Path(args.out) if args.out else Path(args.patch)
        return patch(Path(args.patch), Path(args.practice), args.chapter, out_path)

    if not args.content or not args.out:
        console("error=content_and_out_required")
        return 2
    template_path = Path(args.template) if args.template else default_template()
    if not template_path.is_file():
        console("error=template_not_found")
        console_path("path", template_path)
        return 2
    return build(Path(args.content), template_path, Path(args.out), args.only)


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
