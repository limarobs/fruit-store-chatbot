from fastapi.testclient import TestClient

from app.main import app


# tstes de integração da API usando TestClient do FastAPI
def test_products_route_lists_seeded_inventory():
    with TestClient(app) as client:
        response = client.get("/products")

    assert response.status_code == 200
    products = response.json()

    assert len(products) >= 5
    assert {"slug": "maca", "name": "Maca", "quantity": 42} in products



# verifica se a rota /chat responde corretamente a uma pergunta sobre estoque
def test_chat_route_answers_inventory_question_with_accent():
    with TestClient(app) as client:
        response = client.post("/chat", json={"question": "Tem quantas maçãs?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Temos 42 unidades de maca em estoque.",
        "product": "Maca",
        "quantity": 42,
    }
