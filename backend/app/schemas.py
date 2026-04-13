from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID để lưu bộ nhớ theo người dùng")
    message: str = Field(..., min_length=1, description="Tin nhắn của người dùng")


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    source: str


class IngestUrlRequest(BaseModel):
    url: str = Field(..., description="URL cần nạp vào kho tri thức")


class IngestUrlResponse(BaseModel):
    message: str
    chunk_count: int


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Nội dung văn bản cần nạp")
    source: str = Field(default="manual_input", description="Nguồn dữ liệu tự đặt tên")


class KnowledgeSourceItem(BaseModel):
    source: str
    display_name: str
    source_type: str
    chunk_count: int


class KnowledgeSourcesResponse(BaseModel):
    items: list[KnowledgeSourceItem]


class DeleteKnowledgeSourceResponse(BaseModel):
    message: str
    removed_chunks: int
