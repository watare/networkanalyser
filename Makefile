# Makefile — installer ptp-diag and IEC61850 analyzer
.RECIPEPREFIX := >
SHELL := /bin/bash

PREFIX ?= /usr/local
PYTHON ?= python3

APP_DIR ?= /opt/ptp-diag
BIN_NAME ?= ptp-diag
SCRIPT_SRC ?= ptp_diag.py
WRAPPER := $(PREFIX)/bin/$(BIN_NAME)
LOGS_WRAPPER := $(PREFIX)/bin/ptp-logs
CHAT_WRAPPER := $(PREFIX)/bin/ptp-chat

APP_DIR_IEC ?= /opt/iec61850-diag
BIN_NAME_IEC ?= iec61850-diag
SCRIPT_SRC_IEC ?= iec61850_diag.py
WRAPPER_IEC := $(PREFIX)/bin/$(BIN_NAME_IEC)

.PHONY: all deps install uninstall check clean run-diagnostic logs chat check-key

all: install

deps:
> echo "[deps] Installing linuxptp and python3-venv…"
> sudo apt-get update -qq
> sudo apt-get install -y -qq linuxptp python3-venv

install: deps
> for f in $(SCRIPT_SRC) $(SCRIPT_SRC_IEC) cli_chat.py; do \
>   test -f "$$f" || { echo "Missing $$f"; exit 1; }; \
> done
> echo "[install] Creating app dir: $(APP_DIR)"
> sudo mkdir -p "$(APP_DIR)"
> echo "[install] Copying ptp script"
> sudo install -m 0755 "$(SCRIPT_SRC)" "$(APP_DIR)/ptp_diag.py"
> echo "[install] Copying chat helper"
> sudo install -m 0755 cli_chat.py "$(APP_DIR)/cli_chat.py"
> echo "[install] Creating virtualenv for ptp"
> sudo $(PYTHON) -m venv "$(APP_DIR)/venv"
> echo "[install] Installing Python deps"
> sudo "$(APP_DIR)/venv/bin/pip" install -r requirements.txt
> echo "[install] Generating wrapper: $(WRAPPER)"
> printf '%s\n' '#!/usr/bin/env bash' \
>   'APP_DIR="$(APP_DIR)"' \
>   'exec "$$APP_DIR/venv/bin/python" "$$APP_DIR/ptp_diag.py" "$$@"' \
>   | sudo tee "$(WRAPPER)" >/dev/null
> sudo chmod 0755 "$(WRAPPER)"
> echo "[install] Generating wrapper: $(LOGS_WRAPPER)"
> printf '%s\n' '#!/usr/bin/env bash' \
>   'APP_DIR="$(APP_DIR)"' \
>   'exec "$$APP_DIR/venv/bin/python" "$$APP_DIR/cli_chat.py" logs "$$@"' \
>   | sudo tee "$(LOGS_WRAPPER)" >/dev/null
> sudo chmod 0755 "$(LOGS_WRAPPER)"
> echo "[install] Generating wrapper: $(CHAT_WRAPPER)"
> printf '%s\n' '#!/usr/bin/env bash' \
>   'APP_DIR="$(APP_DIR)"' \
>   'exec "$$APP_DIR/venv/bin/python" "$$APP_DIR/cli_chat.py" chat "$$@"' \
>   | sudo tee "$(CHAT_WRAPPER)" >/dev/null
> sudo chmod 0755 "$(CHAT_WRAPPER)"
> echo "[install] Creating app dir: $(APP_DIR_IEC)"
> sudo mkdir -p "$(APP_DIR_IEC)"
> echo "[install] Copying IEC61850 script"
> sudo install -m 0755 "$(SCRIPT_SRC_IEC)" "$(APP_DIR_IEC)/iec61850_diag.py"
> echo "[install] Creating virtualenv for IEC61850"
> sudo $(PYTHON) -m venv "$(APP_DIR_IEC)/venv"
> echo "[install] Installing Python deps"
> sudo "$(APP_DIR_IEC)/venv/bin/pip" install -r requirements.txt
> echo "[install] Generating wrapper: $(WRAPPER_IEC)"
> printf '%s\n' '#!/usr/bin/env bash' \
>   'APP_DIR="$(APP_DIR_IEC)"' \
>   'exec "$$APP_DIR/venv/bin/python" "$$APP_DIR/iec61850_diag.py" "$$@"' \
>   | sudo tee "$(WRAPPER_IEC)" >/dev/null
> sudo chmod 0755 "$(WRAPPER_IEC)"
> echo "[ok] Installed. Usage: sudo $(BIN_NAME) -i eth0 | sudo $(BIN_NAME_IEC) -i eth0"

uninstall:
> echo "[uninstall] Removing wrapper: $(WRAPPER)"
> sudo rm -f "$(WRAPPER)"
> echo "[uninstall] Removing wrapper: $(LOGS_WRAPPER)"
> sudo rm -f "$(LOGS_WRAPPER)"
> echo "[uninstall] Removing wrapper: $(CHAT_WRAPPER)"
> sudo rm -f "$(CHAT_WRAPPER)"
> echo "[uninstall] Removing app dir: $(APP_DIR)"
> sudo rm -rf "$(APP_DIR)"
> echo "[uninstall] Removing wrapper: $(WRAPPER_IEC)"
> sudo rm -f "$(WRAPPER_IEC)"
> echo "[uninstall] Removing app dir: $(APP_DIR_IEC)"
> sudo rm -rf "$(APP_DIR_IEC)"
> echo "[ok] Uninstalled."

check:
> $(PYTHON) -m py_compile $(SCRIPT_SRC) $(SCRIPT_SRC_IEC) cli_chat.py
> echo "[ok] Python syntax checks passed."

clean:
> echo "Nothing to clean."

# IFACE et DURATION sont optionnelles
run-diagnostic:
> $(PYTHON) cli_chat.py run-diagnostic IFACE=$(IFACE) DURATION=$(DURATION)

logs:
> $(PYTHON) cli_chat.py logs

chat:
> $(PYTHON) cli_chat.py chat

check-key:
> $(PYTHON) cli_chat.py check-key
