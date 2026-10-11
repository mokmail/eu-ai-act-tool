"""
Render the extracted EUR-Lex text as well-formed Markdown.

The extractor strips HTML, which leaves the Act's structure encoded only in line
breaks and markers:

    1. The following AI practices shall be prohibited:
     (a)
     the placing on the market, ...
     (b)
     ...

This module recovers that structure — paragraph numbers, lettered points, roman
sub-points, numbered definitions, annex section headings — so the text renders
with real typographic hierarchy instead of a wall of pre-wrapped prose.

Three facts about the source, each established by reading the corpus rather than
guessed at, drive the design:

* **One line is one block.** ``\\n`` comes from a block-level HTML tag, so a line
  is never a soft wrap. A marker standing alone therefore takes exactly the *next*
  line as its body; anything after that is a separate paragraph. Merging runs of
  lines would swallow half of Article 3 into a single bullet.
* **A marker is the citation.** Paragraph numbers and point labels are preserved
  verbatim ("1.", "(a)", "(i)", "(46)"), so markdown's automatic list renumbering
  must never be allowed to rewrite them.
* **Nesting follows the sequence, not the look of the label.** ``(i)`` is genuinely
  ambiguous: in Article 16 it is the letter after ``(h)``, in Article 5 a sub-point
  of ``(h)``. Only the *following* marker distinguishes them — see :func:`_nest`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence

_PARA_ALONE = re.compile(r"^(\d{1,3})\.$")
_PARA_INLINE = re.compile(r"^(\d{1,3})\.\s+(.+)$")
_POINT_ALONE = re.compile(r"^\((\d{1,3}|[a-z]{1,2}|[ivxlcdm]{1,6})\)$")
_POINT_INLINE = re.compile(r"^\((\d{1,3}|[a-z]{1,2}|[ivxlcdm]{1,6})\)\s+(.+)$")
_SECTION = re.compile(r"^Section\s+([A-Z])\.\s*(.*)$")
_STRUCTURE = re.compile(r"^(?:CHAPTER|SECTION)\s+[IVXLC0-9]+$")

_ROMAN_VALUES = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7,
                 "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12}

_SENTENCE_END = (".", ";", ":", "?", "!")
_MAX_DROPPED_HEADING_LINES = 8


@dataclass
class _Block:
    kind: str            # "para" | "point" | "section" | "plain"
    label: str
    text: str
    level: int = 1       # points only: 1 = top level, 2+ = sub-point


# -- reading the flat text --------------------------------------------------
def _is_marker(line: str) -> bool:
    return bool(
        _PARA_ALONE.match(line)
        or _PARA_INLINE.match(line)
        or _POINT_ALONE.match(line)
        or _POINT_INLINE.match(line)
        or _SECTION.match(line)
    )


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_structural_tail(line: str) -> bool:
    """A chapter/section heading, or its title: short and not a sentence."""
    if _STRUCTURE.match(line):
        return True
    return len(line) <= 80 and not line.endswith(_SENTENCE_END)


def _strip_trailing_structure(lines: List[str]) -> List[str]:
    """
    Drop the chapter/section headings left dangling at the end of the last article
    before them.

    Article 5 ends with ``CHAPTER III / HIGH-RISK AI SYSTEMS / SECTION 1 /
    Classification of AI systems as high-risk`` — the next chapter's masthead, not
    part of Article 5. Every such block in the corpus sits at the very end, and the
    headings are already carried by the structure data.
    """
    end = len(lines)
    while end > 0 and _is_structural_tail(lines[end - 1]):
        end -= 1

    dropped = lines[end:]
    if dropped and _STRUCTURE.match(dropped[0]) and len(dropped) <= _MAX_DROPPED_HEADING_LINES:
        return lines[:end]
    return lines


def _body_of(lines: Sequence[str], index: int) -> str:
    """The next line, when it is the body of the marker at ``index``."""
    nxt = lines[index + 1] if index + 1 < len(lines) else ""
    return "" if (not nxt or _is_marker(nxt)) else _clean(nxt)


def _body_length(lines: Sequence[str], index: int) -> int:
    """How many source lines the marker at ``index`` consumed: 1, or 2 with a body."""
    nxt = lines[index + 1] if index + 1 < len(lines) else ""
    return 2 if (nxt and not _is_marker(nxt)) else 1


def _parse(text: str) -> List[_Block]:
    """Split the flat text into typed blocks, each carrying its own body."""
    lines = _strip_trailing_structure([line.strip() for line in text.split("\n") if line.strip()])
    blocks: List[_Block] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        section = _SECTION.match(line)
        if section:
            blocks.append(_Block("section", section.group(1), _clean(section.group(2))))
            i += 1
            continue

        # paragraph numbers: "1." alone takes the next line; "1. text" is inline
        para = _PARA_ALONE.match(line)
        if para:
            blocks.append(_Block("para", para.group(1), _body_of(lines, i)))
            i += _body_length(lines, i)
            continue

        para = _PARA_INLINE.match(line)
        if para:
            blocks.append(_Block("para", para.group(1), _clean(para.group(2))))
            i += 1
            continue

        # points: letters, roman numerals, or the (1)-(68) numbered definitions
        point = _POINT_ALONE.match(line)
        if point:
            blocks.append(_Block("point", point.group(1), _body_of(lines, i)))
            i += _body_length(lines, i)
            continue

        point = _POINT_INLINE.match(line)
        if point:
            blocks.append(_Block("point", point.group(1), _clean(point.group(2))))
            i += 1
            continue

        blocks.append(_Block("plain", "", _clean(line)))
        i += 1

    return blocks


# -- nesting ----------------------------------------------------------------
def _is_roman(label: str) -> bool:
    return label in _ROMAN_VALUES


def _successor(label: str) -> str:
    """The next label in the a, b, ... z, aa, ab sequence."""
    if len(label) == 1:
        return "aa" if label == "z" else chr(ord(label) + 1)
    return label[:-1] + chr(ord(label[-1]) + 1)


def _nest(blocks: Sequence[_Block]) -> None:
    """
    Decide which points are sub-points, in place.

    A roman-looking label is top-level only when it continues the letter sequence
    (``(h)`` → ``(i)``, as in Article 16). Otherwise it nests. One case defeats that
    test — Article 5 nests ``(i)``, ``(ii)``, ``(iii)`` under ``(h)``, where ``(i)``
    *looks* like the successor letter — so a run is corrected once the marker after
    it proves the series is roman.

    Numbered markers (``(46)`` in Article 3, ``(1)``-``(6)`` in Article 108) stand in
    for the paragraph level rather than the point level, so the letters inside them
    belong one rung down; ``base`` carries that shift.
    """
    last_letter: Optional[str] = None
    base = 1
    run: List[_Block] = []

    for block in blocks:
        if block.kind != "point":
            if block.kind in ("para", "section"):
                last_letter = None
                base = 1
            _correct_run(run)
            run = []
            continue

        label = block.label
        if label.isdigit():
            block.level = 1
            base = 2
            last_letter = None
        elif _is_roman(label) and last_letter is not None and label == _successor(last_letter):
            block.level = base
            last_letter = label
        elif _is_roman(label):
            block.level = base + 1
        else:
            block.level = base
            last_letter = label
        run.append(block)

    _correct_run(run)


def _correct_run(run: Sequence[_Block]) -> None:
    """Demote a `(i)`/`(v)`/`(x)` that a following `(ii)`/`(vi)`/`(xi)` proves roman."""
    for first, second in zip(run, run[1:]):
        if (first.level + 1 == second.level
                and _is_roman(first.label) and _is_roman(second.label)
                and _ROMAN_VALUES[second.label] == _ROMAN_VALUES[first.label] + 1):
            first.level = second.level


# -- writing markdown -------------------------------------------------------
def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def to_markdown(text: str, title: Optional[str] = None) -> str:
    """
    Convert one provision's extracted text to Markdown.

    ``title`` is the provision's own heading; annex texts repeat it as their first
    line, so it is dropped when it would only duplicate the heading.
    """
    if not text or not text.strip():
        return ""

    blocks = _parse(text)
    if title:
        wanted = _normalise(title)
        while blocks and blocks[0].kind == "plain" and _normalise(blocks[0].text) == wanted:
            blocks.pop(0)

    _nest(blocks)

    out: List[str] = []
    previous: Optional[str] = None
    for block in blocks:
        if not block.text:
            continue

        # points form one tight list; every other change of kind gets a blank line
        if out and not (block.kind == "point" and previous == "point"):
            out.append("")

        if block.kind == "section":
            out.append(f"**Section {block.label}.** {block.text}")
        elif block.kind == "para":
            out.append(f"**{block.label}.** {block.text}")
        elif block.kind == "point":
            out.append(f"{'  ' * (block.level - 1)}- **({block.label})** {block.text}")
        else:
            out.append(block.text)

        previous = block.kind

    markdown = re.sub(r"\n{3,}", "\n\n", "\n".join(out).strip())
    return markdown + "\n" if markdown else ""
