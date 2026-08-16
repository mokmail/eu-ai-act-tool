# Dataset

This repository ships two datasets:

1. **`data/raw_articles_recitals_annexes.json`** — the complete official text of the Act, extracted from EUR-Lex.
2. **`data/curated_dataset.json`** — an analytical layer encoding risk tiers, actor obligations, timeline, penalties, definitions, governance bodies, and cross-references.

Both are also bundled inside the Python package at `src/eu_ai_act/data/` so the CLI works after installation.

---

## Raw dataset schema

```jsonc
{
  "source": "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689",
  "citation": "Regulation (EU) 2024/1689 ... OJ L, 2024/1689, 12.7.2024.",
  "recitals": [
    { "number": 1, "text": "..." }   // 180 recitals
  ],
  "articles": [
    { "number": "5", "title": "Prohibited AI practices", "text": "..." }  // 113 articles
  ],
  "annexes": [
    { "number": "III", "title": "High-risk AI systems referred to in Article 6(2)", "text": "..." }  // 13 annexes
  ]
}
```

**Counts:** 180 recitals · 113 articles · 13 annexes.

---

## Curated dataset schema

```jsonc
{
  "meta": { "title", "regulation", "official_citation", "source", "published", "entered_into_force", "applies_from", "generated", "note" },
  "risk_tiers": [
    {
      "tier": "prohibited" | "high_risk" | "limited_risk" | "minimal_risk",
      "label", "summary", "legal_basis", "applies_from", "penalty",
      "practices" | "classification" | "annex_iii_areas" | "obligations"
    }
  ],
  "actors": [
    { "actor", "definition_ref", "definition", "key_obligations": [ { "ref", "obligation" } ] }
  ],
  "timeline": [ { "date", "event", "ref" } ],
  "penalties": [ { "ref", "violation", "fine", "note?" } ],
  "definitions": { "ai_system": { "ref", "definition" }, ... },
  "delegated_acts": [ { "ref", "subject" } ],
  "governance_bodies": [ { "body", "ref", "role" } ],
  "cross_references": { "gpaI_models": { "ref", "summary", "key_articles" }, ... }
}
```

---

## Provenance

The raw text is extracted from the **official EUR-Lex** HTML:

- **Source:** https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689
- **Citation:** Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024.

The extraction script is `scripts/extract_eurlex.py`. It parses the EUR-Lex HTML structure (article headings in `oj-ti-art`/`oj-sti-art` classes, recital markers in `oj-normal`, annex headings in `oj-doc-ti`).

---

## Regenerating the raw dataset

```bash
curl -sL -A "Mozilla/5.0" -o /tmp/aiact.html \
  "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
python scripts/extract_eurlex.py /tmp/aiact.html data/raw_articles_recitals_annexes.json
```

Then copy the regenerated files into the package:

```bash
cp data/raw_articles_recitals_annexes.json data/curated_dataset.json src/eu_ai_act/data/
```

---

## Programmatic access

```python
from eu_ai_act import data

data.articles()          # { "5": {...}, ... }
data.get_article("5")    # single article
data.recitals()          # { 1: {...}, ... }
data.annexes()           # { "III": {...}, ... }
data.risk_tiers()        # list of 4 tiers
data.get_actor("provider")
data.timeline()
data.penalties()
data.definitions()
data.governance_bodies()
data.cross_references()
data.citation()
```

---

## Disclaimer

This dataset is a compliance aid built on the official EUR-Lex text. It is not legal advice. Always verify against the authoritative source before making compliance decisions.
