from pathlib import Path
from collections import Counter

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
    DeleteKnowledgeSourceResponse,
    IngestTextRequest,
    IngestUrlRequest,
    IngestUrlResponse,
    KnowledgeSourceItem,
    KnowledgeSourcesResponse,
)
from .workflow import ChatbotAgent

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
KB_STORE_FILE = DATA_DIR / "knowledge_base.json"
settings = get_settings()

llm = LLMClient(
    model=settings.gemini_model,
    api_key=settings.gemini_api_key,
    fallback_model=settings.gemini_fallback_model,
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
    description="AI Agent có bộ nhớ + nạp tài liệu từ URL + workflow rõ ràng",
)
FRONTEND_DIR = PROJECT_ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
FRONTEND_KNOWLEDGE_ENTRY = FRONTEND_DIR / "knowledge.html"
FRONTEND_CHAT_ENTRY = FRONTEND_DIR / "chat.html"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_CHAT_ENTRY)


@app.get("/chat")
def chat_page() -> FileResponse:
    return FileResponse(FRONTEND_CHAT_ENTRY)


@app.get("/knowledge")
def knowledge_page() -> FileResponse:
    return FileResponse(FRONTEND_KNOWLEDGE_ENTRY)


@app.get("/knowledge-sources", response_model=KnowledgeSourcesResponse)
def knowledge_sources() -> KnowledgeSourcesResponse:
    source_counts = Counter(kb.sources)
    items: list[KnowledgeSourceItem] = []

    for source, chunk_count in source_counts.items():
        if source.startswith("file:"):
            source_type = "file"
            display_name = source.removeprefix("file:")
        elif source.startswith("http://") or source.startswith("https://"):
            source_type = "url"
            display_name = source
        else:
            source_type = "text"
            display_name = source

        items.append(
            KnowledgeSourceItem(
                source=source,
                display_name=display_name,
                source_type=source_type,
                chunk_count=chunk_count,
            )
        )

    items.sort(key=lambda item: item.chunk_count, reverse=True)
    return KnowledgeSourcesResponse(items=items)


@app.delete("/knowledge-sources", response_model=DeleteKnowledgeSourceResponse)
def delete_knowledge_source(source: str) -> DeleteKnowledgeSourceResponse:
    removed_count = kb.remove_source(source)
    if removed_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguồn dữ liệu để xóa")

    _save_kb_to_disk()
    return DeleteKnowledgeSourceResponse(
        message="Xóa nguồn dữ liệu thành công",
        removed_chunks=removed_count,
    )


@app.post("/ingest-url", response_model=IngestUrlResponse)
def ingest_url(payload: IngestUrlRequest) -> IngestUrlResponse:
    try:
        count = agent.ingest_url(payload.url)
        _save_kb_to_disk()
        return IngestUrlResponse(
            message="Nạp tài liệu thành công",
            chunk_count=count,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Không nạp được URL: {exc}") from exc


@app.post("/ingest-text", response_model=IngestUrlResponse)
def ingest_text(payload: IngestTextRequest) -> IngestUrlResponse:
    normalized_text = normalizer.normalize_text(payload.text)
    count = agent.ingest_text(text=normalized_text, source=payload.source)
    if count == 0:
        raise HTTPException(status_code=400, detail="Nội dung văn bản rỗng hoặc không trích xuất được")
    _save_kb_to_disk()
    return IngestUrlResponse(
        message="Nạp văn bản thành công",
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
            detail="Chỉ hỗ trợ .txt, .md, .csv, .json, .pdf, .doc, .docx, .xls, .xlsx",
        )

    raw = await file.read()
    try:
        text = normalizer.normalize_file(raw, filename=filename)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Không thể trích xuất nội dung tệp. Kiểm tra tệp hoặc cài thêm dependency hệ thống (ví dụ: pandoc cho doc/docx): {exc}",
        ) from exc

    count = agent.ingest_text(text=text, source=f"file:{filename}")
    if count == 0:
        raise HTTPException(status_code=400, detail="Tệp không có nội dung hợp lệ")
    _save_kb_to_disk()

    return IngestUrlResponse(
        message=f"Nạp tệp {filename} thành công",
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
        raise HTTPException(status_code=500, detail=f"Lỗi khi chat: {exc}") from exc
