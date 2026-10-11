"""
Mindmap builder — turns the Act's structure and the curated obligations into
nested trees a diagram can render.

Two shapes are produced:

* **topic maps** — a themed root with branches, each leaf citing a provision
  (e.g. "High-risk AI systems" → Requirements → Risk management system → Art 9);
* **the contents map** — chapters → sections → articles, straight from the Act.

Everything is derived from the shipped data, so a mindmap can never drift from
the text it claims to summarise.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import compliance, data, guides, structure


def _obligation_nodes(ids: List[str]) -> List[Dict[str, Any]]:
    by_id = {o["id"]: o for o in compliance.OBLIGATIONS}
    nodes = []
    for oid in ids:
        o = by_id.get(oid)
        if o:
            nodes.append({"label": o["title"], "ref": o["ref"], "note": o["description"]})
    return nodes


def _leaf(label: str, ref: str, note: str = "") -> Dict[str, Any]:
    return {"label": label, "ref": ref, "note": note}


# ---------------------------------------------------------------------------
# Topic maps
# ---------------------------------------------------------------------------
_HIGH_RISK_BUCKETS = [
    ("Requirements of the system", "Articles 9-15, Chapter III Section 2", [
        "hr-rm", "hr-data", "hr-techdoc", "hr-logs", "hr-transp", "hr-oversight", "hr-robust",
    ]),
    ("Organisation and evidence", "Articles 17, 18", ["hr-qms", "hr-dockeep"]),
    ("Getting it to market", "Articles 43, 47, 48, 49", [
        "hr-conform", "hr-decl", "hr-ce", "hr-reg",
    ]),
    ("Watching it in the field", "Articles 20, 21, 22, 72, 73", [
        "hr-correct", "hr-coop", "hr-authrep", "hr-pmm", "hr-incident",
    ]),
    ("Using it", "Articles 26, 27", ["hr-deploy", "hr-fria"]),
    ("Importers and distributors", "Articles 23, 24", ["hr-imp", "hr-dist"]),
    ("For everyone", "Articles 4, 5", ["proh-1", "lit-1"]),
]


def _high_risk_map() -> Dict[str, Any]:
    # Only the high-risk and cross-cutting obligations belong on this map;
    # transparency and GPAI duties have maps of their own.
    in_scope = {o["id"] for o in compliance.obligations_for(tier="high_risk")}
    children = []
    used = set()
    for title, ref, ids in _HIGH_RISK_BUCKETS:
        scoped = [i for i in ids if i in in_scope]
        used.update(scoped)
        nodes = _obligation_nodes(scoped)
        if nodes:
            children.append({"label": title, "ref": ref, "children": nodes})
    leftover = [i for i in (o["id"] for o in compliance.OBLIGATIONS)
                if i in in_scope and i not in used]
    if leftover:
        children.append({"label": "Other", "ref": "—",
                         "children": _obligation_nodes(leftover)})
    return {"id": "high-risk", "title": "High-risk AI systems", "ref": "Chapter III",
            "summary": "Everything the Act requires once a system is high-risk, grouped "
                       "by the job it has to be done for.",
            "children": children}


def _transparency_map() -> Dict[str, Any]:
    return {"id": "transparency", "title": "Transparency duties", "ref": "Article 50",
            "summary": "The four disclosure triggers and who they land on.",
            "children": _obligation_nodes(["tr-chatbot", "tr-emotion", "tr-deepfake", "tr-public"])}


def _gpai_map() -> Dict[str, Any]:
    baseline = _obligation_nodes(["gpai-techdoc", "gpai-copyright", "gpai-summary"])
    systemic = _obligation_nodes(["gpai-sysrisk"])
    return {"id": "gpai", "title": "General-purpose AI models", "ref": "Articles 51-55",
            "summary": "A lighter regime than high-risk, but it scales sharply once "
                       "systemic risk is presumed.",
            "children": [
                {"label": "Every GPAI model", "ref": "Article 53", "children": baseline},
                {"label": "Plus systemic risk", "ref": "Article 51, Article 55", "children": systemic},
            ]}


def _prohibited_map() -> Dict[str, Any]:
    tier = data.get_risk_tier("prohibited") or {}
    practices = [
        _leaf(p["name"], p["ref"], p.get("description", ""))
        for p in tier.get("practices", [])
    ]
    return {"id": "prohibited", "title": "Prohibited AI practices", "ref": "Article 5",
            "summary": "Banned outright, from 2 February 2025. The highest penalty band.",
            "children": practices}


def _timeline_map() -> Dict[str, Any]:
    return {"id": "timeline", "title": "When it applies", "ref": "Article 113",
            "summary": "The phased application of the Act.",
            "children": [_leaf(e["date"], e["ref"], e["event"]) for e in data.timeline()]}


def _penalties_map() -> Dict[str, Any]:
    return {"id": "penalties", "title": "Penalties", "ref": "Articles 99-101",
            "summary": "What non-compliance costs.",
            "children": [
                _leaf(p["violation"], p["ref"], (p.get("fine") or "") + (f" — {p['note']}" if p.get("note") else ""))
                for p in data.penalties()
            ]}


def _governance_map() -> Dict[str, Any]:
    def convert(node: Dict[str, Any]) -> Dict[str, Any]:
        out = {"label": node["name"], "ref": node.get("ref", ""), "note": node.get("note", "")}
        kids = [convert(c) for c in node.get("children", [])]
        if kids:
            out["children"] = kids
        return out

    root = guides.governance_structure().get("root", {})
    return {"id": "governance", "title": "Who governs the Act", "ref": "Chapter VII",
            "summary": guides.governance_structure().get("note", ""),
            "children": [convert(c) for c in root.get("children", [])]}


def _contents_map() -> Dict[str, Any]:
    arts = data.articles()
    children = []
    for c in structure.chapters():
        sections = {n for s in c.get("sections", []) for n in s["articles"]}
        nodes: List[Dict[str, Any]] = []
        plain = [n for n in c["articles"] if n not in sections]
        if plain:
            nodes.append({
                "label": "Articles",
                "ref": f"Chapter {c['number']}",
                "children": [
                    _leaf(f"{n}. {arts[n]['title']}", f"Article {n}")
                    for n in plain if n in arts
                ],
            })
        for s in c.get("sections", []):
            nodes.append({
                "label": s["title"],
                "ref": f"Chapter {c['number']}, Section {s['number']}",
                "children": [
                    _leaf(f"{n}. {arts[n]['title']}", f"Article {n}")
                    for n in s["articles"] if n in arts
                ],
            })
        children.append({"label": c["title"], "ref": f"Chapter {c['number']}", "children": nodes})
    return {"id": "contents", "title": "The whole Act", "ref": "Regulation (EU) 2024/1689",
            "summary": "13 chapters, 16 sections, 113 articles — the shape of the text.",
            "children": children}


_BUILDERS = {
    "contents": _contents_map,
    "prohibited": _prohibited_map,
    "high-risk": _high_risk_map,
    "transparency": _transparency_map,
    "gpai": _gpai_map,
    "governance": _governance_map,
    "timeline": _timeline_map,
    "penalties": _penalties_map,
}


def topics() -> List[Dict[str, Any]]:
    """The available mindmaps, with a one-line summary each."""
    out = []
    for key, build in _BUILDERS.items():
        try:
            node = build()
        except Exception:  # noqa: BLE001 - one broken map must not hide the rest
            continue
        out.append({"id": key, "title": node["title"], "ref": node.get("ref", ""),
                    "summary": node.get("summary", "")})
    return out


def build(topic_id: str) -> Optional[Dict[str, Any]]:
    """Build one mindmap, or ``None`` if the id is unknown."""
    builder = _BUILDERS.get(topic_id)
    return builder() if builder else None


def chapter_map(chapter_number: str) -> Optional[Dict[str, Any]]:
    """A mindmap of a single chapter: its sections and articles."""
    chapter = structure.chapter(chapter_number.upper())
    if not chapter:
        return None
    arts = data.articles()
    children = []
    if chapter["articles"]:
        children.append({
            "label": "Articles",
            "ref": f"Chapter {chapter['number']}",
            "children": [_leaf(f"{n}. {arts[n]['title']}", f"Article {n}")
                         for n in chapter["articles"] if n in arts],
        })
    for s in chapter.get("sections", []):
        children.append({
            "label": s["title"],
            "ref": f"Section {s['number']}",
            "children": [_leaf(f"{n}. {arts[n]['title']}", f"Article {n}")
                         for n in s["articles"] if n in arts],
        })
    return {"id": f"chapter:{chapter['number']}", "title": chapter["title"],
            "ref": f"Chapter {chapter['number']}", "children": children}
