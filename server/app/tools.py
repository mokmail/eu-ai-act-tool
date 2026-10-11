"""
Tool registry: exposes the existing ``eu_ai_act`` package to the agent as a set
of callable tools with OpenAI function-calling schemas.

Two consumers:

* ``TOOL_SCHEMAS`` — the ``tools`` array sent to the chat model.
* ``execute(name, args)`` — the server-side dispatcher the agent loop calls.

Every tool result is a JSON-serialisable dict shaped as
``{"ref": ..., "title": ..., "text"/"items"/..., "disclaimer"?}`` so the model
gets grounded, citable content and the UI can render a structured card from the
same payload. Nothing here touches the network except ``semantic_search``, which
uses the vector store (and degrades with a clear message when it is not built).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from eu_ai_act import compliance, data, guides, mindmap, search, structure

# Results are fed back to the model, so bound them.
MAX_TEXT = 6000


def _clip(text: str, limit: int = MAX_TEXT) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[... truncated, {len(text) - limit} more characters]"


# ---------------------------------------------------------------------------
# Tool schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_act",
            "description": (
                "Full-text search across the EU AI Act (articles, recitals and "
                "annexes). Returns ranked hits with their legal reference. Use "
                "this to locate where a term, obligation or concept appears."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search terms."},
                    "scope": {
                        "type": "string",
                        "enum": ["all", "articles", "recitals", "annexes"],
                        "description": "Restrict the search to one part of the Act.",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 8)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_article",
            "description": "Return the full official text of a numbered article (e.g. '5', '6', '113').",
            "parameters": {
                "type": "object",
                "properties": {"number": {"type": "string", "description": "Article number."}},
                "required": ["number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recital",
            "description": "Return the full text of a recital (1-180). Recitals carry the intent behind the articles.",
            "parameters": {
                "type": "object",
                "properties": {"number": {"type": "integer", "description": "Recital number."}},
                "required": ["number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_annex",
            "description": "Return the full text of an annex by roman numeral (e.g. 'III' for high-risk areas, 'IV' for technical documentation).",
            "parameters": {
                "type": "object",
                "properties": {"number": {"type": "string", "description": "Annex roman numeral."}},
                "required": ["number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "risk_tier",
            "description": "Explain one of the four risk tiers: prohibited, high_risk, limited_risk, minimal_risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "enum": ["prohibited", "high_risk", "limited_risk", "minimal_risk"],
                    }
                },
                "required": ["tier"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actor_obligations",
            "description": "List the key obligations that apply to a given actor type under the Act.",
            "parameters": {
                "type": "object",
                "properties": {
                    "actor": {
                        "type": "string",
                        "enum": ["provider", "deployer", "importer", "distributor",
                                 "authorised_representative", "operator"],
                    }
                },
                "required": ["actor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_checklist",
            "description": "Generate an actionable compliance checklist for an actor, optionally narrowed to a risk tier. Each item cites its legal basis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "actor": {
                        "type": "string",
                        "enum": ["provider", "deployer", "importer", "distributor",
                                 "authorised_representative", "operator", "all"],
                    },
                    "tier": {
                        "type": "string",
                        "enum": ["prohibited", "high_risk", "limited_risk",
                                 "minimal_risk", "gpai", "gpai_systemic"],
                    },
                },
                "required": ["actor"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "classify_high_risk",
            "description": "Heuristically assess whether an AI system is likely high-risk under Article 6 / Annex III, from a plain-language description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "What the AI system does."}
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "timeline",
            "description": "Return the phased application timeline of the Act.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "penalties",
            "description": "Return the penalty schedule (fines for infringements).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "definitions",
            "description": "Return the key statutory definitions, or a single one by term.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Optional term key, e.g. 'ai_system', 'provider', 'systemic_risk'.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "governance",
            "description": "Return the EU governance bodies established by the Act and their roles.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cross_references",
            "description": "Return the curated cross-reference map (GPAI models, sandboxes, market surveillance, fundamental rights, real-world testing).",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Optional topic key."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": (
                "Semantic (embedding) search over the full Act. Better than "
                "keyword search for conceptual or paraphrased questions. "
                "Requires the vector store to be built."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "n": {"type": "integer", "description": "Number of passages (default 5)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "citation",
            "description": "Return the official citation of Regulation (EU) 2024/1689.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "structure_of_act",
            "description": (
                "Navigate the Act's own structure. With no argument, returns the "
                "table of contents (13 chapters, their sections and article numbers). "
                "With an article number, returns where that article sits."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "article": {"type": "string", "description": "Optional article number."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "procedures",
            "description": (
                "Step-by-step procedures for complying with the Act, each step citing "
                "its article (classification, conformity assessment, deployer duties, "
                "fundamental rights impact assessment, serious-incident reporting, GPAI, "
                "transparency). With no argument, lists them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Optional procedure id or a keyword such as 'fria' or 'incident'."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scenarios",
            "description": (
                "Worked, illustrative examples of applying the Act to a real-world "
                "system (CV screening, credit scoring, hospital triage, chatbots, "
                "social scoring, police biometrics, frontier models). With no argument, "
                "lists them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Optional scenario id or keyword."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "corpus_stats",
            "description": "Corpus statistics: counts, size by chapter, and how obligations distribute across actors and tiers.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "provision_references",
            "description": (
                "The citation graph between provisions. Which articles does a given "
                "article cite, and which articles cite it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "article": {"type": "string", "description": "Article number."},
                    "direction": {
                        "type": "string",
                        "enum": ["out", "in", "both"],
                        "description": "out = what it cites (default), in = who cites it.",
                    },
                },
                "required": ["article"],
            },
        },
    },
]

TOOL_NAMES = [t["function"]["name"] for t in TOOL_SCHEMAS]


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
class ToolError(ValueError):
    """Raised for an unknown tool or unusable arguments."""


def execute(name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run a tool by name and return a JSON-serialisable result."""
    args = args or {}
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ToolError(f"Unknown tool '{name}'. Available: {', '.join(TOOL_NAMES)}")
    return handler(args)


