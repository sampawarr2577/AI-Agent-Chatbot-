from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    document_id: str
    filename : str
    total_chunks: int
    status : str
    message : str
    timestamp : datetime = datetime.utcnow()

class DocumentUpload(BaseModel):
    filename: str

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int] = None

class DocumentList(BaseModel):
    documents: List[Dict[str, Any]]
    total: int

class DocumentDeleteResponse(BaseModel):
    document_id: str
    message: str
    success: bool