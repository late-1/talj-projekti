#!/usr/bin/env bash
# Runs the tests with one command. Works on macOS and Linux.
#
# Usage:
#   ./test.sh          runs the unit tests (pytest)
#
# The tests use their own database and never touch the real one.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

# a virtual environment of another project must not confuse uv
unset VIRTUAL_ENV

echo "Installing dependencies..."
uv sync --quiet

echo "Running unit tests..."
uv run pytest src/tests
