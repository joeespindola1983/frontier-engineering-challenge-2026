#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Reproduce the public WAKE submission from a clean checkout.

Usage:
  ./scripts/reproduce_submission.sh
  ./scripts/reproduce_submission.sh --verify-only
  ./scripts/reproduce_submission.sh --help

The default installs locked Python and web dependencies, verifies every public
fixture and saved report, runs all tests, lints, and creates a production build.
Use --verify-only when dependencies are already installed.

This workflow costs US$0.00 and never calls the OpenAI API. It deliberately
ignores any local API key. Paid model re-execution is outside this script.
EOF
}

install_dependencies=true
case "${1:-}" in
  "") ;;
  --verify-only) install_dependencies=false ;;
  --help|-h) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$repo_root/.cache/uv}"

unset OPENAI_API_KEY
unset NEXT_PUBLIC_WAKE_RUNTIME_MODE
unset NEXT_PUBLIC_WAKE_API_URL

command -v uv >/dev/null || { echo "uv is required." >&2; exit 1; }
command -v node >/dev/null || { echo "Node.js is required." >&2; exit 1; }
command -v npm >/dev/null || { echo "npm is required." >&2; exit 1; }

node_version="$(node -p 'process.versions.node')"
IFS=. read -r node_major node_minor _ <<< "$node_version"
if (( node_major < 22 || (node_major == 22 && node_minor < 13) )); then
  echo "Node.js 22.13.0 or newer is required; found $node_version." >&2
  exit 1
fi

echo "WAKE public reproduction"
echo "Python requirement: 3.11+"
echo "$(uv --version)"
echo "Node v$node_version"
echo "npm $(npm --version)"

if "$install_dependencies"; then
  uv sync --frozen
  (
    cd web
    npm ci
  )
fi

uv run python scripts/test_all.py
uv run python scripts/score_longitudinal_pilot.py

(
  cd web
  npm test
  npm run lint
  npm run build
)

echo "WAKE reproduction complete."
echo "Expected fixed-case result: WAKE 83.76 / baseline 49.00."
echo 'Longitudinal pilot: 4 saved reports, US$0.110426 observed, no demonstrated quality gain.'
echo "Start the no-cost interface with ./scripts/start_dashboard.sh"