# -- individual handlers ----------------------------------------------------
def _search_act(args: Dict[str, Any]) -> Dict[str, Any]:
    query = str(args.get("query") or "").strip()
    if not query:
        raise ToolError("search_act requires a non-empty 'query'.")
    scope = args.get("scope") or "all"
    limit = int(args.get("limit") or 8)
    hits = search.search(query, scope=scope, limit=limit)
    items = [
        {
            "ref": h["ref"],
            "title": h["title"],
            "matches": h["count"],
            "excerpt": search.excerpt(h["text"], query, width=240),
        }
        for h in hits
    ]
    return {
        "ref": f"search: {query}",
        "result_count": len(items),
        "items": items,
        "text": "\n".join(f"- {i['ref']}: {i['excerpt']}" for i in items) or "No matches.",
    }


def _provision_text(text: str, args: Dict[str, Any]) -> str:
    """
    The agent's context is bounded, so a tool result is clipped; a person reading
    the Act in a browser is not. `full` is set by the REST passthrough only — the
    tool schema never offers it, so the model cannot ask for the unclipped text.
    """
    return text if args.get("full") else _clip(text)


def _get_article(args: Dict[str, Any]) -> Dict[str, Any]:
    number = str(args.get("number") or "").strip()
    art = data.get_article(number)
    if not art:
        return {"ref": f"Article {number}", "text": f"Article {number} not found."}
    return {"ref": f"Article {number}", "title": art["title"],
            "text": _provision_text(art["text"], args)}


def _get_recital(args: Dict[str, Any]) -> Dict[str, Any]:
    number = int(args.get("number") or 0)
    rec = data.get_recital(number)
    if not rec:
        return {"ref": f"Recital {number}", "text": f"Recital {number} not found."}
    return {"ref": f"Recital {number}", "text": _provision_text(rec["text"], args)}


def _get_annex(args: Dict[str, Any]) -> Dict[str, Any]:
    number = str(args.get("number") or "").strip().upper()
    ann = data.get_annex(number)
    if not ann:
        return {"ref": f"Annex {number}", "text": f"Annex {number} not found."}
    return {"ref": f"Annex {number}", "title": ann["title"],
            "text": _provision_text(ann["text"], args)}


def _risk_tier(args: Dict[str, Any]) -> Dict[str, Any]:
    tier = str(args.get("tier") or "").strip()
    t = data.get_risk_tier(tier)
    if not t:
        return {"ref": tier, "text": f"Risk tier '{tier}' not found.",
                "options": ["prohibited", "high_risk", "limited_risk", "minimal_risk"]}
    return {"ref": t["legal_basis"], "title": t["label"], "summary": t["summary"],
            "applies_from": t.get("applies_from"),
            "penalty": t.get("penalty"),
            "areas": t.get("annex_iii_areas"),
            "practices": t.get("practices"),
            "obligations": t.get("obligations"),
            "text": t["summary"]}


