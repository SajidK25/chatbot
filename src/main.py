from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from src.config import settings
from src.services.chat_handler import chat_handler
from src.services.search_service import search_service
from src.bots.whatsapp_bot import router as whatsapp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("OpenClaw API started!")
    yield
    print("OpenClaw API shutting down!")


app = FastAPI(
    title="OpenClaw API",
    description="AI-powered e-commerce chatbot backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    max_price: float | None = None
    category: str | None = None
    gender: str | None = None
    limit: int = 3


class ChatRequest(BaseModel):
    message: str
    platform: str = "telegram"


class ChatResponse(BaseModel):
    response: str
    products: list[dict] | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "OpenClaw API"}


@app.post("/api/search", response_model=ChatResponse)
async def search_products(request: SearchRequest):
    parsed = search_service.parse_natural_language(request.query)

    if request.max_price:
        parsed["max_price"] = request.max_price
    if request.category:
        parsed["category"] = request.category
    if request.gender:
        parsed["gender"] = request.gender

    products = await search_service.search_products(
        query=parsed["query"],
        max_price=parsed.get("max_price"),
        category=parsed.get("category"),
        gender=parsed.get("gender"),
        limit=request.limit,
    )

    if not products:
        response_text = chat_handler._no_results_message(parsed["query"])
    else:
        response_text = chat_handler._format_products_message(
            products, request.platform
        )

    return ChatResponse(response=response_text, products=products)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    response = await chat_handler.handle_message(request.message, request.platform)
    return {"response": response}


app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])


@app.get("/")
async def root():
    return {"message": "Welcome to OpenClaw API", "docs": "/docs"}
