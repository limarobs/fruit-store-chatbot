import json as _json

import httpx
import pytest

from app.services import llm

AVAILABLE = ["maca", "banana", "laranja", "uva", "abacaxi"]


@pytest.fixture
def force_ollama_enabled(monkeypatch):
    # Sob pytest a LLM fica desligada por padrao (is_ollama_enabled retorna
    # False). Aqui forcamos habilitada para exercitar o caminho da LLM.
    monkeypatch.setattr(llm, "is_ollama_enabled", lambda: True)


def _response(url, payload):
    # raise_for_status() exige um request associado ao response.
    return httpx.Response(200, json=payload, request=httpx.Request("POST", url))


def _fake_post_returning(content):
    def fake_post(url, json=None, timeout=None):
        # O Ollama devolve o texto do modelo dentro de "response" como string.
        payload = {"response": _json.dumps(content)}
        return _response(url, payload)

    return fake_post


def test_llm_extracts_intent_and_product(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(
        httpx, "post", _fake_post_returning({"intent": "quantity", "products": ["banana"]})
    )

    result = llm.interpret_question_with_llm("Tem quantas bananas?", AVAILABLE)

    assert result == {"intent": "quantity", "products": ["banana"]}


def test_llm_extracts_intent_without_products(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(
        httpx, "post", _fake_post_returning({"intent": "low_stock", "products": []})
    )

    result = llm.interpret_question_with_llm("O que esta acabando?", AVAILABLE)

    assert result == {"intent": "low_stock", "products": []}


def test_llm_normalizes_plural_and_dedupes_products(monkeypatch, force_ollama_enabled):
    # "macas" -> "maca"; duplicata de uva deve ser removida.
    monkeypatch.setattr(
        httpx,
        "post",
        _fake_post_returning({"intent": "quantity", "products": ["macas", "uva", "uva"]}),
    )

    result = llm.interpret_question_with_llm("Tem macas e uvas?", AVAILABLE)

    assert result == {"intent": "quantity", "products": ["maca", "uva"]}


def test_llm_drops_products_outside_catalog(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(
        httpx, "post", _fake_post_returning({"intent": "quantity", "products": ["manga"]})
    )

    result = llm.interpret_question_with_llm("Tem manga?", AVAILABLE)

    assert result == {"intent": "quantity", "products": []}


def test_llm_returns_none_on_invalid_intent(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(
        httpx, "post", _fake_post_returning({"intent": "sei la", "products": []})
    )

    result = llm.interpret_question_with_llm("???", AVAILABLE)

    assert result is None


def test_llm_returns_none_on_network_error(monkeypatch, force_ollama_enabled):
    def raising_post(url, json=None, timeout=None):
        raise httpx.ConnectError("ollama offline")

    monkeypatch.setattr(httpx, "post", raising_post)

    assert llm.interpret_question_with_llm("Tem uva?", AVAILABLE) is None


def test_llm_returns_none_on_invalid_json(monkeypatch, force_ollama_enabled):
    def fake_post(url, json=None, timeout=None):
        return _response(url, {"response": "isto nao e json"})

    monkeypatch.setattr(httpx, "post", fake_post)

    assert llm.interpret_question_with_llm("Tem uva?", AVAILABLE) is None


def test_llm_disabled_skips_http_call(monkeypatch):
    # Com a LLM desligada, nenhuma chamada HTTP deve acontecer.
    monkeypatch.setattr(llm, "is_ollama_enabled", lambda: False)

    def fail_post(*args, **kwargs):
        raise AssertionError("nao deveria chamar a LLM quando desligada")

    monkeypatch.setattr(httpx, "post", fail_post)

    assert llm.interpret_question_with_llm("Tem uva?", AVAILABLE) is None
