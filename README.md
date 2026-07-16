# Fruit Store Chatbot

Chatbot para consultar o estoque local de uma loja de frutas.

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
GET http://localhost:8000/health
```
