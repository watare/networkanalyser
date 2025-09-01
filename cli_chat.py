#!/usr/bin/env python3
"""Simple CLI to run diagnostics and fetch logs."""

import argparse
import logging
import os
import subprocess
import sys

LOG_FILE = "diagnostic.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)


def run_diagnostic(iface: str | None, duration: int | None) -> int:
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
    except Exception as exc:  # pragma: no cover - catastrophic failure
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Network diagnostic helper")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run-diagnostic", help="Run PTP diagnostic")
    run.add_argument("-i", "--interface", help="Network interface to probe")
    run.add_argument("-t", "--duration", type=int, help="Collection duration in seconds")

    sub.add_parser("logs", help="Show diagnostic logs")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run-diagnostic":
        code = run_diagnostic(args.interface, args.duration)
        sys.exit(code)
    elif args.command == "logs":
        show_logs()
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
