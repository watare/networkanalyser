import os
import sys

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def query_model(prompt: str) -> str:
    """Query the OpenRouter API and return the model's response.

    The API key is read from the OPENROUTER_API_KEY environment variable.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
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


if __name__ == "__main__":
    try:
        chat()
    except KeyboardInterrupt:
        print("\n[Terminé]")
        sys.exit(0)
