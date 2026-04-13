from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID de luu memory theo nguoi dung")
    message: str = Field(..., min_length=1, description="Tin nhan cua nguoi dung")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    source: str


class IngestUrlRequest(BaseModel):
    url: str = Field(..., description="URL can nap vao knowledge base")


class IngestUrlResponse(BaseModel):
    message: str
    chunk_count: int


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Noi dung van ban can nap")
    source: str = Field(default="manual_input", description="Nguon du lieu tu dat ten")
