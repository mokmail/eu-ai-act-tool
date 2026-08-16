#!/bin/sh
#
# run-tui.sh — bootstrap the EU AI Act tool and launch the interactive TUI.
#
# POSIX sh compatible, so it works whether piped to sh or bash, or run
# directly. It clones (or updates) the repository, installs the tool,
# and starts the TUI.
#
#   # Run directly from a downloaded copy:
#   curl -fsSL https://raw.githubusercontent.com/mokmail/eu-ai-act-tool/main/run-tui.sh | sh
#
#   # Or download, then run:
#   curl -fsSL -o run-tui.sh https://raw.githubusercontent.com/mokmail/eu-ai-act-tool/main/run-tui.sh
#   chmod +x run-tui.sh
#   ./run-tui.sh
#
# Install location can be overridden with EU_AI_ACT_DIR.
#
set -eu

REPO_URL="https://github.com/mokmail/eu-ai-act-tool.git"
INSTALL_DIR="${EU_AI_ACT_DIR:-$HOME/eu-ai-act-tool}"

# --- 1. Clone or update the repository -------------------------------------
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "==> Updating existing install in $INSTALL_DIR"
    # Use the HTTPS URL for pulls so no SSH key is required.
    git -C "$INSTALL_DIR" remote set-url origin "$REPO_URL"
    git -C "$INSTALL_DIR" pull --ff-only
else
    echo "==> Cloning repository into $INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --- 2. Install the tool ---------------------------------------------------
if command -v uv >/dev/null 2>&1; then
    echo "==> Installing with uv (uv sync)"
    uv sync
    RUN="uv run"
else
    echo "==> uv not found; using python venv + pip"
    if [ ! -d .venv ]; then
        python3 -m venv .venv
    fi
    # shellcheck disable=SC1091
    . .venv/bin/activate
    python -m pip install --upgrade pip >/dev/null
    pip install -e .
    RUN=""
fi

# --- 3. Launch the TUI ------------------------------------------------------
echo "==> Starting the EU AI Act TUI..."
echo "    (press 'q' to quit)"
if [ -t 0 ]; then
    # stdin is already a terminal: run normally.
    $RUN eu-ai-act-tui
elif [ -e /dev/tty ]; then
    # stdin is not a terminal (e.g. piped via 'curl | sh'), but a controlling
    # terminal exists: read keyboard input from it so the TUI is not stuck.
    $RUN eu-ai-act-tui < /dev/tty
else
    echo "ERROR: no terminal available for the interactive TUI." >&2
    echo "Run the script directly (./run-tui.sh) in a terminal instead of piping it." >&2
    exit 1
fi
