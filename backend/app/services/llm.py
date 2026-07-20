import json
import logging
import os
import re
import unicodedata

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def extract_product_with_llm(question: str, available_slugs: list[str]) -> str | None:
    if not is_ollama_enabled():
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
                # temperatura 0 deixa a extracao deterministica; keep_alive
                # mantem o modelo carregado e evita recarga a cada pergunta.
                "options": {"temperature": 0},
                "keep_alive": "10m",
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        content = json.loads(payload["response"])
    except (httpx.HTTPError, KeyError, json.JSONDecodeError) as error:
        # Ollama offline, lento ou fora do formato: cai no fallback local.
        logger.warning("LLM indisponivel, usando fallback local: %s", error)
        return None

    product = normalize_product(content.get("product"))

    # O modelo as vezes devolve a string "null"/"none" em vez de JSON null.
    if product in ("", "null", "none", "nenhum", "nenhuma"):
        return None

    if product in available_slugs:
        return product

    if product.endswith("s") and product[:-1] in available_slugs:
        return product[:-1]

    logger.info("LLM devolveu produto fora do catalogo: %r", product)
    return None


def is_ollama_enabled() -> bool:
    return (
        os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        and "PYTEST_CURRENT_TEST" not in os.environ
    )


def build_prompt(question: str, available_slugs: list[str]) -> str:
    options = ", ".join(available_slugs)

    return f"""
Voce identifica qual fruta aparece em uma pergunta de estoque.
Responda SOMENTE com JSON no formato {{"product": "<fruta>"}} ou {{"product": null}}.
A fruta deve ser exatamente uma destas, sempre no singular: {options}.
Converta plural para singular (ex.: "bananas" -> "banana", "macas" -> "maca").
Se nenhuma fruta da lista aparecer, use o valor JSON null (sem aspas).

Exemplos:
Pergunta: Tem quantas bananas? -> {{"product": "banana"}}
Pergunta: Quantas laranjas tem no estoque? -> {{"product": "laranja"}}
Pergunta: uva -> {{"product": "uva"}}
Pergunta: Tem quantas mangas? -> {{"product": null}}

Pergunta: {question} ->
""".strip()


def normalize_product(value: object) -> str:
    if not isinstance(value, str):
        return ""

    without_accents = unicodedata.normalize("NFKD", value)
    ascii_text = without_accents.encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z]+", ascii_text.lower())

    return words[0] if words else ""
