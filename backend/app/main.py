from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.database import init_db, list_products
from app.services.chat import answer_inventory_question


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Tem quantas macas?"])


class ChatResponse(BaseModel):
    answer: str
    intent: str
    product: str | None
    quantity: int | None
    interpreter: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Fruit Store Chatbot API",
    description="API para consultar o estoque de uma loja de frutas.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/products")
def get_products() -> list[dict[str, int | str]]:
    return list_products()


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(**answer_inventory_question(request.question))
