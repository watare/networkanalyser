#!/usr/bin/env bash
# setup.sh — installateur direct sans make
set -euo pipefail

APP_DIR="/opt/ptp-diag"
WRAPPER="/usr/local/bin/ptp-diag"
SCRIPT_SRC="ptp_diag.py"

APP_DIR_IEC="/opt/iec61850-diag"
WRAPPER_IEC="/usr/local/bin/iec61850-diag"
SCRIPT_SRC_IEC="iec61850_diag.py"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo ./setup.sh"
  exit 1
fi

command -v apt-get >/dev/null 2>&1 || { echo "apt-get not found."; exit 1; }

echo "[1/8] Installing linuxptp and python3-venv…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq linuxptp python3-venv

echo "[2/8] Checking script sources…"
[[ -f "$SCRIPT_SRC" && -f "$SCRIPT_SRC_IEC" ]] || { echo "Missing scripts."; exit 1; }

echo "[3/8] Installing ptp-diag…"
mkdir -p "$APP_DIR"
install -m 0755 "$SCRIPT_SRC" "$APP_DIR/ptp_diag.py"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -r requirements.txt
cat > "$WRAPPER" <<'EOW'
#!/usr/bin/env bash
APP_DIR="/opt/ptp-diag"
exec "${APP_DIR}/venv/bin/python" "${APP_DIR}/ptp_diag.py" "$@"
EOW
chmod 0755 "$WRAPPER"

echo "[4/8] Installing IEC61850 analyzer…"
mkdir -p "$APP_DIR_IEC"
install -m 0755 "$SCRIPT_SRC_IEC" "$APP_DIR_IEC/iec61850_diag.py"
python3 -m venv "$APP_DIR_IEC/venv"
"$APP_DIR_IEC/venv/bin/pip" install -r requirements.txt
cat > "$WRAPPER_IEC" <<'EOW'
#!/usr/bin/env bash
APP_DIR="/opt/iec61850-diag"
exec "${APP_DIR}/venv/bin/python" "${APP_DIR}/iec61850_diag.py" "$@"
EOW
chmod 0755 "$WRAPPER_IEC"

echo "[5/8] Installation complete."
echo "Usage:"
echo "  sudo ptp-diag -i eth0"
echo "  sudo iec61850-diag -i eth0"