def _actor_obligations(args: Dict[str, Any]) -> Dict[str, Any]:
    actor = str(args.get("actor") or "").strip()
    a = data.get_actor(actor)
    if not a:
        return {"ref": actor, "text": f"Actor '{actor}' not found."}
    items = [{"obligation": o["obligation"], "ref": o["ref"]}
             for o in a["key_obligations"]]
    return {"ref": f"Actor: {a['actor']}", "definition": a["definition"],
            "definition_ref": a["definition_ref"], "items": items,
            "text": "\n".join(f"- {i['obligation']} ({i['ref']})" for i in items)}


def _compliance_checklist(args: Dict[str, Any]) -> Dict[str, Any]:
    actor = str(args.get("actor") or "all").strip()
    tier = args.get("tier")
    items = compliance.checklist(actor, tier)
    packed = [
        {"title": i["title"], "description": i["description"],
         "action": i["action"], "ref": i["ref"]}
        for i in items
    ]
    return {
        "ref": f"checklist: {actor}" + (f" / {tier}" if tier else ""),
        "count": len(packed),
        "items": packed,
        "text": "\n".join(f"- [ ] {i['title']} ({i['ref']}) — {i['action']}"
                          for i in packed) or "No obligations for that filter.",
    }


def _classify_high_risk(args: Dict[str, Any]) -> Dict[str, Any]:
    description = str(args.get("description") or "").strip()
    if not description:
        raise ToolError("classify_high_risk requires a 'description'.")
    r = compliance.classify_high_risk(description)
    areas = [{"area": a["area"], "name": a["name"], "ref": a["ref"]}
             for a in r["matched_annex_iii_areas"]]
    verdict = "LIKELY HIGH-RISK" if r["likely_high_risk"] else "LIKELY NOT HIGH-RISK"
    return {"ref": r["ref"], "verdict": verdict, "likely_high_risk": r["likely_high_risk"],
            "areas": areas, "disclaimer": r["disclaimer"],
            "text": f"{verdict}. " + "; ".join(f"[{a['area']}] {a['name']} ({a['ref']})"
                                               for a in areas)}


def _timeline(args: Dict[str, Any]) -> Dict[str, Any]:
    events = [{"date": e["date"], "event": e["event"], "ref": e["ref"]}
              for e in data.timeline()]
    return {"ref": "Article 113", "items": events,
            "text": "\n".join(f"- {e['date']}: {e['event']} ({e['ref']})" for e in events)}


def _penalties(args: Dict[str, Any]) -> Dict[str, Any]:
    rows = [{"violation": p["violation"], "fine": p.get("fine"),
             "note": p.get("note"), "ref": p["ref"]} for p in data.penalties()]
    return {"ref": "Article 99", "items": rows,
            "text": "\n".join(f"- {r['violation']}: {r.get('fine') or ''} ({r['ref']})"
                              for r in rows)}


def _definitions(args: Dict[str, Any]) -> Dict[str, Any]:
    defs = data.definitions()
    term = args.get("term")
    if term:
        d = defs.get(str(term))
        if not d:
            return {"ref": str(term), "text": f"No definition for '{term}'.",
                    "available": sorted(defs.keys())}
        return {"ref": d["ref"], "term": term, "definition": d["definition"],
                "text": f"{term}: {d['definition']}"}
    items = [{"term": k, "ref": v["ref"], "definition": v["definition"]}
             for k, v in defs.items()]
    return {"ref": "Article 3", "items": items,
            "text": "\n".join(f"- {i['term']}: {i['definition']}" for i in items)}


def _governance(args: Dict[str, Any]) -> Dict[str, Any]:
    bodies = [{"body": g["body"], "role": g["role"], "ref": g["ref"]}
              for g in data.governance_bodies()]
    return {"ref": "Chapter VII", "items": bodies,
            "text": "\n".join(f"- {b['body']} ({b['ref']}): {b['role']}" for b in bodies)}


def _cross_references(args: Dict[str, Any]) -> Dict[str, Any]:
    crs = data.cross_references()
    topic = args.get("topic")
    if topic:
        cr = crs.get(str(topic))
        if not cr:
            return {"ref": str(topic), "text": f"No cross-reference group '{topic}'.",
                    "available": sorted(crs.keys())}
        crs = {topic: cr}
    items = [{"topic": k, "ref": v["ref"], "summary": v["summary"],
              "key_articles": v["key_articles"]} for k, v in crs.items()]
    return {"ref": "cross-references", "items": items,
            "text": "\n".join(f"- {i['topic']}: {i['summary']} ({i['ref']})" for i in items)}


