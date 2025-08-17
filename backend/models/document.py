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

