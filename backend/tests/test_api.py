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
    assert {"slug": "maca", "name": "Maca", "quantity": 42} in products


# verifica se /chat responde corretamente a uma pergunta sobre estoque
def test_chat_route_answers_inventory_question_with_accent():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Tem quantas maçãs?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Temos 42 unidades de maca em estoque.",
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


def test_chat_route_rejects_empty_question():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": ""})

    assert response.status_code == 422
