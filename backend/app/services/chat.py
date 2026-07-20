import re
import unicodedata

from app.database import find_product_by_slug, list_products
from app.services.llm import interpret_question_with_llm

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

CATALOG_SLUGS = list(dict.fromkeys(ALIASES.values()))

# Frutas abaixo desta quantidade sao consideradas "acabando".
LOW_STOCK_THRESHOLD = 20

_UNKNOWN_FRUIT = (
    "Nao encontrei essa fruta no estoque. "
    "Tente perguntar por maca, banana, laranja, uva ou abacaxi."
)


def answer_inventory_question(question: str) -> dict[str, str | int | None]:
    interpretation = interpret_question_with_llm(question, CATALOG_SLUGS)

    if interpretation is not None:
        interpreter = "llm"
    else:
        interpretation = interpret_question_fallback(question)
        interpreter = "fallback"

    intent = str(interpretation["intent"])
    products = list(interpretation["products"])

    builder = _INTENT_BUILDERS.get(intent, _answer_quantity)
    response = builder(products)
    response["intent"] = intent
    response["interpreter"] = interpreter
    return response


# --- construtores de resposta por intencao -------------------------------

def _answer_quantity(slugs: list[str]) -> dict[str, str | int | None]:
    if not slugs:
        return _response(_UNKNOWN_FRUIT)

    if len(slugs) == 1:
        product = find_product_by_slug(slugs[0])
        if product is None:
            return _response(
                "Essa fruta nao esta cadastrada no estoque.", product=slugs[0]
            )
        quantity = int(product["quantity"])
        name = str(product["name"])
        return _response(
            f"Temos {quantity} unidades de {name.lower()} em estoque.",
            product=name,
            quantity=quantity,
        )

    parts = []
    for slug in slugs:
        product = find_product_by_slug(slug)
        if product is not None:
            parts.append(f"{int(product['quantity'])} de {str(product['name']).lower()}")

    if not parts:
        return _response(_UNKNOWN_FRUIT)

    return _response(f"Temos {_join_natural(parts)} em estoque.")


def _answer_price(slugs: list[str]) -> dict[str, str | int | None]:
    if not slugs:
        return _response(
            "Sobre qual fruta voce quer saber o preco? "
            "Ex.: maca, banana, laranja, uva ou abacaxi."
        )

    parts = []
    for slug in slugs:
        product = find_product_by_slug(slug)
        if product is not None:
            name = str(product["name"]).lower()
            parts.append(f"a {name} custa {_format_price(int(product['price_cents']))}")

    if not parts:
        return _response("Essa fruta nao esta cadastrada no estoque.", product=slugs[0])

    sentence = _join_natural(parts)
    if len(slugs) == 1:
        product = find_product_by_slug(slugs[0])
        return _response(
            f"{sentence[0].upper()}{sentence[1:]} a unidade.",
            product=str(product["name"]),
        )

    return _response(f"{sentence[0].upper()}{sentence[1:]} a unidade.")


def _answer_cheapest(_slugs: list[str]) -> dict[str, str | int | None]:
    return _answer_price_extreme(cheapest=True)


def _answer_expensive(_slugs: list[str]) -> dict[str, str | int | None]:
    return _answer_price_extreme(cheapest=False)


def _answer_price_extreme(cheapest: bool) -> dict[str, str | int | None]:
    products = list_products()
    if not products:
        return _response("Nao ha frutas cadastradas no estoque.")

    chosen = (min if cheapest else max)(products, key=lambda p: int(p["price_cents"]))
    name = str(chosen["name"])
    label = "mais barata" if cheapest else "mais cara"
    price = _format_price(int(chosen["price_cents"]))
    return _response(
        f"A fruta {label} e a {name.lower()}, a {price} a unidade.",
        product=name,
    )


def _answer_low_stock(_slugs: list[str]) -> dict[str, str | int | None]:
    low = [p for p in list_products() if int(p["quantity"]) < LOW_STOCK_THRESHOLD]
    low.sort(key=lambda p: int(p["quantity"]))

    if not low:
        return _response("Nenhuma fruta esta com estoque baixo no momento.")

    parts = [f"{str(p['name']).lower()} ({int(p['quantity'])} unidades)" for p in low]
    return _response(f"Estao acabando: {_join_natural(parts)}.")


def _answer_total(_slugs: list[str]) -> dict[str, str | int | None]:
    products = list_products()
    total_units = sum(int(p["quantity"]) for p in products)
    types = len(products)
    return _response(
        f"Temos {total_units} unidades no total, distribuidas em {types} tipos de fruta.",
        quantity=total_units,
    )


def _answer_list(_slugs: list[str]) -> dict[str, str | int | None]:
    names = [str(p["name"]).lower() for p in list_products()]
    if not names:
        return _response("Nao ha frutas cadastradas no estoque.")
    return _response(f"Temos estas frutas: {_join_natural(names)}.")


_INTENT_BUILDERS = {
    "quantity": _answer_quantity,
    "price": _answer_price,
    "cheapest": _answer_cheapest,
    "expensive": _answer_expensive,
    "low_stock": _answer_low_stock,
    "total": _answer_total,
    "list": _answer_list,
}


# --- fallback deterministico ---------------------------------------------

def interpret_question_fallback(question: str) -> dict[str, object]:
    normalized = normalize_text(question)
    return {
        "intent": detect_intent_fallback(normalized),
        "products": extract_products_fallback(normalized),
    }


def detect_intent_fallback(normalized: str) -> str:
    if "mais barat" in normalized:
        return "cheapest"
    if "mais car" in normalized:
        return "expensive"
    if any(k in normalized for k in ("quanto custa", "preco", "valor", "custa")):
        return "price"
    if any(k in normalized for k in ("acaband", "acabar", "acabou", "pouco", "baixo", "faltando", "falta")):
        return "low_stock"
    if "total" in normalized or "quantos tipos" in normalized:
        return "total"
    if any(k in normalized for k in ("quais frutas", "que frutas", "quais voces", "lista", "listar", "catalogo")):
        return "list"
    return "quantity"


def extract_products_fallback(normalized: str) -> list[str]:
    found: list[str] = []
    for word in re.findall(r"[a-z]+", normalized):
        slug = ALIASES.get(word)
        if slug is not None and slug not in found:
            found.append(slug)
    return found


def extract_product_slug(question: str) -> str | None:
    products = extract_products_fallback(normalize_text(question))
    return products[0] if products else None


def normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    ascii_text = without_accents.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


# --- helpers -------------------------------------------------------------

def _response(
    answer: str, product: str | None = None, quantity: int | None = None
) -> dict[str, str | int | None]:
    return {"answer": answer, "product": product, "quantity": quantity}


def _format_price(cents: int) -> str:
    return f"R$ {cents // 100},{cents % 100:02d}"


def _join_natural(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} e {items[-1]}"
