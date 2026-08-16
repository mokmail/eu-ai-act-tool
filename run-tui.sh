#!/usr/bin/env bash
#
# run-tui.sh — install the EU AI Act tool and launch the interactive TUI.
#
# Usage:
#   ./run-tui.sh
#
# Prefers uv when available; otherwise falls back to a Python venv + pip.
# All runtime dependencies (textual, httpx, chromadb) are core dependencies,
# so a plain install is enough to run the TUI.
#
set -euo pipefail

# Resolve the directory this script lives in, so it works from anywhere.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing the EU AI Act tool..."

if command -v uv >/dev/null 2>&1; then
    echo "    Using uv (uv sync)"
    uv sync
    RUN_CMD=(uv run)
else
    echo "    uv not found; using python venv + pip"
    if [ ! -d .venv ]; then
        python3 -m venv .venv
    fi
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --upgrade pip >/dev/null
    pip install -e .
    RUN_CMD=()
fi

echo "==> Starting the EU AI Act TUI..."
echo "    (press 'q' to quit)"
"${RUN_CMD[@]}" eu-ai-act-tui