def _citation(args: Dict[str, Any]) -> Dict[str, Any]:
    c = data.citation()
    return {"ref": "EUR-Lex", "text": c, "citation": c}


def _semantic_search(args: Dict[str, Any]) -> Dict[str, Any]:
    query = str(args.get("query") or "").strip()
    if not query:
        raise ToolError("semantic_search requires a non-empty 'query'.")
    n = int(args.get("n") or 5)
    try:
        from eu_ai_act import vector_store  # pulls in chromadb only when used

        hits = vector_store.query(query, n_results=n)
    except Exception as exc:  # noqa: BLE001 - surface any failure as tool output
        return {
            "ref": f"semantic: {query}",
            "text": (f"Semantic search unavailable: {exc}. "
                     "Fall back to search_act (keyword search)."),
            "unavailable": True,
        }
    items = [{"ref": h["ref"], "title": h.get("title", ""), "text": h["text"],
              "distance": h.get("distance")} for h in hits]
    return {"ref": f"semantic: {query}", "items": items,
            "text": "\n\n".join(f"[{i['ref']}]\n{i['text']}" for i in items) or "No matches."}


def _ranges(numbers: List[Any]) -> str:
    """Compress article numbers into a readable range list: 1-4, 6, 8-10."""
    nums = sorted({int(n) for n in numbers if str(n).isdigit()})
    if not nums:
        return ", ".join(str(n) for n in numbers)
    parts, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        parts.append(str(nums[i]) if i == j else f"{nums[i]}-{nums[j]}")
        i = j + 1
    return ", ".join(parts)


def _structure_of_act(args: Dict[str, Any]) -> Dict[str, Any]:
    article = str(args.get("article") or "").strip()
    if article:
        loc = structure.location(article)
        if not loc:
            return {"ref": f"Article {article}",
                    "text": f"Article {article} is not in the Act."}
        path = structure.breadcrumb(article)
        return {
            "ref": f"Article {article}",
            "chapter": loc["chapter"],
            "chapter_title": loc["chapter_title"],
            "section": loc["section"],
            "section_title": loc["section_title"],
            "breadcrumb": path,
            "text": f"Article {article} sits in {' > '.join(path)}.",
        }

    chapters = []
    lines = []
    for c in structure.table_of_contents():
        chapters.append({
            "number": c["number"],
            "title": c["title"],
            "articles": f"{c['articles'][0]['number']}-{c['articles'][-1]['number']}"
            if c["articles"] else "",
            "sections": [
                {"number": s["number"], "title": s["title"],
                 "articles": _ranges([a["number"] for a in s["articles"]])}
                for s in c["sections"]
            ],
        })
        lines.append(f"Chapter {c['number']} — {c['title']}"
                     + (f" (Articles {_ranges([a['number'] for a in c['articles']])})"
                        if c["articles"] else ""))
        for s in c["sections"]:
            lines.append(f"  Section {s['number']} — {s['title']}"
                         f" (Articles {_ranges([a['number'] for a in s['articles']])})")
    return {"ref": "Table of contents", "chapters": chapters, "text": "\n".join(lines)}


def _match(items: List[Dict[str, Any]], key: str, extra: List[str]) -> List[Dict[str, Any]]:
    """
    Find the entries a keyword refers to, most-specific first: an exact id, then
    an id substring, then the title, then any other field. Stops at the first
    tier that matches, so 'incident' finds the serious-incident procedure rather
    than every procedure that mentions incidents.
    """
    for test in (
        lambda x: x["id"] == key,
        lambda x: key in x["id"],
        lambda x: key in x.get("title", "").lower(),
        lambda x: any(key in str(x.get(f, "")).lower() for f in extra),
    ):
        hits = [x for x in items if test(x)]
        if hits:
            return hits
    return []


def _procedures(args: Dict[str, Any]) -> Dict[str, Any]:
    key = str(args.get("id") or "").strip().lower()
    if key:
        matches = _match(guides.procedures(), key, ["actor", "summary"])
        if not matches:
            return {"text": f"No procedure matches '{key}'.",
                    "available": [{"id": p["id"], "title": p["title"]}
                                  for p in guides.procedures()]}
        if len(matches) > 1:
            return {"text": "Several procedures match — which one?",
                    "candidates": [{"id": p["id"], "title": p["title"]} for p in matches]}
        proc = matches[0]
        # The detail must be a superset of the list entry — the UI renders `tier`
        # and `summary` from it, and dropping one blanks the panel.
        return {
            "ref": proc["ref"],
            "id": proc["id"],
            "title": proc["title"],
            "actor": proc["actor"],
            "tier": proc["tier"],
            "summary": proc["summary"],
            "steps": proc["steps"],
            "text": f"{proc['title']} ({proc['ref']})\n" + "\n".join(
                f"{s['n']}. {s['title']} ({s['ref']}) — {s['detail']}" for s in proc["steps"]),
        }

    items = [{"id": p["id"], "title": p["title"], "actor": p["actor"],
              "tier": p["tier"], "ref": p["ref"], "steps": len(p["steps"]),
              "summary": p["summary"]} for p in guides.procedures()]
    return {"ref": "procedures", "items": items,
            "text": "\n".join(f"- {i['title']} [{i['id']}] — {i['summary']}" for i in items)}


