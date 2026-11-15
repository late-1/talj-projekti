#!/usr/bin/env bash
# Runs the tests with one command. Works on macOS and Linux.
#
# Usage:
#   ./test.sh          runs unit tests and Robot Framework tests
#   ./test.sh unit     runs only the unit tests (pytest)
#   ./test.sh robot    runs only the Robot Framework tests (browser)
#
# The tests use their own databases and never touch the real one.
# Set SKIP_BROWSER_INSTALL=1 to skip installing the test browser.
set -euo pipefail

cd "$(dirname "$0")"

mode="${1:-all}"
case "$mode" in
    all|unit|robot) ;;
    *) echo "Usage: $0 [all|unit|robot]" >&2; exit 2 ;;
esac

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

# a virtual environment of another project must not confuse uv
unset VIRTUAL_ENV

export TEST_ENV=true
export SECRET_KEY=test-secret
export DATABASE_URL=sqlite:///robot_test.db
export HOST=127.0.0.1
export PORT="${PORT:-5001}"

echo "Installing dependencies..."
uv sync --quiet

if [ "$mode" != "robot" ]; then
    echo "Running unit tests..."
    uv run pytest src/tests
fi

if [ "$mode" = "unit" ]; then
    exit 0
fi

url="http://127.0.0.1:$PORT"

if curl -s -o /dev/null "$url"; then
    echo "Port $PORT is already in use. Stop the running application or set PORT." >&2
    exit 1
fi

if [ -z "${SKIP_BROWSER_INSTALL:-}" ]; then
    echo "Installing the test browser (only downloads on the first run)..."
    uv run rfbrowser install chromium
fi

echo "Creating the test database..."
uv run python src/db_helper.py

echo "Starting the application..."
.venv/bin/python src/index.py > robot_server.log 2>&1 &
server_pid=$!

stop_server() {
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
}
trap stop_server EXIT

for _ in $(seq 1 60); do
    if [ "$(curl -s -o /dev/null -w '%{http_code}' "$url/login")" = "200" ]; then
        break
    fi
    if ! kill -0 "$server_pid" 2>/dev/null; then
        echo "The application did not start:" >&2
        cat robot_server.log >&2
        exit 1
    fi
    sleep 1
done

if [ "$(curl -s -o /dev/null -w '%{http_code}' "$url/login")" != "200" ]; then
    echo "The application did not answer in $url" >&2
    cat robot_server.log >&2
    exit 1
fi

echo "Running Robot Framework tests..."
uv run robot --variable HEADLESS:true --variable "SERVER:127.0.0.1:$PORT" src/story_tests
