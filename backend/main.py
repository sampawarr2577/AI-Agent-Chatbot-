from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from models.document import DocumentResponse, DocumentDeleteResponse, DocumentList
from services.document_service import DocumentService
from utils.logger import logger
import uvicorn 
from config import settings
from services.vector_service import VectorService
from contextlib import asynccontextmanager
import os
import uuid
from services.chat_service import ChatService
from models.chat import ChatRequest,ChatResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global vector_service, document_service
    
    # Ensure data directories exist
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
    
    # Initialize services
    app.state.vector_service = VectorService()
    app.state.document_service = DocumentService()
    app.state.chat_service = ChatService(app.state.vector_service)

    logger.info(f"Application started with {app.state.vector_service.get_document_count()} documents in vector store")
    
    yield
    
    # Shutdown
    print("Application shutting down...")

app = FastAPI(
    title= "AI Document QA Agent",
    description= "Intelligent document Question-Answering system using RAG with support for text and tables",
    version="1.0.0",
    lifespan= lifespan
)

# Dependency functions
def get_vector_service(request: Request) -> VectorService:
    return request.app.state.vector_service

def get_document_service(request: Request) -> DocumentService:
    return request.app.state.document_service

def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service

app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Document QA Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Document QA Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check(vector_service: VectorService = Depends(get_vector_service)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Document QA Agent",
        "documents_count": vector_service.get_document_count() if vector_service else 0
    }

@app.post("/documents/upload", response_model= DocumentResponse)
async def upload_document(background_tasks: BackgroundTasks,
                          file: UploadFile = File(...,description="upload file to process of pdf, txt, docx format"),
                          document_service: DocumentService = Depends(get_document_service),
                          vector_service: VectorService = Depends(get_vector_service)):
    """ upload and process document for QA"""
    try:
        file_content = await file.read()
        result = await document_service.process_document(file_content, file.filename)

        # Add chunks to vector store in background
        background_tasks.add_task(
            vector_service.add_documents,
            result["chunks"]
        )

        return DocumentResponse(
            document_id = result["document_id"],
            filename = result["filename"],
            total_chunks=result["total_chunks"],
            status = "Processed",
            message = "Document successfully processed and indexed"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Process chat query using RAG"""

    try:
        # Use the vector_service stored inside chat_service
        if chat_service.vector_service.get_document_count() == 0:
            return ChatResponse(
                answer="I don't have any documents to search through. Please upload some documents first.",
                sources=[],
                session_id=request.session_id or str(uuid.uuid4()),
                success=False,
                error_message="No documents available"
            )

        result = await chat_service.get_response(
            message=request.message,
            session_id=request.session_id
        )

        return ChatResponse(**result)

    except Exception as e:
        logger.exception("Error in chat endpoint")
        return ChatResponse(
            answer=f"I apologize, but I encountered an error: {e}",
            sources=[],
            session_id=request.session_id or str(uuid.uuid4()),
            success=False,
            error_message=str(e)
        )

@app.get("/documents", response_model=DocumentList)
async def list_documents(vector_service: VectorService = Depends(get_vector_service)):
    """List all processed documents"""
    try:
        # Get unique documents from vector store
        documents_info = {}
        
        for doc in vector_service.documents:
            doc_id = doc.metadata['document_id']
            filename = doc.metadata['filename']
            
            if doc_id not in documents_info:
                documents_info[doc_id] = {
                    'document_id': doc_id,
                    'filename': filename,
                    'total_chunks': 0,
                    'text_chunks': 0,
                    'table_chunks': 0
                }
            
            documents_info[doc_id]['total_chunks'] += 1
            
            if doc.metadata.get('chunk_type') == 'table':
                documents_info[doc_id]['table_chunks'] += 1
            else:
                documents_info[doc_id]['text_chunks'] += 1
        
        documents_list = list(documents_info.values())
        
        return DocumentList(
            documents=documents_list,
            total=len(documents_list)
        )
        
    except Exception as e:
        print(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str,
                          vector_service: VectorService = Depends(get_vector_service)):
    """Delete a specific document from the system"""
    try:
        result = vector_service.clear_documents(document_id)
        
        return DocumentDeleteResponse(
            document_id=document_id,
            message=result,
            success=True
        )
        
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}")
async def get_session_info(session_id: str,
                           chat_service: ChatService = Depends(get_chat_service)):
    """Get information about a chat session"""
    session_info = chat_service.get_session_info(session_id)
    
    if session_info:
        return session_info
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str,
                        chat_service: ChatService = Depends(get_chat_service)):
    """Clear a specific chat session"""
    success = chat_service.clear_session(session_id)
    
    if success:
        return {"message": f"Session {session_id} cleared successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    uvicorn.run("main:app",
                host = settings.BACKEND_HOST,
                port = settings.BACKEND_PORT,
                reload= True)