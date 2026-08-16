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
# The TUI is a full-screen interactive app. It needs a real terminal (a TTY)
# and a TERM that is not 'dumb'. When piped via 'curl | sh', stdin is the
# curl pipe, so we redirect the TUI's input from the controlling terminal.
can_tui() {
    [ "$TERM" != "dumb" ] && { [ -t 0 ] || [ -e /dev/tty ]; }
}

echo "==> Starting the EU AI Act TUI..."
echo "    (navigate with arrow keys, Enter to select, 'q' to quit)"
if [ -t 0 ] && [ "$TERM" != "dumb" ]; then
    $RUN eu-ai-act-tui
elif [ -e /dev/tty ] && [ "$TERM" != "dumb" ]; then
    $RUN eu-ai-act-tui < /dev/tty
else
    echo
    echo "The interactive TUI needs a real terminal and is not available here."
    echo "The tool is installed. Run it directly in a terminal with:"
    echo "  cd $INSTALL_DIR"
    echo "  $RUN eu-ai-act-tui"
    echo
    echo "Or use the command-line interface instead, e.g.:"
    echo "  $RUN eu-ai-act article 5"
    echo "  $RUN eu-ai-act search 'human oversight'"
    echo "  $RUN eu-ai-act --help"
fi
