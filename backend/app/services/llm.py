import json
import os
import re
import unicodedata

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"


def extract_product_with_llm(question: str, available_slugs: list[str]) -> str | None:
    if not OLLAMA_ENABLED:
        return None

    prompt = build_prompt(question, available_slugs)

    # Usa a LLM local apenas para extrair a fruta da pergunta.
    # A consulta real ao estoque continua sendo feita no banco SQLite.
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        content = json.loads(payload["response"])
    except (httpx.HTTPError, KeyError, json.JSONDecodeError):
        return None

    product = normalize_product(content.get("product"))

    if product in available_slugs:
        return product

    if product.endswith("s") and product[:-1] in available_slugs:
        return product[:-1]

    return None


def build_prompt(question: str, available_slugs: list[str]) -> str:
    options = ", ".join(available_slugs)

    return f"""
Voce interpreta perguntas de estoque de uma loja de frutas.
Retorne apenas JSON valido no formato {{"product": string | null}}.
Use apenas uma destas frutas: {options}.
Se a pergunta for apenas o nome de uma fruta, com ou sem pontuacao, retorne essa fruta.
Se a pergunta nao mencionar uma fruta da lista, use null.

Pergunta: {question}
""".strip()


def normalize_product(value: object) -> str:
    if not isinstance(value, str):
        return ""

    without_accents = unicodedata.normalize("NFKD", value)
    ascii_text = without_accents.encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z]+", ascii_text.lower())

    return words[0] if words else ""
