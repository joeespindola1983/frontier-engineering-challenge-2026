#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="replay"
ALLOW_WEATHER="1"
PRINT_PLAN="0"
API_PORT="${WAKE_API_PORT:-8788}"
WEB_PORT="${WAKE_WEB_PORT:-3000}"
COST_AUTHORIZATION_USD="${WAKE_COST_AUTHORIZATION_USD:-0.20}"
API_PID=""
WEB_PID=""

usage() {
  cat <<'EOF'
Start the WAKE product service and coach dashboard together.

Usage:
  ./scripts/start_dashboard.sh [options]

Replay mode is the default and does not call the model or incur model cost.

Options:
  --live              Enable explicit paid agent execution.
  --no-weather        Disable historical-weather enrichment.
  --api-port PORT     API port (default: 8788).
  --web-port PORT     dashboard port (default: 3000).
  --print-plan        Print the safe launch configuration and exit.
  -h, --help          Show this help.

The --live option requires OPENAI_API_KEY in the environment or the repository
.env file. Stop both services together with Ctrl+C.
EOF
}

fail() {
  printf 'WAKE launcher error: %s\n' "$1" >&2
  exit 1
}

is_port() {
  case "$1" in
    ''|*[!0-9]*) return 1 ;;
  esac
  [ "$1" -ge 1 ] && [ "$1" -le 65535 ]
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --live)
      MODE="live"
      shift
      ;;
    --no-weather)
      ALLOW_WEATHER="0"
      shift
      ;;
    --api-port)
      [ "$#" -ge 2 ] || fail "--api-port requires a value."
      API_PORT="$2"
      shift 2
      ;;
    --web-port)
      [ "$#" -ge 2 ] || fail "--web-port requires a value."
      WEB_PORT="$2"
      shift 2
      ;;
    --print-plan)
      PRINT_PLAN="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

is_port "$API_PORT" || fail "invalid API port: $API_PORT"
is_port "$WEB_PORT" || fail "invalid dashboard port: $WEB_PORT"
[ "$API_PORT" != "$WEB_PORT" ] || fail "API and dashboard ports must differ."