def _scenarios(args: Dict[str, Any]) -> Dict[str, Any]:
    key = str(args.get("id") or "").strip().lower()
    if key:
        matches = _match(guides.scenarios(), key, ["sector", "summary", "tier"])
        if not matches:
            return {"text": f"No scenario matches '{key}'.",
                    "available": [{"id": s["id"], "title": s["title"]}
                                  for s in guides.scenarios()]}
        if len(matches) > 1:
            return {"text": "Several scenarios match — which one?",
                    "candidates": [{"id": s["id"], "title": s["title"]} for s in matches]}
        scen = matches[0]
        return {
            "ref": scen["refs"][0] if scen["refs"] else "",
            "id": scen["id"],
            "title": scen["title"],
            "sector": scen["sector"],
            "tier": scen["tier"],
            "refs": scen["refs"],
            "analysis": scen["analysis"],
            "watchouts": scen.get("watchouts", []),
            "disclaimer": ("Illustrative example built from the Act, not an enforcement "
                           "decision."),
            "text": f"{scen['title']} — {scen['summary']}\nTier: {scen['tier']}\n" + "\n".join(
                f"- {a['title']} ({a['ref']}): {a['detail']}" for a in scen["analysis"]),
        }

    items = [{"id": s["id"], "title": s["title"], "sector": s["sector"],
              "tier": s["tier"], "refs": s["refs"], "summary": s["summary"]}
             for s in guides.scenarios()]
    return {"ref": "scenarios", "items": items,
            "disclaimer": "Illustrative examples, not enforcement decisions.",
            "text": "\n".join(f"- {i['title']} [{i['tier']}]" for i in items)}


def _corpus_stats(args: Dict[str, Any]) -> Dict[str, Any]:
    s = structure.stats()
    c = s["corpus"]
    text = (f"{c['articles']} articles, {c['recitals']} recitals, {c['annexes']} annexes, "
            f"{c['chapters']} chapters, {c['sections']} sections, {c['words']:,} words.\n"
            + "\n".join(f"- Chapter {ch['number']} {ch['title']}: {ch['articles']} articles, "
                        f"{ch['words']:,} words" for ch in s["chapters"]))
    return {**s, "ref": "corpus statistics", "text": text}


def _provision_references(args: Dict[str, Any]) -> Dict[str, Any]:
    article = str(args.get("article") or "").strip()
    if not article:
        raise ToolError("provision_references requires an 'article'.")
    direction = args.get("direction") or "out"
    out: Dict[str, Any] = {"ref": f"Article {article}"}
    lines = []
    if direction in ("out", "both"):
        refs = structure.references_of(article)
        out["cites"] = refs
        lines += [f"cites {r['ref']} ({r['count']}×)" for r in refs[:12]]
    if direction in ("in", "both"):
        back = structure.cited_by(article)
        out["cited_by"] = back
        lines += [f"cited by {r['ref']} ({r['count']}×)" for r in back[:12]]
    out["text"] = f"Article {article}: " + ("; ".join(lines) or "no cross-references found.")
    return out


_HANDLERS = {
    "search_act": _search_act,
    "get_article": _get_article,
    "get_recital": _get_recital,
    "get_annex": _get_annex,
    "risk_tier": _risk_tier,
    "actor_obligations": _actor_obligations,
    "compliance_checklist": _compliance_checklist,
    "classify_high_risk": _classify_high_risk,
    "timeline": _timeline,
    "penalties": _penalties,
    "definitions": _definitions,
    "governance": _governance,
    "cross_references": _cross_references,
    "citation": _citation,
    "semantic_search": _semantic_search,
    "structure_of_act": _structure_of_act,
    "procedures": _procedures,
    "scenarios": _scenarios,
    "corpus_stats": _corpus_stats,
    "provision_references": _provision_references,
}
