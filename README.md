# EU AI Act Tool

An exhaustive, citation-grounded tool for **navigating, understanding and applying the EU AI Act** — Regulation (EU) 2024/1689 (the Artificial Intelligence Act).

This repository ships five integrated layers:

1. **A full structured dataset** — the complete official text of the Act (180 recitals, 113 articles, 13 annexes) extracted from EUR-Lex, plus a curated analytical layer (risk tiers, actor obligations, timeline, penalties, definitions, governance bodies, cross-references).
2. **A powerful CLI** — search, risk-tier lookup, actor obligation maps, compliance checklists, timeline, penalties, definitions, and a heuristic high-risk classifier. Every output cites its legal basis.
3. **An interactive TUI** — a menu-driven, arrow-key-navigable browser built on Textual.
4. **An AI assistant** — natural-language interaction with the Act (ask, summarize, list, compare, explain) via local Ollama, grounded in a hardened ChromaDB vector store.
5. **Comprehensive documentation** — risk-tier guides, actor obligation maps, compliance checklists, timeline, penalties, and a quick-start.

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

### Using `uv` (fast, modern alternative)

This project is `uv`-compatible and ships a `uv.lock` for reproducible installs. If you use [uv](https://docs.astral.sh/uv/):

```bash
# Install the project and its dev dependencies from the lockfile
uv sync

# Run the CLI
uv run eu-ai-act citation

# Run the tests
uv run pytest
```

To add the tool to an existing `uv` project (from the git repo, since it is not yet on PyPI):

```bash
uv add "eu-ai-act-tool @ git+https://github.com/mokmail/eu-ai-act-tool.git"
uv run eu-ai-act citation
```

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

## Interactive TUI

For a menu-driven, arrow-key-navigable browser, use the built-in **TUI** (built on [Textual](https://textual.textualize.io/)):

```bash
# Install with the TUI extra
pip install -e ".[tui]"
# or with uv
uv sync --extra tui

# Launch the TUI
eu-ai-act-tui
```

The TUI gives you a home menu with 14 sections — search, articles, recitals, annexes, risk tiers, actors, compliance checklists, timeline, penalties, definitions, governance bodies, cross-references, the official citation, and the AI Assistant. Navigate with **arrow keys**, select with **Enter**, go back with **Esc**, and quit with **q**.

> **Note:** The TUI requires a terminal that supports full-screen interactive apps (not a plain piped/CI environment).

---

## AI Assistant (local Ollama)

The tool includes an **AI-powered assistant** that lets you interact with the EU AI Act in natural language — ask questions, summarize provisions, list obligations, compare concepts, and more. It uses **local Ollama** by default (fully private, no data leaves your machine), with a **hardened ChromaDB vector store** for semantic retrieval over the full Act.

### Setup

1. **Install with the AI extra:**
   ```bash
   pip install -e ".[ai]"
   # or with uv
   uv sync --extra ai
   ```

2. **Ensure Ollama is running** and has the embedding model:
   ```bash
   ollama serve
   ollama pull nomic-embed-text
   ```

3. **Build the vector store** (embeds the full Act — 488 chunks):
   ```bash
   eu-ai-act ai embed
   ```

4. **Check status:**
   ```bash
   eu-ai-act ai status
   ```

### Usage

```bash
# Ask a question (grounded in the Act, with citations)
eu-ai-act ai ask "What are the prohibited AI practices?"

# Summarize a provision or topic
eu-ai-act ai summarize "Article 5"
eu-ai-act ai summarize "high-risk obligations"

# List obligations on a topic
eu-ai-act ai list "data governance requirements"

# Compare two provisions or concepts
eu-ai-act ai compare "provider" "deployer"

# List obligations for an actor or tier
eu-ai-act ai obligations --actor provider
eu-ai-act ai obligations --tier high_risk

# Plain-language explanation of a provision
eu-ai-act ai explain "Article 5"

# Manage the provider
eu-ai-act ai models          # list available models
eu-ai-act ai config --chat-model "deepseek-v4-flash:0731-cloud"
eu-ai-act ai status          # provider + vector store status
```

### Configuration

The AI provider is configured via `~/.config/eu-ai-act/provider.json`:

```json
{
  "base_url": "http://localhost:11434/v1",
  "chat_model": "deepseek-v4-flash:0731-cloud",
  "embed_model": "nomic-embed-text:latest",
  "api_key": null,
  "timeout": 120
}
```

- **Default:** local Ollama (`http://localhost:11434/v1`), fully private.
- **Ollama Cloud:** if you're logged into Ollama Cloud, the same endpoint can reach cloud models (e.g. `gemini-3-flash-preview`, `mistral-large-3:675b-cloud`). Just set the `chat_model` to a cloud model.
- **Other providers:** set `base_url` to any OpenAI-compatible endpoint and provide an `api_key` if required.

### In the TUI

The TUI has an **AI Assistant** screen (menu item 14) — type a question, press Enter, and get a grounded answer with sources.

> **Note:** The AI features require Ollama to be running. The vector store is built once and reused (hardened, persistent) — queries do not recompute embeddings.

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
│   ├── cli.py                            # Command-line interface
│   ├── tui.py                            # Interactive TUI (Textual)
│   ├── ai_provider.py                    # AI provider abstraction (Ollama default)
│   ├── ai_rag.py                         # RAG + natural-language capabilities
│   └── vector_store.py                   # Hardened ChromaDB vector store
├── docs/
│   ├── risk-tiers.md                     # Deep dive on the four risk tiers
│   ├── obligations.md                    # Actor-by-actor obligation map
│   ├── compliance-checklist.md           # Step-by-step compliance guide
│   ├── timeline.md                       # Application timeline
│   ├── penalties.md                     # Penalty schedule
│   └── dataset.md                        # Dataset schema & provenance
├── tests/                                # 52 tests
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

The project uses [uv](https://docs.astral.sh/uv/) for dependency management and a `uv.lock` for reproducible installs.

```bash
# Install the project + all extras (dev, tui, ai) from the lockfile
uv sync --all-extras

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=eu_ai_act

# Run the CLI
uv run eu-ai-act citation

# Run the TUI
uv run eu-ai-act-tui
```

> **Note:** The AI tests that hit a live model require Ollama to be running. The unit tests (52 total) run without it.

---

## License

MIT. See [LICENSE](LICENSE).

---

## Author

Mohammed Kmail — [kmail.at](https://kmail.at)
