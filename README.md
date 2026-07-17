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

Listar estoque:

```bash
GET http://localhost:8000/products
```

Perguntar ao chatbot:

```bash
POST http://localhost:8000/chat
Content-Type: application/json

{
  "question": "Tem quantas macas?"
}
```

### LLM local opcional

Para usar uma LLM local com Ollama:

```bash
ollama pull llama3.2
uvicorn app.main:app --reload
```

As configuracoes ficam em `backend/.env`. Use `backend/.env.example` como referencia.

Se o Ollama estiver desligado ou indisponivel, a API continua usando o fallback local.

Rodar testes:

```bash
cd backend
pytest
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Com o backend rodando em `http://localhost:8000`, o frontend usa proxy do Vite para chamar `POST /api/chat`.
