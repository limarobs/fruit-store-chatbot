from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db, list_products


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
