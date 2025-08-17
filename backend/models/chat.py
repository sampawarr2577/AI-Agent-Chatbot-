from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Source(BaseModel):
    filename: str
    page_number: Optional[int] = None
    chunk_id: str
    content_preview: str
    chunk_type: str  # 'text' or 'table'
    similarity_score: Optional[float] = None
    table_info: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    session_id: str
    timestamp: datetime = datetime.utcnow()
    success: bool = True
    error_message: Optional[str] = None
