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
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    # Try to load .env file from script directory first, then fallback to default
    _ENV_FILE = Path(__file__).resolve().parent / ".env"
    if not load_dotenv(_ENV_FILE):
        load_dotenv()
except ImportError:
    # If python-dotenv is not available, skip .env loading
    # Environment variables should still work
    pass

import requests

LOG_FILE = Path(__file__).resolve().parent / "diagnostic.log"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Try to setup logging, fallback to /tmp if no write permission
try:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
except PermissionError:
    # Fallback to /tmp if we can't write to script directory
    fallback_log = Path("/tmp") / "diagnostic.log" 
    logging.basicConfig(
        filename=fallback_log,
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


def get_diagnostic_context() -> str:
    """Load recent diagnostic data to provide context for analysis."""
    context_parts = []
    
    # Try to load diagnostic logs
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log_content = f.read()
                # Get last 2000 chars to avoid token limits
                if len(log_content) > 2000:
                    log_content = "..." + log_content[-2000:]
                context_parts.append(f"=== DIAGNOSTIC LOGS ===\n{log_content}")
    except Exception as e:
        context_parts.append(f"=== LOG ERROR ===\nCould not read diagnostic logs: {e}")
    
    # Try to get recent PTP diagnostic results from various locations
    ptp_log_locations = [
        Path(__file__).parent / "diagnostic.log",  # Same as LOG_FILE
        Path("/tmp/diagnostic.log"),  # Fallback location
        Path("/var/log/ptp-diag.log"),  # System log location
        Path.home() / "ptp-diagnostic.log"  # User home
    ]
    
    for log_path in ptp_log_locations:
        try:
            if log_path.exists() and log_path.stat().st_size > 0:
                with open(log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "ptp_diag" in content.lower() or "ptp" in content.lower():
                        if len(content) > 1500:
                            content = "..." + content[-1500:]
                        context_parts.append(f"=== PTP DIAGNOSTIC DATA ({log_path.name}) ===\n{content}")
                        break  # Use first found log
        except Exception:
            continue
    
    # Also try to capture live system PTP status if ptp4l/pmc available
    try:
        import subprocess
        # Try to get current PTP status
        result = subprocess.run(["pmc", "-u", "-b", "0", "GET TIME_STATUS_NP"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            context_parts.append(f"=== CURRENT PTP STATUS ===\n{result.stdout.strip()}")
    except Exception:
        pass
    
    if not context_parts:
        context_parts.append("=== NO DIAGNOSTIC DATA ===\nNo recent diagnostic data found. Run 'sudo ptp-diag -i <interface>' first to generate data for analysis.")
    
    return "\n\n".join(context_parts)


def chat() -> None:
    """Enhanced chat with automatic diagnostic context loading."""
    print("Chat CLI PTP/IEC61850 - Assistant d'analyse réseau")
    print("Chargement du contexte diagnostic...")
    
    api_key = get_api_key()
    if not api_key:
        print("OPENROUTER_API_KEY is not set.")
        return
        
    # Load diagnostic context
    diagnostic_context = get_diagnostic_context()
    print("Contexte chargé. Tapez 'exit' pour quitter, 'context' pour voir les données chargées.")
    
    # Initial context message for the AI
    system_context = f"""Tu es un expert en analyse de réseaux industriels, spécialisé en PTP (Precision Time Protocol) et IEC 61850.
    
Voici les données diagnostiques actuelles à analyser:

{diagnostic_context}

Analyse ces données et réponds aux questions de l'utilisateur en français. Si aucune donnée n'est disponible, guide l'utilisateur pour exécuter les bons diagnostics."""

    conversation_history = [{"role": "system", "content": system_context}]
    
    while True:
        try:
            prompt = input("> ")
        except EOFError:
            print()
            break
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        if prompt.strip().lower() == "context":
            print("\n" + "="*50)
            print(diagnostic_context)
            print("="*50 + "\n")
            continue
        if not prompt.strip():
            continue
            
        # Add user message to conversation
        conversation_history.append({"role": "user", "content": prompt})
        
        try:
            # Use conversation history for better context
            full_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-5:]])  # Last 5 messages
            reply = query_model(full_prompt)
            conversation_history.append({"role": "assistant", "content": reply})
        except Exception as exc:
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

