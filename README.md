# EU AI Act Tool

An exhaustive, citation-grounded tool for **navigating, understanding and applying the EU AI Act** — Regulation (EU) 2024/1689 (the Artificial Intelligence Act).

This repository ships three integrated layers:

1. **A full structured dataset** — the complete official text of the Act (180 recitals, 113 articles, 13 annexes) extracted from EUR-Lex, plus a curated analytical layer (risk tiers, actor obligations, timeline, penalties, definitions, governance bodies, cross-references).
2. **A powerful CLI** — search, risk-tier lookup, actor obligation maps, compliance checklists, timeline, penalties, definitions, and a heuristic high-risk classifier. Every output cites its legal basis.
3. **Comprehensive documentation** — risk-tier guides, actor obligation maps, compliance checklists, timeline, penalties, and a quick-start.

> **Disclaimer:** This tool is a compliance aid, not legal advice. It is built on the official EUR-Lex text of Regulation (EU) 2024/1689, but formal legal assessment is always required for definitive compliance decisions.

---

## Installation

### Prerequisites

- **Python 3.9 or newer** (3.11+ recommended). Check your version:

  ```bash
  python3 --version
  ```

- **`pip`** (Python's package installer). On most systems it ships with Python. If missing:

  ```bash
  # Debian / Ubuntu
  sudo apt install python3-pip

  # macOS (Homebrew)
  brew install python3
  ```

- **`git`** (only needed for the "install from source" methods). Check:

  ```bash
  git --version
  ```

---

### Method 1 — Install from PyPI (recommended, simplest)

If the package is published to PyPI, install it directly:

```bash
pip install eu-ai-act-tool
```

> **Note:** If this package is not yet on PyPI, use Method 2 or 3 below. (The dataset is bundled inside the package, so no extra download is needed.)

---

### Method 2 — Install from GitHub (no clone needed)

Install straight from the repository:

```bash
pip install git+https://github.com/mokmail/eu-ai-act-tool.git
```

---

### Method 3 — Clone and install in editable mode (for development)

This is the recommended approach if you want to modify the code or run the tests.

**Step 1 — Clone the repository:**

```bash
git clone https://github.com/mokmail/eu-ai-act-tool.git
cd eu-ai-act-tool
```

**Step 2 — (Recommended) Create and activate a virtual environment.**

A virtual environment keeps the tool's dependencies isolated from your system Python.

```bash
# Create the virtual environment
python3 -m venv .venv

# Activate it
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

**Step 3 — Install the package (with dev dependencies for testing):**

```bash
pip install -e ".[dev]"
```

**Step 4 — Verify the installation:**

```bash
eu-ai-act citation
```

You should see the official citation of Regulation (EU) 2024/1689. If the command is not found, make sure your virtual environment is activated (Step 2).

---

### Method 4 — Run without installing (from source)

If you prefer not to install anything, you can run the CLI directly from the source tree:

```bash
git clone https://github.com/mokmail/eu-ai-act-tool.git
cd eu-ai-act-tool
python3 -m eu_ai_act.cli citation
```

> This requires the `src/` directory to be on your `PYTHONPATH`. The simplest way is to install in editable mode (Method 3), which handles this automatically.

---

### Troubleshooting

| Problem | Fix |
|---|---|
| `eu-ai-act: command not found` | Your virtual environment isn't activated, or the install didn't complete. Re-run `source .venv/bin/activate` then `pip install -e ".[dev]"`. |
| `pip: command not found` | Install pip (see Prerequisites) or use `python3 -m pip install ...`. |
| `externally-managed-environment` error (PEP 668) | You're on a system Python that blocks pip. Use a virtual environment (Method 3, Step 2). |
| Permission errors during install | Use a virtual environment, or add `--user` to the pip command. |
| `ModuleNotFoundError: eu_ai_act` | The package isn't installed. Run `pip install -e ".[dev]"` from the repo root. |

---

## Quick start

Once installed, you can start using the tool immediately:

```bash
# Search the Act
eu-ai-act search "human oversight"

# Read a full article
eu-ai-act article 5

# Read a recital or annex
eu-ai-act recital 12
eu-ai-act annex III

# Explore a risk tier
eu-ai-act tier high_risk

# Explore an actor's obligations
eu-ai-act actor provider

# Generate a compliance checklist
eu-ai-act checklist provider

# Timeline, penalties, definitions, governance
eu-ai-act timeline
eu-ai-act penalties
eu-ai-act definitions
eu-ai-act governance
eu-ai-act crossrefs

# Heuristic high-risk classification
eu-ai-act classify "facial recognition for recruitment"

# Official citation
eu-ai-act citation
```

Every command supports `--json` for machine-readable output.

---

## What the EU AI Act is

Regulation (EU) 2024/1689 is the world's first comprehensive, horizontal legal framework for artificial intelligence. It was adopted by the European Parliament and the Council, published in the Official Journal on **12 July 2024**, entered into force on **1 August 2024**, and applies in full from **2 August 2026** (with phased application of specific chapters earlier).

It establishes a **risk-based approach** to AI regulation:

| Risk tier | Description | Applies from |
|---|---|---|
| **Prohibited** | AI practices banned outright (unacceptable risk) | 2 Feb 2025 |
| **High-risk** | AI systems subject to the most extensive obligations | 2 Aug 2026 (Art 6(1) from 2 Aug 2027) |
| **Limited-risk** | Transparency obligations (chatbots, deepfakes, etc.) | 2 Aug 2026 |
| **Minimal-risk** | No mandatory obligations; voluntary codes of conduct | Voluntary |

---

## Repository structure

```
eu-ai-act-tool/
├── data/
│   ├── raw_eurlex_32024R1689.html        # Official EUR-Lex HTML (source)
│   ├── raw_articles_recitals_annexes.json # Full text: 180 recitals, 113 articles, 13 annexes
│   └── curated_dataset.json              # Analytical layer (risk tiers, actors, timeline, penalties)
├── scripts/
│   └── extract_eurlex.py                 # Regenerate the raw dataset from EUR-Lex
├── src/eu_ai_act/
│   ├── data.py                           # Data loading & access layer
│   ├── search.py                         # Full-text search
│   ├── compliance.py                     # Obligation maps & checklists
│   └── cli.py                            # Command-line interface
├── docs/
│   ├── risk-tiers.md                     # Deep dive on the four risk tiers
│   ├── obligations.md                    # Actor-by-actor obligation map
│   ├── compliance-checklist.md           # Step-by-step compliance guide
│   ├── timeline.md                       # Application timeline
│   ├── penalties.md                     # Penalty schedule
│   └── dataset.md                        # Dataset schema & provenance
├── tests/                                # 38 tests
└── pyproject.toml
```

---

## Documentation

- [Risk tiers](docs/risk-tiers.md) — the four-tier risk framework in depth.
- [Obligations by actor](docs/obligations.md) — who must do what, with citations.
- [Compliance checklist](docs/compliance-checklist.md) — a step-by-step path to compliance.
- [Timeline](docs/timeline.md) — when each provision applies.
- [Penalties](docs/penalties.md) — the fine schedule.
- [Dataset](docs/dataset.md) — schema, provenance, and how to regenerate.

---

## Data provenance

The full legal text is extracted from the **official EUR-Lex** source:

- **Source:** https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689
- **Citation:** Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act), OJ L, 2024/1689, 12.7.2024.

To regenerate the raw dataset from a fresh EUR-Lex download:

```bash
curl -sL -A "Mozilla/5.0" -o /tmp/aiact.html \
  "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32024R1689"
python scripts/extract_eurlex.py /tmp/aiact.html data/raw_articles_recitals_annexes.json
```

---

## Development

```bash
# Run tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=eu_ai_act
```

---

## License

MIT. See [LICENSE](LICENSE).

---

## Author

Mohammed Kmail — [kmail.at](https://kmail.at)
