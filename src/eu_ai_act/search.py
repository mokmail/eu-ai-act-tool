"""
Full-text search over the EU AI Act.

Searches article text, recital text, and annex text. Supports simple
case-insensitive substring matching plus optional word-boundary matching.
Results are ranked by number of matches and returned with their legal
reference (e.g. 'Article 5', 'Recital 12', 'Annex III').
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from . import data


def _normalise(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    return re.sub(r"\s+", " ", text.lower())


def _count_matches(text: str, terms: List[str], whole_word: bool) -> int:
    """Count occurrences of any of the terms in the text."""
    norm = _normalise(text)
    count = 0
    for term in terms:
        t = _normalise(term)
        if not t:
            continue
        if whole_word:
            count += len(re.findall(rf"\b{re.escape(t)}\b", norm))
        else:
            count += norm.count(t)
    return count


def search(
    query: str,
    scope: str = "all",
    whole_word: bool = False,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search the Act for `query`.

    scope: 'all' | 'articles' | 'recitals' | 'annexes'
    Returns a ranked list of hits, each with a reference, title, and excerpt.
    """
    terms = [t for t in query.split() if t]
    if not terms:
        return []

    results: List[Dict[str, Any]] = []

    if scope in ("all", "articles"):
        for num, art in data.articles().items():
            count = _count_matches(art["text"], terms, whole_word)
            if count:
                results.append(
                    {
                        "ref": f"Article {num}",
                        "title": art["title"],
                        "count": count,
                        "text": art["text"],
                        "kind": "article",
                    }
                )

    if scope in ("all", "recitals"):
        for num, rec in data.recitals().items():
            count = _count_matches(rec["text"], terms, whole_word)
            if count:
                results.append(
                    {
                        "ref": f"Recital {num}",
                        "title": "",
                        "count": count,
                        "text": rec["text"],
                        "kind": "recital",
                    }
                )

    if scope in ("all", "annexes"):
        for num, ann in data.annexes().items():
            count = _count_matches(ann["text"], terms, whole_word)
            if count:
                results.append(
                    {
                        "ref": f"Annex {num}",
                        "title": ann["title"],
                        "count": count,
                        "text": ann["text"],
                        "kind": "annex",
                    }
                )

    results.sort(key=lambda r: r["count"], reverse=True)
    return results[:limit]


def excerpt(text: str, query: str, width: int = 160) -> str:
    """Return a short excerpt of `text` around the first match of `query`."""
    norm = _normalise(text)
    terms = [t for t in query.split() if t]
    if not terms:
        return text[:width]
    first = min(
        (norm.find(_normalise(t)) for t in terms if _normalise(t) in norm),
        default=-1,
    )
    if first < 0:
        return text[:width]
    start = max(0, first - width // 2)
    end = min(len(text), first + width // 2)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