if [ "$MODE" = "live" ] && [ "${WAKE_SKIP_ENV_FILE:-0}" != "1" ] && [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # The repository-local file is ignored by Git and is never printed here.
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

if [ "$MODE" = "live" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
  fail "--live requires OPENAI_API_KEY in the environment or repository .env file."
fi

API_URL="http://127.0.0.1:${API_PORT}"
WEB_URL="http://localhost:${WEB_PORT}"

print_plan() {
  printf 'WAKE launch plan\n'
  if [ "$MODE" = "live" ]; then
    printf '  Mode: live (model calls can incur cost)\n'
    printf '  Cost authorization: US$%s\n' "$COST_AUTHORIZATION_USD"
  else
    printf '  Mode: replay (no model call)\n'
  fi
  if [ "$ALLOW_WEATHER" = "1" ]; then
    printf '  Weather: enabled\n'
  else
    printf '  Weather: disabled\n'
  fi
  printf '  API: %s/\n' "$API_URL"
  printf '  Dashboard: %s/\n' "$WEB_URL"
  printf '  Local state: private-data/wake-product/product-state.json\n'
}

if [ "$PRINT_PLAN" = "1" ]; then
  print_plan
  exit 0
fi

command -v curl >/dev/null 2>&1 || fail "curl is required."
UV_BIN="$(command -v uv || true)"
[ -n "$UV_BIN" ] || fail "uv is required. Install it before starting WAKE."

node_is_supported() {
  "$1" -e '
    const [major, minor] = process.versions.node.split(".").map(Number);
    process.exit(major > 22 || (major === 22 && minor >= 13) ? 0 : 1);
  ' >/dev/null 2>&1
}

find_node_bin() {
  current_node="$(command -v node || true)"
  if [ -n "$current_node" ] && node_is_supported "$current_node"; then
    dirname "$current_node"
    return 0
  fi

  for candidate in /opt/homebrew/bin/node /usr/local/bin/node; do
    if [ -x "$candidate" ] && node_is_supported "$candidate"; then
      dirname "$candidate"
      return 0
    fi
  done

  return 1
}

NODE_BIN_DIR="$(find_node_bin || true)"
[ -n "$NODE_BIN_DIR" ] || fail "Node.js 22.13 or newer is required."
[ -x "$NODE_BIN_DIR/npm" ] || fail "npm was not found beside the compatible Node.js executable."
NPM_BIN="$NODE_BIN_DIR/npm"

port_is_listening() {
  port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi
  return 1
}

port_is_listening "$API_PORT" && fail "port $API_PORT is already in use; stop the existing API or choose --api-port."
port_is_listening "$WEB_PORT" && fail "port $WEB_PORT is already in use; stop the existing dashboard or choose --web-port."

cleanup() {
  exit_code=$?
  trap - EXIT INT TERM

  if [ -n "$WEB_PID" ] && kill -0 "$WEB_PID" >/dev/null 2>&1; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "$API_PID" ] && kill -0 "$API_PID" >/dev/null 2>&1; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi

  [ -z "$WEB_PID" ] || wait "$WEB_PID" 2>/dev/null || true
  [ -z "$API_PID" ] || wait "$API_PID" 2>/dev/null || true

  if [ "$exit_code" -ne 0 ] && [ "$exit_code" -ne 130 ] && [ "$exit_code" -ne 143 ]; then
    printf 'WAKE stopped after a service error.\n' >&2
  elif [ "$exit_code" -eq 130 ] || [ "$exit_code" -eq 143 ]; then
    printf '\nWAKE services stopped.\n'
  fi
  exit "$exit_code"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

API_COMMAND=(
  "$UV_BIN" run python scripts/wake_product_service.py
  --port "$API_PORT"
  --origin "$WEB_URL"
)

if [ "$ALLOW_WEATHER" = "1" ]; then
  API_COMMAND+=(--allow-weather)
fi

if [ "$MODE" = "live" ]; then
  API_COMMAND+=(--allow-live --required-cost-authorization-usd "$COST_AUTHORIZATION_USD")
fi

print_plan
printf '\nStarting WAKE API...\n'
(
  cd "$ROOT_DIR"
  exec "${API_COMMAND[@]}"
) &
API_PID=$!

api_ready="0"
attempt="0"
while [ "$attempt" -lt 100 ]; do
  if curl --silent --show-error --fail "$API_URL/api/sessions" >/dev/null 2>&1; then
    api_ready="1"
    break
  fi
  kill -0 "$API_PID" >/dev/null 2>&1 || break
  attempt=$((attempt + 1))
  sleep 0.1
done
[ "$api_ready" = "1" ] || fail "the API did not become ready at $API_URL."

printf 'Starting WAKE dashboard...\n'
(
  cd "$ROOT_DIR/web"
  export PATH="$NODE_BIN_DIR:$PATH"
  export NEXT_PUBLIC_WAKE_API_URL="$API_URL"
  if [ "$MODE" = "live" ]; then
    export NEXT_PUBLIC_WAKE_RUNTIME_MODE="live"
    export NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD="$COST_AUTHORIZATION_USD"
  else
    export NEXT_PUBLIC_WAKE_RUNTIME_MODE="replay"
  fi
  exec "$NPM_BIN" run dev -- --port "$WEB_PORT"
) &
WEB_PID=$!

web_ready="0"
attempt="0"
while [ "$attempt" -lt 200 ]; do
  if curl --silent --show-error --fail "$WEB_URL/" >/dev/null 2>&1; then
    web_ready="1"
    break
  fi
  kill -0 "$WEB_PID" >/dev/null 2>&1 || break
  attempt=$((attempt + 1))
  sleep 0.1
done
[ "$web_ready" = "1" ] || fail "the dashboard did not become ready at $WEB_URL."

printf '\nWAKE is ready: %s/\n' "$WEB_URL"
printf 'Press Ctrl+C to stop the API and dashboard together.\n\n'

while true; do
  kill -0 "$API_PID" >/dev/null 2>&1 || fail "the API process exited unexpectedly."
  kill -0 "$WEB_PID" >/dev/null 2>&1 || fail "the dashboard process exited unexpectedly."
  sleep 1
done
