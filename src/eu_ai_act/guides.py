"""
The curated "understand and apply" layer.

Ships alongside the dataset as ``data/guides.json`` and adds four things the raw
text cannot give you directly:

* a **classification path** — the decision ladder from prohibited to minimal risk;
* **procedures** — step-by-step, each step citing the provision it comes from;
* **scenarios** — worked, illustrative cases;
* **governance structure** — the institutional tree, for the organigram.

Every entry cites its legal basis. The scenarios are illustrative examples built
from the Act's own text, not enforcement decisions.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

from .data import DATA_DIR, load_raw

GUIDES_JSON = os.path.join(DATA_DIR, "guides.json")


class GuidesError(RuntimeError):
    """Raised when the guide layer cannot be loaded."""


@lru_cache(maxsize=1)
def _guides() -> Dict[str, Any]:
    if not os.path.exists(GUIDES_JSON):
        raise GuidesError(f"Guide layer not found at {GUIDES_JSON}.")
    with open(GUIDES_JSON, encoding="utf-8") as f:
        return json.load(f)


def meta() -> Dict[str, Any]:
    return _guides().get("meta", {})


# -- classification path ----------------------------------------------------
def risk_path() -> Dict[str, Any]:
    """The decision ladder: questions, branches and the tier outcomes."""
    return _guides().get("risk_path", {})


def classify_path(answers: Dict[str, bool]) -> Dict[str, Any]:
    """
    Walk the classification ladder given ``{question_id: True/False}``.

    Missing answers stop the walk and return the question that is still open, so
    a UI can ask one thing at a time.
    """
    path = risk_path()
    questions = {q["id"]: q for q in path.get("questions", [])}
    outcomes = path.get("outcomes", {})
    trace: List[Dict[str, Any]] = []

    node = path.get("start")
    while node:
        if node in outcomes:
            return {
                "outcome": node,
                "label": outcomes[node]["label"],
                "detail": outcomes[node],
                "trace": trace,
                "complete": True,
            }
        question = questions.get(node)
        if question is None:
            return {"outcome": None, "trace": trace, "complete": False,
                    "error": f"unknown node '{node}'"}
        if node not in answers:
            return {"outcome": None, "question": question, "trace": trace,
                    "complete": False}
        yes = bool(answers[node])
        trace.append({"question": question["question"], "ref": question.get("ref"),
                      "answer": "yes" if yes else "no"})
        node = question["yes"] if yes else question["no"]

    return {"outcome": None, "trace": trace, "complete": False}


# -- procedures -------------------------------------------------------------
def procedures() -> List[Dict[str, Any]]:
    return _guides().get("procedures", [])


def get_procedure(procedure_id: str) -> Optional[Dict[str, Any]]:
    for p in procedures():
        if p["id"] == procedure_id:
            return p
    return None


def procedures_for(actor: Optional[str] = None, tier: Optional[str] = None) -> List[Dict[str, Any]]:
    out = procedures()
    if actor:
        key = actor.lower().replace(" ", "_")
        out = [p for p in out if p["actor"] in ("all", key)]
    if tier:
        key = tier.lower().replace(" ", "_")
        out = [p for p in out if p["tier"] in ("all", key)]
    return out


# -- scenarios --------------------------------------------------------------
def scenarios() -> List[Dict[str, Any]]:
    return _guides().get("scenarios", [])


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    for s in scenarios():
        if s["id"] == scenario_id:
            return s
    return None


def scenarios_for(tier: Optional[str] = None, sector: Optional[str] = None) -> List[Dict[str, Any]]:
    out = scenarios()
    if tier:
        key = tier.lower().replace(" ", "_")
        out = [s for s in out if s["tier"] == key]
    if sector:
        out = [s for s in out if s["sector"].lower() == sector.lower()]
    return out


# -- integrity --------------------------------------------------------------
CASE_KEYS = {"id", "title", "sector", "summary", "tier", "refs", "roles", "analysis", "watchouts"}
CASE_TIERS = {"prohibited", "high_risk", "limited_risk", "minimal_risk", "gpai", "gpai_systemic"}

_ARTICLE_CITE = re.compile(r"\bArticles?\s+([0-9][0-9,\s\-–]*)")
_ANNEX_CITE = re.compile(r"\bAnnex(?:es)?\s+([IVXLC][IVXLC,\s]*)")
_ANNEX_III_POINT = re.compile(r"Annex\s+III,?\s+point\s+(\d+)")


def _bad_citations(text: str, articles: set, annexes: set) -> List[str]:
    """Citations in one string that point at a provision the corpus does not have."""
    bad: List[str] = []
    for match in _ARTICLE_CITE.finditer(text):
        for token in re.split(r"[,\s]+", match.group(1).strip()):
            if not token:
                continue
            if token.isdigit():
                if token not in articles:
                    bad.append(f"Article {token}")
            elif re.fullmatch(r"\d+\s*[-–]\s*\d+", token):
                lo, hi = (int(x) for x in re.split(r"[-–]", token))
                bad += [f"Article {n}" for n in range(lo, hi + 1) if str(n) not in articles]
            else:
                bad.append(f"unparseable citation {token!r}")
    for match in _ANNEX_CITE.finditer(text):
        for token in re.split(r"[,\s]+", match.group(1).strip()):
            if token and token not in annexes:
                bad.append(f"Annex {token}")
    for match in _ANNEX_III_POINT.finditer(text):
        if not 1 <= int(match.group(1)) <= 8:
            bad.append(f"Annex III point {match.group(1)}")
    return bad


def validation_errors(cases: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Everything wrong with a case corpus, one human-readable line each; ``[]`` if sound.

    The cases are authored content rather than text derived from the Act, so a
    citation is the only thing tying a claim to the law — and "Article 114" reads as
    plausibly as "Article 113" to anyone who has not memorised all of them. Every
    provision a case cites is therefore checked against the shipped corpus.

    Pass ``cases`` to screen a candidate set before merging it; the default checks
    what actually shipped.
    """
    cases = scenarios() if cases is None else cases
    raw = load_raw()
    articles = {str(a["number"]) for a in raw["articles"]}
    annexes = {str(a["number"]).upper() for a in raw["annexes"]}

    problems: List[str] = []
    seen: set = set()

    for case in cases:
        where = f"case {case.get('id')!r}"

        if set(case) != CASE_KEYS:
            problems.append(f"{where}: keys differ by {sorted(set(case) ^ CASE_KEYS)}")
            continue
        if not re.fullmatch(r"[a-z0-9-]+", case["id"]):
            problems.append(f"{where}: id is not a slug")
        elif case["id"] in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(case["id"])

        if case["tier"] not in CASE_TIERS:
            problems.append(f"{where}: unknown tier {case['tier']!r}")
        for field in ("title", "sector", "summary"):
            if not case[field].strip():
                problems.append(f"{where}: empty {field}")
        if not case["refs"]:
            problems.append(f"{where}: cites nothing")
        if not 2 <= len(case["roles"]) <= 4:
            problems.append(f"{where}: {len(case['roles'])} roles, want 2-4")
        if not 3 <= len(case["analysis"]) <= 6:
            problems.append(f"{where}: {len(case['analysis'])} analysis items, want 3-6")
        if not 1 <= len(case["watchouts"]) <= 4:
            problems.append(f"{where}: {len(case['watchouts'])} watchouts, want 1-4")
        for role in case["roles"]:
            if not (role.get("role") and role.get("who")):
                problems.append(f"{where}: malformed role {role!r}")
        for item in case["analysis"]:
            if not (item.get("title") and item.get("detail") and item.get("ref")):
                problems.append(f"{where}: malformed analysis item {item!r}")

        for text in list(case["refs"]) + [i.get("ref", "") for i in case["analysis"]]:
            for bad in _bad_citations(str(text), articles, annexes):
                problems.append(f"{where}: cites {bad} (in {text!r})")

    return problems


# -- governance -------------------------------------------------------------
def governance_structure() -> Dict[str, Any]:
    return _guides().get("governance_structure", {})
