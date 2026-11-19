#!/usr/bin/env bash
# Starts the application with one command.
# Installs the dependencies and creates the configuration and the database
# when they are missing. Works on macOS and Linux.
#
# Usage: ./run.sh
# The port can be changed with the PORT environment variable (default 5001).
# Flask debug mode is on here (DEBUG=true); it is off unless DEBUG is set.
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

if [ ! -f .env ]; then
    echo "Creating .env..."
    secret_key="$(uv run python -c 'import secrets; print(secrets.token_hex(16))')"
    printf 'DATABASE_URL=sqlite:///database.db\nSECRET_KEY=%s\n' "$secret_key" > .env
fi

uv run python src/db_helper.py --if-missing

echo "Starting the application at http://localhost:${PORT:-5001}"
export DEBUG=true
exec uv run python src/index.py
