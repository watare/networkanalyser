#!/usr/bin/env python3
"""Simple CLI chat that loads API key from environment."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str | None:
    """Retrieve the OpenRouter API key from environment variables."""
    return os.environ.get("OPENROUTER_API_KEY")


if __name__ == "__main__":
    api_key = get_api_key()
    if api_key:
        print("API key loaded.")
    else:
        print("OPENROUTER_API_KEY is not set.")
