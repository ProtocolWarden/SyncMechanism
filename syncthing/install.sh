#!/usr/bin/env bash
# Thin shim — delegates to install.py (requires: pip install typer[all])
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/install.py" "$@"
