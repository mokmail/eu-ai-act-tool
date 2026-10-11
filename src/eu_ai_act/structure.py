"""
Structure, citation graph and corpus statistics for the EU AI Act.

The Act's own skeleton — 13 chapters, the sections inside them, which articles
belong to each, and the annex list — is derived from the official EUR-Lex HTML by
``scripts/extract_eurlex.py`` and shipped inside the raw dataset under
``structure``.

On top of that this module computes two things the Act does not state directly:

* a **citation graph** — which article cites which, mined from the article text,
  so you can see which provisions are load-bearing;
* **corpus statistics** — sizes, distributions and obligation counts.

Nothing here needs a model or a network.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from . import compliance, data

_ARTICLE_CITE = re.compile(r"\bArticle\s+(\d+[a-z]?)")
_ANNEX_CITE = re.compile(r"\bAnnex\s+([IVXL]+)\b")
_RECITAL_CITE = re.compile(r"\bRecital\s+(\d+)\b")


# ---------------------------------------------------------------------------
# The Act's skeleton
# ---------------------------------------------------------------------------
def _structure() -> Dict[str, Any]:
    return data.load_raw().get("structure", {}) or {}


@lru_cache(maxsize=1)
def chapters() -> List[Dict[str, Any]]:
    """The 13 chapters, each with its title, sections and article numbers."""
    return _structure().get("chapters", [])


@lru_cache(maxsize=1)
def article_index() -> Dict[str, Dict[str, Any]]:
    """Per-article location: ``{"6": {"chapter": "III", "section": 1, ...}}``."""
    return _structure().get("article_index", {})


@lru_cache(maxsize=1)
def annexes() -> List[Dict[str, Any]]:
    """The 13 annexes, each with its title."""
    return _structure().get("annexes", [])


def chapter(number: str) -> Optional[Dict[str, Any]]:
    for c in chapters():
        if c["number"] == number:
            return c
    return None


def location(article_number: str) -> Optional[Dict[str, Any]]:
    """Where an article sits: its chapter and section."""
    return article_index().get(str(article_number))


def table_of_contents() -> List[Dict[str, Any]]:
    """
    A navigable table of contents: chapters with their resolved article titles,
    and sections nested inside them.
    """
    arts = data.articles()
    out = []
    for c in chapters():
        articles = [
            {"number": n, "title": arts[n]["title"]}
            for n in c["articles"] if n in arts
        ]
        sections = []
        for s in c.get("sections", []):
            sections.append({
                "number": s["number"],
                "title": s["title"],
                "articles": [
                    {"number": n, "title": arts[n]["title"]}
                    for n in s["articles"] if n in arts
                ],
            })
        out.append({
            "number": c["number"],
            "label": c.get("label", f"CHAPTER {c['number']}"),
            "title": c["title"],
            "articles": articles,
            "sections": sections,
        })
    return out


def breadcrumb(article_number: str) -> List[str]:
    """Human-readable path to an article, e.g. ['Chapter III', 'Section 1']."""
    loc = location(article_number)
    if not loc:
        return []
    crumbs = [f"Chapter {loc['chapter']}"]
    if loc.get("section"):
        crumbs.append(f"Section {loc['section']}")
    return crumbs


# ---------------------------------------------------------------------------
# Citation graph
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def citation_graph() -> Dict[str, Any]:
    """
    Which provision cites which, mined from the article text.

    Returns ``{"edges": {from: {to: weight}}, "nodes": [...], "most_cited": [...]}``
    where a node id is ``"Article 6"`` or ``"Annex III"``.
    """
    arts = data.articles()
    edges: Dict[str, Dict[str, int]] = {}
    indegree: Dict[str, int] = {}
    outdegree: Dict[str, int] = {}

    for num, art in arts.items():
        source = f"Article {num}"
        targets: Dict[str, int] = {}
        for m in _ARTICLE_CITE.finditer(art["text"]):
            target = m.group(1)
            if target == num or target not in arts:
                continue
            key = f"Article {target}"
            targets[key] = targets.get(key, 0) + 1
        for m in _ANNEX_CITE.finditer(art["text"]):
            key = f"Annex {m.group(1)}"
            targets[key] = targets.get(key, 0) + 1
        edges[source] = targets
        outdegree[source] = sum(targets.values())
        for key, weight in targets.items():
            indegree[key] = indegree.get(key, 0) + weight

    nodes = sorted(set(edges) | set(indegree), key=_node_sort_key)
    most_cited = sorted(indegree.items(), key=lambda kv: (-kv[1], _node_sort_key(kv[0])))

    return {
        "edges": edges,
        "nodes": nodes,
        "indegree": indegree,
        "outdegree": outdegree,
        "most_cited": [{"ref": ref, "citations": n} for ref, n in most_cited[:25]],
        "edge_count": sum(len(t) for t in edges.values()),
    }


def _node_sort_key(ref: str) -> tuple:
    """Sort 'Article 6a' before 'Article 10' and both before 'Annex III'."""
    kind, _, rest = ref.partition(" ")
    m = re.match(r"(\d+)([a-z]?)", rest)
    if m:
        return (0, int(m.group(1)), m.group(2))
    return (1, rest, "")


def references_of(article_number: str) -> List[Dict[str, Any]]:
    """What one article cites, most-cited first."""
    source = f"Article {article_number}"
    targets = citation_graph()["edges"].get(source, {})
    return [
        {"ref": ref, "count": n}
        for ref, n in sorted(targets.items(), key=lambda kv: (-kv[1], _node_sort_key(kv[0])))
    ]


def cited_by(article_number: str) -> List[Dict[str, Any]]:
    """Which articles cite this one."""
    target = f"Article {article_number}"
    out = []
    for source, targets in citation_graph()["edges"].items():
        if target in targets:
            out.append({"ref": source, "count": targets[target]})
    return sorted(out, key=lambda d: (-d["count"], _node_sort_key(d["ref"])))


# ---------------------------------------------------------------------------
# Corpus statistics
# ---------------------------------------------------------------------------
def _words(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


@lru_cache(maxsize=1)
def stats() -> Dict[str, Any]:
    """Corpus and obligation statistics, all computed from the shipped data."""
    arts = data.articles()
    recs = data.recitals()

    chapter_stats = []
    for c in chapters():
        text = " ".join(arts[n]["text"] for n in c["articles"] if n in arts)
        chapter_stats.append({
            "number": c["number"],
            "title": c["title"],
            "articles": len(c["articles"]),
            "sections": len(c.get("sections", [])),
            "words": _words(text),
        })

    article_sizes = sorted(
        ({"ref": f"Article {n}", "title": a["title"], "words": _words(a["text"])}
         for n, a in arts.items()),
        key=_article_size_key,
    )

    obligations = compliance.OBLIGATIONS
    by_actor: Dict[str, int] = {}
    by_tier: Dict[str, int] = {}
    for o in obligations:
        by_actor[o["actor"]] = by_actor.get(o["actor"], 0) + 1
        by_tier[o["tier"]] = by_tier.get(o["tier"], 0) + 1

    graph = citation_graph()

    return {
        "corpus": {
            "recitals": len(recs),
            "articles": len(arts),
            "annexes": len(data.annexes()),
            "chapters": len(chapters()),
            "sections": sum(len(c.get("sections", [])) for c in chapters()),
            "words": sum(_words(a["text"]) for a in arts.values()),
            "recital_words": sum(_words(r["text"]) for r in recs.values()),
        },
        "chapters": chapter_stats,
        "longest_articles": list(reversed(article_sizes[-8:])),
        "shortest_articles": article_sizes[:8],
        "obligations": {
            "total": len(obligations),
            "by_actor": dict(sorted(by_actor.items(), key=lambda kv: -kv[1])),
            "by_tier": dict(sorted(by_tier.items(), key=lambda kv: -kv[1])),
        },
        "citations": {
            "edges": graph["edge_count"],
            "most_cited": graph["most_cited"][:10],
        },
    }


def _article_size_key(entry: Dict[str, Any]) -> tuple:
    """Natural order: by word count, then by article number."""
    number = entry["ref"].split(" ", 1)[1]
    m = re.match(r"(\d+)([a-z]?)", number)
    return (entry["words"], int(m.group(1)) if m else 0, m.group(2) if m else "")
