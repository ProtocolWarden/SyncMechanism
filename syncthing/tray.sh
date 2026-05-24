#!/usr/bin/env bash
# Thin shim — delegates to tray.py (requires: pip install -r syncthing/requirements.txt)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/tray.py" "$@"
