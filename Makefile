# Makefile — installer ptp-diag
.RECIPEPREFIX := >
SHELL := /bin/bash

PREFIX ?= /usr/local
APP_DIR ?= /opt/ptp-diag
BIN_NAME ?= ptp-diag
SCRIPT_SRC ?= ptp_diag.py
WRAPPER := $(PREFIX)/bin/$(BIN_NAME)

.PHONY: all deps install uninstall check clean

all: install

deps:
> echo "[deps] Installing linuxptp and python3-venv…"
> sudo apt-get update -qq
> sudo apt-get install -y -qq linuxptp python3-venv

install: deps
> test -f "$(SCRIPT_SRC)" || { echo "Missing $(SCRIPT_SRC)"; exit 1; }
> echo "[install] Creating app dir: $(APP_DIR)"
> sudo mkdir -p "$(APP_DIR)"
> echo "[install] Copying script"
> sudo install -m 0755 "$(SCRIPT_SRC)" "$(APP_DIR)/ptp_diag.py"
> echo "[install] Creating virtualenv"
> sudo python3 -m venv "$(APP_DIR)/venv"
> echo "[install] Generating wrapper: $(WRAPPER)"
> printf '%s\n' '#!/usr/bin/env bash' \
>   'APP_DIR="$(APP_DIR)"' \
>   'exec "$${APP_DIR}/venv/bin/python" "$${APP_DIR}/ptp_diag.py" "$$@"' \
>   | sudo tee "$(WRAPPER)" >/dev/null
> sudo chmod 0755 "$(WRAPPER)"
> echo "[ok] Installed. Usage: sudo $(BIN_NAME) -i eth0"

uninstall:
> echo "[uninstall] Removing wrapper: $(WRAPPER)"
> sudo rm -f "$(WRAPPER)"
> echo "[uninstall] Removing app dir: $(APP_DIR)"
> sudo rm -rf "$(APP_DIR)"
> echo "[ok] Uninstalled."

check:
> python3 -m py_compile $(SCRIPT_SRC)
> echo "[ok] Python syntax checks passed."

clean:
> echo "Nothing to clean."

