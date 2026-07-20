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


def _fake_post_returning(product):
    def fake_post(url, json=None, timeout=None):
        # O Ollama devolve o texto do modelo dentro de "response" como string.
        payload = {"response": _json.dumps({"product": product})}
        return _response(url, payload)

    return fake_post


def test_llm_extracts_known_product(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(httpx, "post", _fake_post_returning("banana"))

    result = llm.extract_product_with_llm("Tem quantas bananas?", AVAILABLE)

    assert result == "banana"


def test_llm_normalizes_plural_to_singular(monkeypatch, force_ollama_enabled):
    # A LLM devolveu "macas"; deve casar com o slug "maca".
    monkeypatch.setattr(httpx, "post", _fake_post_returning("macas"))

    result = llm.extract_product_with_llm("Tem macas?", AVAILABLE)

    assert result == "maca"


def test_llm_ignores_product_outside_catalog(monkeypatch, force_ollama_enabled):
    monkeypatch.setattr(httpx, "post", _fake_post_returning("manga"))

    result = llm.extract_product_with_llm("Tem manga?", AVAILABLE)

    assert result is None


def test_llm_returns_none_on_network_error(monkeypatch, force_ollama_enabled):
    def raising_post(url, json=None, timeout=None):
        raise httpx.ConnectError("ollama offline")

    monkeypatch.setattr(httpx, "post", raising_post)

    result = llm.extract_product_with_llm("Tem uva?", AVAILABLE)

    assert result is None


def test_llm_returns_none_on_invalid_json(monkeypatch, force_ollama_enabled):
    def fake_post(url, json=None, timeout=None):
        return _response(url, {"response": "isto nao e json"})

    monkeypatch.setattr(httpx, "post", fake_post)

    result = llm.extract_product_with_llm("Tem uva?", AVAILABLE)

    assert result is None


def test_llm_disabled_skips_http_call(monkeypatch):
    # Com a LLM desligada, nenhuma chamada HTTP deve acontecer.
    monkeypatch.setattr(llm, "is_ollama_enabled", lambda: False)

    def fail_post(*args, **kwargs):
        raise AssertionError("nao deveria chamar a LLM quando desligada")

    monkeypatch.setattr(httpx, "post", fail_post)

    assert llm.extract_product_with_llm("Tem uva?", AVAILABLE) is None
