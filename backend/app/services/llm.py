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

VALID_INTENTS = {
    "quantity",
    "price",
    "cheapest",
    "expensive",
    "low_stock",
    "total",
    "list",
}

_NULL_LIKE = ("", "null", "none", "nenhum", "nenhuma")


def interpret_question_with_llm(
    question: str, available_slugs: list[str]
) -> dict[str, object] | None:
    """Extrai {"intent": str, "products": [slug, ...]} da pergunta via LLM.

    Retorna None quando a LLM esta desligada, indisponivel ou responde de
    forma que nao da para interpretar - nesses casos o chamador usa o
    fallback local. A consulta real ao estoque continua sendo feita no banco.
    """
    if not is_ollama_enabled():
        return None

    prompt = build_prompt(question, available_slugs)

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

    intent = normalize_intent(content.get("intent"))
    if intent not in VALID_INTENTS:
        logger.info("LLM devolveu intent invalido: %r", content.get("intent"))
        return None

    products = resolve_products(content.get("products"), available_slugs)
    return {"intent": intent, "products": products}


def is_ollama_enabled() -> bool:
    return (
        os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
        and "PYTEST_CURRENT_TEST" not in os.environ
    )


def build_prompt(question: str, available_slugs: list[str]) -> str:
    options = ", ".join(available_slugs)

    return f"""
Voce interpreta perguntas sobre o estoque de uma loja de frutas.
Responda SOMENTE com JSON no formato {{"intent": "<intent>", "products": ["<fruta>", ...]}}.

Os intents possiveis sao:
- "quantity": quantas unidades de uma ou mais frutas existem.
- "price": qual o preco de uma fruta.
- "cheapest": qual a fruta mais barata.
- "expensive": qual a fruta mais cara.
- "low_stock": quais frutas estao acabando ou com pouco estoque.
- "total": quantidade total de frutas ou quantos tipos existem.
- "list": quais frutas a loja tem.

As frutas devem ser exatamente uma destas, sempre no singular: {options}.
Converta plural para singular (ex.: "bananas" -> "banana", "macas" -> "maca").
Em "products" liste as frutas citadas; use [] quando o intent nao precisa de
fruta ou quando nenhuma fruta da lista for citada.

Exemplos:
Pergunta: Tem quantas bananas? -> {{"intent": "quantity", "products": ["banana"]}}
Pergunta: Tem maca e uva? -> {{"intent": "quantity", "products": ["maca", "uva"]}}
Pergunta: Quanto custa a laranja? -> {{"intent": "price", "products": ["laranja"]}}
Pergunta: Qual a fruta mais barata? -> {{"intent": "cheapest", "products": []}}
Pergunta: Qual a mais cara? -> {{"intent": "expensive", "products": []}}
Pergunta: Quais frutas estao acabando? -> {{"intent": "low_stock", "products": []}}
Pergunta: Quantas frutas no total? -> {{"intent": "total", "products": []}}
Pergunta: Quais frutas voces tem? -> {{"intent": "list", "products": []}}

Pergunta: {question} ->
""".strip()


def resolve_products(value: object, available_slugs: list[str]) -> list[str]:
    """Normaliza a lista crua da LLM em slugs validos, sem duplicatas."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []

    resolved: list[str] = []
    for item in value:
        slug = match_slug(normalize_product(item), available_slugs)
        if slug is not None and slug not in resolved:
            resolved.append(slug)

    return resolved


def match_slug(product: str, available_slugs: list[str]) -> str | None:
    if product in _NULL_LIKE:
        return None
    if product in available_slugs:
        return product
    if product.endswith("s") and product[:-1] in available_slugs:
        return product[:-1]
    return None


def normalize_intent(value: object) -> str:
    if not isinstance(value, str):
        return ""

    ascii_text = _strip_accents(value).lower()
    return re.sub(r"[^a-z_]", "", ascii_text)


def normalize_product(value: object) -> str:
    if not isinstance(value, str):
        return ""

    words = re.findall(r"[a-z]+", _strip_accents(value).lower())
    return words[0] if words else ""


def _strip_accents(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return without_accents.encode("ascii", "ignore").decode("ascii")
