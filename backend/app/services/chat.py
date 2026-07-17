import re
import unicodedata

from app.database import find_product_by_slug
from app.services.llm import extract_product_with_llm

ALIASES = {
    "abacaxis": "abacaxi",
    "abacaxi": "abacaxi",
    "bananas": "banana",
    "banana": "banana",
    "laranjas": "laranja",
    "laranja": "laranja",
    "macas": "maca",
    "maca": "maca",
    "uvas": "uva",
    "uva": "uva",
}


def answer_inventory_question(question: str) -> dict[str, str | int | None]:
    llm_slug = extract_product_with_llm(question, list(ALIASES.values()))
    slug = llm_slug or extract_product_slug(question)
    interpreter = "llm" if llm_slug else "fallback"

    if slug is None:
        return {
            "answer": "Nao encontrei essa fruta no estoque. Tente perguntar por maca, banana, laranja, uva ou abacaxi.",
            "product": None,
            "quantity": None,
            "interpreter": interpreter,
        }

    product = find_product_by_slug(slug)

    if product is None:
        return {
            "answer": "Essa fruta nao esta cadastrada no estoque.",
            "product": slug,
            "quantity": None,
            "interpreter": interpreter,
        }

    quantity = int(product["quantity"])
    name = str(product["name"])

    return {
        "answer": f"Temos {quantity} unidades de {name.lower()} em estoque.",
        "product": name,
        "quantity": quantity,
        "interpreter": interpreter,
    }


def extract_product_slug(question: str) -> str | None:
    normalized_question = normalize_text(question)
    words = re.findall(r"[a-z]+", normalized_question)

    for word in words:
        if word in ALIASES:
            return ALIASES[word]

    return None


def normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    ascii_text = without_accents.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()
