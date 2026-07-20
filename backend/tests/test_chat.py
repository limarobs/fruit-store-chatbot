from app.services import chat


def test_normalize_text_removes_accents_and_lowercases():
    assert chat.normalize_text("Maçã") == "maca"
    assert chat.normalize_text("ABACAXI") == "abacaxi"


def test_extract_product_slug_matches_plural_alias():
    assert chat.extract_product_slug("Tem quantas bananas?") == "banana"


def test_extract_product_slug_returns_none_for_unknown_fruit():
    assert chat.extract_product_slug("Tem manga?") is None


# --- roteamento por intencao (via fallback deterministico) ---------------

def test_fallback_detects_intents():
    detect = chat.detect_intent_fallback
    assert detect(chat.normalize_text("Tem quantas macas?")) == "quantity"
    assert detect(chat.normalize_text("Quanto custa a banana?")) == "price"
    assert detect(chat.normalize_text("Qual a mais barata?")) == "cheapest"
    assert detect(chat.normalize_text("Qual a mais cara?")) == "expensive"
    assert detect(chat.normalize_text("Quais frutas estao acabando?")) == "low_stock"
    assert detect(chat.normalize_text("Quantas frutas no total?")) == "total"
    assert detect(chat.normalize_text("Quais frutas voces tem?")) == "list"


def test_answer_multiple_products_in_one_question():
    result = chat.answer_inventory_question("Tem maca e uva?")

    assert result["intent"] == "quantity"
    assert "42 de maca" in result["answer"]
    assert "18 de uva" in result["answer"]


def test_answer_price_question():
    result = chat.answer_inventory_question("Quanto custa a uva?")

    assert result["intent"] == "price"
    assert result["product"] == "Uva"
    assert "R$ 8,90" in result["answer"]


def test_answer_cheapest_question():
    result = chat.answer_inventory_question("Qual a fruta mais barata?")

    assert result["intent"] == "cheapest"
    assert result["product"] == "Laranja"


def test_answer_low_stock_lists_only_scarce_fruits():
    result = chat.answer_inventory_question("O que esta acabando?")

    assert result["intent"] == "low_stock"
    assert "abacaxi" in result["answer"]
    assert "uva" in result["answer"]
    assert "maca" not in result["answer"]


def test_answer_total_returns_sum_and_types():
    result = chat.answer_inventory_question("Quantas frutas no total?")

    assert result["intent"] == "total"
    assert result["quantity"] == 127
    assert "5 tipos" in result["answer"]


# --- integracao com a camada de LLM (mockada) ----------------------------

def test_answer_uses_llm_interpreter_when_llm_resolves(monkeypatch):
    # Simula a LLM interpretando a pergunta; o interpreter deve ser "llm".
    monkeypatch.setattr(
        chat,
        "interpret_question_with_llm",
        lambda q, slugs: {"intent": "quantity", "products": ["uva"]},
    )

    result = chat.answer_inventory_question("qualquer coisa")

    assert result["interpreter"] == "llm"
    assert result["product"] == "Uva"
    assert result["quantity"] == 18


def test_answer_falls_back_when_llm_returns_none(monkeypatch):
    monkeypatch.setattr(chat, "interpret_question_with_llm", lambda q, slugs: None)

    result = chat.answer_inventory_question("Tem quantas macas?")

    assert result["interpreter"] == "fallback"
    assert result["product"] == "Maca"


def test_answer_handles_slug_not_in_database(monkeypatch):
    # Intent resolvido, mas a fruta nao existe no banco: caminho
    # "essa fruta nao esta cadastrada".
    monkeypatch.setattr(
        chat,
        "interpret_question_with_llm",
        lambda q, slugs: {"intent": "quantity", "products": ["kiwi"]},
    )

    result = chat.answer_inventory_question("Tem kiwi?")

    assert result["product"] == "kiwi"
    assert result["quantity"] is None
    assert "nao esta cadastrada" in result["answer"]
