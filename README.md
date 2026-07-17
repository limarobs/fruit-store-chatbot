# Fruit Store Chatbot

Chatbot para consultar o estoque local de uma loja de frutas usando FastAPI,
SQLite, React, TypeScript e LLM local via Ollama.

## Funcionalidades

- Consulta de estoque em linguagem natural.
- Banco SQLite local com seed de frutas.
- LLM local opcional com Ollama.
- Fallback quando a LLM estiver indisponivel.
- Interface web em formato de chat.
- Testes automatizados com pytest.

## Stack

- Backend: Python, FastAPI, SQLite
- Frontend: React, TypeScript, Vite
- LLM: Ollama com `llama3.2:3b`
- Testes: pytest

## Como rodar

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

### Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Aplicacao:

```text
http://localhost:5173
```

## LLM local

O projeto nao usa OpenAI. A LLM local e opcional e roda via Ollama.

Instale o modelo recomendado:

```bash
ollama pull llama3.2:3b
```

Crie `backend/.env` a partir de `backend/.env.example`:

```env
OLLAMA_ENABLED=true
OLLAMA_MODEL=llama3.2:3b
OLLAMA_URL=http://localhost:11434
```

Se o Ollama estiver desligado, lento ou responder fora do formato esperado, a
API usa o fallback local e continua respondendo com dados do SQLite.

## Exemplos de uso

```bash
GET http://localhost:8000/health
```

```bash
GET http://localhost:8000/products
```

```bash
POST http://localhost:8000/chat
Content-Type: application/json

{
  "question": "Tem quantas macas?"
}
```

Resposta:

```json
{
  "answer": "Temos 42 unidades de maca em estoque.",
  "product": "Maca",
  "quantity": 42,
  "interpreter": "llm"
}
```

O campo `interpreter` indica se a pergunta foi interpretada pela LLM local
(`llm`) ou pelo fallback deterministico (`fallback`).

## Testes

```bash
cd backend
.venv\Scripts\activate
pytest
```

## Arquitetura

```text
React/Vite -> FastAPI /chat -> interpretador LLM local ou fallback
                              -> consulta SQLite
                              -> resposta com quantidade real do banco
```

A LLM nao inventa quantidades. Ela apenas tenta identificar o produto citado na
pergunta; a quantidade sempre vem do banco local.
