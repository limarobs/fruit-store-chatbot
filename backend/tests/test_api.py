from fastapi.testclient import TestClient

from app.main import app


# testes de integracao da API usando TestClient do FastAPI
def test_health_route_reports_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products_route_lists_seeded_inventory():
    with TestClient(app) as client:
        response = client.get("/products")

    assert response.status_code == 200
    products = response.json()

    assert len(products) >= 5
    assert {"slug": "maca", "name": "Maca", "quantity": 42, "price_cents": 450} in products


# verifica se /chat responde corretamente a uma pergunta sobre estoque
def test_chat_route_answers_inventory_question_with_accent():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Tem quantas maçãs?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Temos 42 unidades de maca em estoque.",
        "intent": "quantity",
        "product": "Maca",
        "quantity": 42,
        "interpreter": "fallback",
    }


def test_chat_route_handles_unknown_product():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Tem manga?"})

    assert response.status_code == 200
    assert response.json()["product"] is None
    assert response.json()["quantity"] is None


def test_chat_route_answers_price_question():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Quanto custa a banana?"})

    body = response.json()
    assert response.status_code == 200
    assert body["intent"] == "price"
    assert "R$ 3,20" in body["answer"]


def test_chat_route_answers_low_stock_question():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Quais frutas estao acabando?"})

    body = response.json()
    assert body["intent"] == "low_stock"
    assert "abacaxi" in body["answer"]
    assert "maca" not in body["answer"]


def test_chat_route_answers_total_question():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Quantas frutas no total?"})

    body = response.json()
    assert body["intent"] == "total"
    assert body["quantity"] == 127


def test_chat_route_rejects_empty_question():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": ""})

    assert response.status_code == 422
