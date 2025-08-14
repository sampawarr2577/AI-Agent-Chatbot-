from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.document import DocumentResponse
from services.document_service import DocumentService
from utils.logger import logger
import uvicorn 
from config import settings


app = FastAPI(
    title= "AI Document QA Agent",
    description= "Intelligent document Question-Answering system using RAG with support for text and tables",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.post("/documents/upload", response_model= DocumentResponse)
async def upload_document(file: UploadFile = File(...,description="upload file to process of pdf, txt, docx format")):
    """ upload and process document for QA"""
    try:
        file_content = await file.read()
        document_service = DocumentService()
        result = await document_service.process_document(file_content, file.filename)

        return DocumentResponse(
            filename = result["filename"],
            status = "Processed",
            message = "Document uploaded successfully"
        )
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app",
                host = settings.BACKEND_HOST,
                port = settings.BACKEND_PORT,
                reload= True)