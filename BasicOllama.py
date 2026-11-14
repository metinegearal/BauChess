"""Optional local LLM experiment; not part of the scheduled pipeline."""

import json
import os

import requests
import config  # Loads the project's .env before reading settings.


def llmZeroShot(data):
    with requests.post(
        os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate"),
        json={"model": os.getenv("OLLAMA_MODEL", "gemma3:12b"), "prompt": data},
        stream=True,
        timeout=(10, 300),
    ) as response:
        response.raise_for_status()
        return "".join(
            json.loads(line).get("response", "")
            for line in response.iter_lines() if line
        )


if __name__ == "__main__":
    print(llmZeroShot("Explain the importance of king safety in chess."))
