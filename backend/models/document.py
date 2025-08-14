from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    filename : str
    status : str
    message : str
    timestamp : datetime = datetime.utcnow()

