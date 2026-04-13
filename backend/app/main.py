from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .llm import LLMClient
from .memory import SessionMemory
from .normalizer import InputNormalizer
from .persistence import load_knowledge_base, save_knowledge_base
from .retriever import InMemoryKnowledgeBase
from .schemas import (
    ChatRequest,
    ChatResponse,
    IngestTextRequest,
    IngestUrlRequest,
    IngestUrlResponse,
)
from .workflow import ChatbotAgent

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
KB_STORE_FILE = DATA_DIR / "knowledge_base.json"
settings = get_settings()

llm = LLMClient(
    provider=settings.get_llm_provider(),
    model=settings.get_llm_model(),
    api_key=settings.get_llm_api_key(),
    base_url=settings.get_llm_base_url(),
)
memory = SessionMemory(max_turns=settings.max_turns_memory)
kb = InMemoryKnowledgeBase()
normalizer = InputNormalizer()
agent = ChatbotAgent(
    llm=llm,
    memory=memory,
    kb=kb,
    system_prompt=settings.load_system_prompt(PROJECT_ROOT),
)


def _load_kb_from_disk() -> None:
    items = load_knowledge_base(KB_STORE_FILE)
    if not items:
        return
    source_to_chunks: dict[str, list[str]] = {}
    for item in items:
        source_to_chunks.setdefault(item["source"], []).append(item["text"])
    for source, chunks in source_to_chunks.items():
        kb.add_chunks(chunks=chunks, source=source)


def _save_kb_to_disk() -> None:
    save_knowledge_base(KB_STORE_FILE, docs=kb.docs, sources=kb.sources)


_load_kb_from_disk()

app = FastAPI(
    title="Chatbot AI Agent",
    version="1.0.0",
    description="Agent co memory + ingest tai lieu tu URL + workflow ro rang",
)
FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/ingest-url", response_model=IngestUrlResponse)
def ingest_url(payload: IngestUrlRequest) -> IngestUrlResponse:
    try:
        count = agent.ingest_url(payload.url)
        _save_kb_to_disk()
        return IngestUrlResponse(
            message="Nap tai lieu thanh cong",
            chunk_count=count,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Khong nap duoc URL: {exc}") from exc


@app.post("/ingest-text", response_model=IngestUrlResponse)
def ingest_text(payload: IngestTextRequest) -> IngestUrlResponse:
    normalized_text = normalizer.normalize_text(payload.text)
    count = agent.ingest_text(text=normalized_text, source=payload.source)
    if count == 0:
        raise HTTPException(status_code=400, detail="Noi dung text rong hoac khong trich xuat duoc")
    _save_kb_to_disk()
    return IngestUrlResponse(
        message="Nap text thanh cong",
        chunk_count=count,
    )


@app.post("/ingest-file", response_model=IngestUrlResponse)
async def ingest_file(file: UploadFile = File(...)) -> IngestUrlResponse:
    allowed = {".txt", ".md", ".csv", ".json", ".pdf", ".doc", ".docx", ".xls", ".xlsx"}
    filename = file.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Chi ho tro .txt, .md, .csv, .json, .pdf, .doc, .docx, .xls, .xlsx",
        )

    raw = await file.read()
    try:
        text = normalizer.normalize_file(raw, filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Khong the trich xuat noi dung file. Kiem tra file hoac cai them dependency he thong (vd: pandoc cho doc/docx): {exc}",
        ) from exc

    count = agent.ingest_text(text=text, source=f"file:{filename}")
    if count == 0:
        raise HTTPException(status_code=400, detail="File khong co noi dung hop le")
    _save_kb_to_disk()

    return IngestUrlResponse(
        message=f"Nap file {filename} thanh cong",
        chunk_count=count,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        result = agent.ask(session_id=payload.session_id, user_message=payload.message)
        return ChatResponse(
            session_id=payload.session_id,
            answer=result.answer,
            source=result.source,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Loi khi chat: {exc}") from exc
