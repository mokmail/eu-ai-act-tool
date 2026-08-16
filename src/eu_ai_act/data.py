"""
Data loading and access layer for the EU AI Act tool.

Loads the raw EUR-Lex extraction (articles, recitals, annexes) and the curated
analytical dataset (risk tiers, actors, obligations, timeline, penalties,
definitions, governance bodies, cross-references).

Every entry carries its source article reference so the tool can always cite
the legal basis.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

# Paths relative to this package.
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_PKG_DIR, "data")

# Allow overriding the data directory (useful for tests / custom datasets).
DATA_DIR = os.environ.get("EU_AI_ACT_DATA_DIR", _DATA_DIR)

RAW_JSON = os.path.join(DATA_DIR, "raw_articles_recitals_annexes.json")
CURATED_JSON = os.path.join(DATA_DIR, "curated_dataset.json")


class DataError(RuntimeError):
    """Raised when the dataset cannot be loaded."""


@lru_cache(maxsize=1)
def load_raw() -> Dict[str, Any]:
    """Load the raw EUR-Lex extraction (articles, recitals, annexes)."""
    if not os.path.exists(RAW_JSON):
        raise DataError(
            f"Raw dataset not found at {RAW_JSON}. "
            "Run `python scripts/extract_eurlex.py` to regenerate it."
        )
    with open(RAW_JSON, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_curated() -> Dict[str, Any]:
    """Load the curated analytical dataset."""
    if not os.path.exists(CURATED_JSON):
        raise DataError(f"Curated dataset not found at {CURATED_JSON}.")
    with open(CURATED_JSON, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def articles() -> Dict[str, Dict[str, Any]]:
    """Return articles keyed by number (e.g. '5', '6', '113')."""
    raw = load_raw()
    return {a["number"]: a for a in raw.get("articles", [])}


@lru_cache(maxsize=1)
def recitals() -> Dict[int, Dict[str, Any]]:
    """Return recitals keyed by number."""
    raw = load_raw()
    return {r["number"]: r for r in raw.get("recitals", [])}


@lru_cache(maxsize=1)
def annexes() -> Dict[str, Dict[str, Any]]:
    """Return annexes keyed by roman numeral (e.g. 'I', 'III')."""
    raw = load_raw()
    return {a["number"]: a for a in raw.get("annexes", [])}


def get_article(number: str) -> Optional[Dict[str, Any]]:
    """Fetch a single article by number (e.g. '5', '6a')."""
    return articles().get(str(number))


def get_recital(number: int) -> Optional[Dict[str, Any]]:
    """Fetch a single recital by number."""
    return recitals().get(int(number))


def get_annex(number: str) -> Optional[Dict[str, Any]]:
    """Fetch a single annex by roman numeral (e.g. 'III')."""
    return annexes().get(str(number).upper())


def risk_tiers() -> List[Dict[str, Any]]:
    """Return the four risk tiers (prohibited, high, limited, minimal)."""
    return load_curated().get("risk_tiers", [])


def get_risk_tier(tier: str) -> Optional[Dict[str, Any]]:
    """Fetch a single risk tier by key (prohibited/high_risk/limited_risk/minimal_risk)."""
    key = tier.lower().replace(" ", "_")
    for t in risk_tiers():
        if t["tier"] == key:
            return t
    return None


def actors() -> List[Dict[str, Any]]:
    """Return the actor types (provider, deployer, importer, etc.)."""
    return load_curated().get("actors", [])


def get_actor(actor: str) -> Optional[Dict[str, Any]]:
    """Fetch a single actor by key."""
    key = actor.lower().replace(" ", "_")
    for a in actors():
        if a["actor"] == key:
            return a
    return None


def timeline() -> List[Dict[str, Any]]:
    """Return the application timeline."""
    return load_curated().get("timeline", [])


def penalties() -> List[Dict[str, Any]]:
    """Return the penalty schedule."""
    return load_curated().get("penalties", [])


def definitions() -> Dict[str, Dict[str, Any]]:
    """Return the key definitions."""
    return load_curated().get("definitions", {})


def governance_bodies() -> List[Dict[str, Any]]:
    """Return the governance bodies."""
    return load_curated().get("governance_bodies", [])


def cross_references() -> Dict[str, Any]:
    """Return the cross-reference map."""
    return load_curated().get("cross_references", {})


def delegated_acts() -> List[Dict[str, Any]]:
    """Return the delegated acts."""
    return load_curated().get("delegated_acts", [])


def citation() -> str:
    """Return the official citation of the Regulation."""
    return load_raw().get(
        "citation",
        "Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024.",
    )
