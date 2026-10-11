#!/bin/sh
#
# Verify the whole repo — library, AG-UI server and web client.
#
#   ./scripts/verify.sh          suites + type-check + production build
#   ./scripts/verify.sh --live   also drive a running AG-UI server end to end
#
# POSIX sh. Exits non-zero on the first failure.
#
# The production build writes to .next-verify, not .next, so this is safe to run
# while `npm run dev` is serving — a build sharing dev's directory corrupts the
# dev bundle (page 200, nothing renders).
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HERE=$(dirname -- "$0")

say() { printf '\n== %s\n' "$1"; }

say "library, CLI and TUI"
(cd "$ROOT" && uv run pytest -q)

say "AG-UI server"
(cd "$ROOT/server" && uv run pytest -q)

say "web client (type-check + production build)"
rm -rf "$ROOT/web/.next-verify"
(cd "$ROOT/web" && npx tsc --noEmit && NEXT_DIST_DIR=.next-verify npm run build)
rm -rf "$ROOT/web/.next-verify"

if [ "${1:-}" = "--live" ]; then
    say "AG-UI end to end (needs the server on :8000)"
    (cd "$ROOT/web" && node scripts/smoke-agui.mjs)
fi

printf '\n== all green\n'
