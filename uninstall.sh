#!/usr/bin/env bash
# uninstall.sh — suppression propre
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "sudo required"; exit 1; }

WRAPPER="/usr/local/bin/ptp-diag"
APP_DIR="/opt/ptp-diag"

rm -f "$WRAPPER"
rm -rf "$APP_DIR"
echo "[OK] Uninstalled."

