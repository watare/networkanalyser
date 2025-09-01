#!/usr/bin/env python3
"""Unified CLI: PTP diagnostics + OpenRouter chat.

Subcommands:
  - run-diagnostic  : run ptp_diag.py with optional interface and duration
  - logs            : print diagnostic.log
  - chat            : simple REPL using OpenRouter API
  - check-key       : verify OPENROUTER_API_KEY availability
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from typing import Optional

from dotenv import load_dotenv
import requests

# ---------- Environment / constants ----------

load_dotenv()

LOG_FILE = "diagnostic.log"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


# ---------- Helpers ----------

def get_api_key() -> Optional[str]:
    """Retrieve the OpenRouter API key from environment variables."""
    return os.environ.get("OPENROUTER_API_KEY")


# ---------- PTP diagnostic ----------

def run_diagnostic(iface: Optional[str], duration: Optional[int]) -> int:
    """Run the ptp diagnostic script with optional arguments."""
    script = os.path.join(os.path.dirname(__file__), "ptp_diag.py")
    cmd = [sys.executable, script]
    if iface:
        cmd.extend(["-i", iface])
    if duration is not None:
        cmd.extend(["-t", str(duration)])

    logging.info("Executing: %s", " ".join(cmd))
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            print(res.stdout, end="")
            logging.info("stdout: %s", res.stdout.strip())
        if res.stderr:
            print(res.stderr, end="", file=sys.stderr)
            logging.error("stderr: %s", res.stderr.strip())
        logging.info("Return code: %s", res.returncode)
        return res.returncode
    except Exception as exc:  # pragma: no cover
        logging.exception("Diagnostic failed: %s", exc)
        print(f"Error running diagnostic: {exc}", file=sys.stderr)
        return 1


def show_logs() -> None:
    """Print the content of the log file."""
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        print("No logs available.", file=sys.stderr)
        return
    with open(LOG_FILE, "r", encoding="utf-8") as fh:
        print(fh.read())


# ---------- OpenRouter chat ----------

def query_model(prompt: str) -> str:
    """Query the OpenRouter API and return the model's response.

    The API key is read from the OPENROUTER_API_KEY environment variable.
    """
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("Variable d'environnement OPENROUTER_API_KEY non définie")

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("La requête a expiré") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Erreur réseau: {exc}") from exc

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Réponse inattendue de l'API") from exc


def chat() -> None:
    """Simple REPL for chatting with the model."""
    print("Chat CLI. Tapez 'exit' pour quitter.")
    api_key = get_api_key()
    print("API key loaded." if api_key else "OPENROUTER_API_KEY is not set.")
    while True:
        try:
            prompt = input("> ")
        except EOFError:
            print()
            break
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        if not prompt.strip():
            continue
        try:
            reply = query_model(prompt)
        except Exception as exc:  # noqa: BLE001
            print(f"[Erreur] {exc}")
            continue
        print(reply)


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Network diagnostic & chat helper")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run-diagnostic", help="Run PTP diagnostic")
    run.add_argument("-i", "--interface", help="Network interface to probe")
    run.add_argument("-t", "--duration", type=int, help="Collection duration in seconds")

    sub.add_parser("logs", help="Show diagnostic logs")
    sub.add_parser("chat", help="OpenRouter chat REPL")
    sub.add_parser("check-key", help="Check OPENROUTER_API_KEY presence")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run-diagnostic":
        code = run_diagnostic(args.interface, args.duration)
        sys.exit(code)
    elif args.command == "logs":
        show_logs()
    elif args.command == "chat":
        chat()
    elif args.command == "check-key":
        print("API key loaded." if get_api_key() else "OPENROUTER_API_KEY is not set.")
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()

