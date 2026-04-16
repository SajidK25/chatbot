import os
import uuid
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.services.chat_handler import chat_handler
from src.services.search_service import search_service
from src.bots.whatsapp_bot import router as whatsapp_router


limiter = Limiter(key_func=get_remote_address)


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

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return Response(
        content='{"error": "Too Many Requests"}',
        status_code=429,
        headers={"Retry-After": "60"},
    )


def get_cors_origins():
    env = os.getenv("ENV", "development")
    if env == "production":
        return ["https://*.render.com", "https://*.railway.com"]
    return ["http://localhost", "http://127.0.0.1"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_debug_headers(request: Request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{int((time.time() - start_time) * 1000)}ms"

    return response


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    max_price: float | None = None
    category: str | None = None
    gender: str | None = None
    limit: int = 3
    platform: str = "telegram"


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
@limiter.limit("100/minute")
async def search_products(request: Request, req: SearchRequest):
    parsed = search_service.parse_natural_language(req.query)

    if req.max_price:
        parsed["max_price"] = req.max_price
    if req.category:
        parsed["category"] = req.category
    if req.gender:
        parsed["gender"] = req.gender

    products = await search_service.search_products(
        query=parsed["query"],
        max_price=parsed.get("max_price"),
        category=parsed.get("category"),
        gender=parsed.get("gender"),
        limit=req.limit,
    )

    if not products:
        response_text = chat_handler._no_results_message(parsed["query"])
    else:
        response_text = chat_handler._format_products_message(products, req.platform)

    return ChatResponse(response=response_text, products=products)


@app.post("/api/chat")
@limiter.limit("100/minute")
async def chat(request: Request, req: ChatRequest):
    response = await chat_handler.handle_message(req.message, req.platform)
    return {"response": response}


app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])


@app.get("/")
async def root():
    return {"message": "Welcome to OpenClaw API", "docs": "/docs"}
