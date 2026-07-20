from app.services import chat


def test_normalize_text_removes_accents_and_lowercases():
    assert chat.normalize_text("Maçã") == "maca"
    assert chat.normalize_text("ABACAXI") == "abacaxi"


def test_extract_product_slug_matches_plural_alias():
    assert chat.extract_product_slug("Tem quantas bananas?") == "banana"


def test_extract_product_slug_returns_none_for_unknown_fruit():
    assert chat.extract_product_slug("Tem manga?") is None


def test_answer_uses_llm_interpreter_when_llm_resolves(monkeypatch):
    # Simula a LLM resolvendo o produto; o interpreter deve ser "llm".
    monkeypatch.setattr(chat, "extract_product_with_llm", lambda q, slugs: "uva")

    result = chat.answer_inventory_question("qualquer coisa")

    assert result["interpreter"] == "llm"
    assert result["product"] == "Uva"
    assert result["quantity"] == 18


def test_answer_falls_back_when_llm_returns_none(monkeypatch):
    monkeypatch.setattr(chat, "extract_product_with_llm", lambda q, slugs: None)

    result = chat.answer_inventory_question("Tem quantas macas?")

    assert result["interpreter"] == "fallback"
    assert result["product"] == "Maca"


def test_answer_handles_slug_not_in_database(monkeypatch):
    # Slug valido resolvido pela LLM, mas ausente do banco: caminho
    # "essa fruta nao esta cadastrada".
    monkeypatch.setattr(chat, "extract_product_with_llm", lambda q, slugs: "kiwi")

    result = chat.answer_inventory_question("Tem kiwi?")

    assert result["product"] == "kiwi"
    assert result["quantity"] is None
    assert "nao esta cadastrada" in result["answer"]
