# ai-service/ollama_client.py

import os
import requests
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")


def chat_once(prompt: str, model: str = "llama3.2") -> str:
    """Send prompt to Ollama and get response"""
    logger.info(f"Sending prompt to Ollama (model: {model})")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()

        if "response" not in data:
            raise RuntimeError(f"Unexpected Ollama response: {data}")

        logger.info("✅ Got response from Ollama")
        return data["response"]
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_URL}")
        raise RuntimeError(f"Ollama service not available: {e}")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        raise

