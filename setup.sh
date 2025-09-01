#!/usr/bin/env bash
# setup.sh — installateur direct sans make
set -euo pipefail

APP_DIR="/opt/ptp-diag"
WRAPPER="/usr/local/bin/ptp-diag"
SCRIPT_SRC="ptp_diag.py"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo ./setup.sh"
  exit 1
fi

command -v apt-get >/dev/null 2>&1 || { echo "apt-get not found."; exit 1; }

echo "[1/5] Installing linuxptp and python3-venv…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq linuxptp python3-venv

echo "[2/5] Checking script source…"
[[ -f "$SCRIPT_SRC" ]] || { echo "Missing $SCRIPT_SRC in current directory."; exit 1; }

echo "[3/5] Creating app directory: $APP_DIR"
mkdir -p "$APP_DIR"
install -m 0755 "$SCRIPT_SRC" "$APP_DIR/ptp_diag.py"

echo "[4/5] Creating virtualenv…"
python3 -m venv "$APP_DIR/venv"

echo "[5/5] Creating wrapper: $WRAPPER"
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
APP_DIR="/opt/ptp-diag"
exec "${APP_DIR}/venv/bin/python" "${APP_DIR}/ptp_diag.py" "$@"
EOF
chmod 0755 "$WRAPPER"

echo "[OK] Installation complete."
echo "Usage:"
echo "  sudo ptp-diag -i eth0"
echo "  sudo ptp-diag -i eth0 --json"

