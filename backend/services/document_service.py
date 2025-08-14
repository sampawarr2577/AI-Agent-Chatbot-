from typing import Dict, Any
from utils.file_utils import validate_file_type
from config import settings
from pathlib import Path
import tempfile
from utils.logger import logger

class DocumentService:
    def __init__(self):
        pass

    async def process_document(self, file_content:bytes, filename:str) -> Dict[str,Any]:
        """Process uploaded document"""

        if not validate_file_type(filename):
            raise ValueError(f"unsupported file type, Supported file types: .pdf, .txt, .docx")
        
        file_size_mb = len(file_content)/(1024*1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size({settings.MAX_FILE_SIZE_MB}MB)")
        
        file_extension = Path(filename).suffix.lower()
        temp_file_path = self.save_temp_file(file_content, file_extension)

        return {
            "filename":filename,
        }


    def save_temp_file(self, file_content:bytes, extension:str) -> str:
        """save uploaded file to temporary location"""
        temp_file = tempfile.NamedTemporaryFile(
            delete = False,
            suffix = extension,
            dir = settings.UPLOAD_FOLDER
        )

        temp_file.write(file_content)
        temp_file.close()
        return temp_file.name