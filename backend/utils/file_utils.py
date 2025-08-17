import os
from typing import List
from pathlib import Path
from utils.logger import logger

ALLOWED_EXTENSIONS = {".pdf",".txt",".docx",".xlsx"}

def validate_file_type(filename:str)-> bool:
    """Check if file type is supported"""
    file_extension = Path(filename).suffix.lower()
    logger.info(f"file extension is {file_extension}")
    return file_extension in ALLOWED_EXTENSIONS
    
def get_file_size(file_path:str)-> int:
    """Get file size in bytes"""
    file_size = os.path.getsize(file_path)
    logger.info(f"file size is {file_size}")
    return file_size

def ensure_directory_exists(directory_path:str)-> None:
    """Create directory if it doesn't exist"""
    os.makedirs(directory_path, exist_ok=True)