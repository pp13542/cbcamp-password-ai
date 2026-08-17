"""FastAPI entry point for the CBCAMP challenge."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.challenge import env_bool, get_flag
from app.model_service import ModelService
from app.schemas import ChatRequest, ChatResponse, HealthResponse

service = ModelService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Validate production configuration even when model loading is disabled.
    get_flag()
    if env_bool("LOAD_MODEL_ON_STARTUP") and not service.emergency_stable_mode:
        service.load()
    yield


app = FastAPI(title="비밀번호 찾기 도움 AI", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=service.model_loaded,
        adapter_loaded=service.adapter_loaded,
        model_name=service.model_name,
        device=service.device,
        emergency_stable_mode=service.emergency_stable_mode,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = [item.model_dump() for item in request.history]
    return ChatResponse(answer=service.answer(request.message, history))

