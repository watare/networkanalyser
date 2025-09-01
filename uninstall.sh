#!/usr/bin/env bash
# uninstall.sh — suppression propre
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "sudo required"; exit 1; }

WRAPPER="/usr/local/bin/ptp-diag"
APP_DIR="/opt/ptp-diag"
WRAPPER_IEC="/usr/local/bin/iec61850-diag"
APP_DIR_IEC="/opt/iec61850-diag"

rm -f "$WRAPPER"
rm -rf "$APP_DIR"
rm -f "$WRAPPER_IEC"
rm -rf "$APP_DIR_IEC"
echo "[OK] Uninstalled."
