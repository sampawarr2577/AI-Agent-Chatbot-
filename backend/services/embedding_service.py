from typing import List
from langchain_openai import OpenAIEmbeddings
from config import settings
from utils.logger import logger
class EmbeddingService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_EMBEDDING_MODEL
        )
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents"""
        try:
            return await self.embeddings.aembed_documents(texts)
        except Exception as e:
            logger.info(f"Error generating embeddings for documents: {e}")
            raise
    
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query"""
        try:
            return await self.embeddings.aembed_query(text)
        except Exception as e:
            logger.info(f"Error generating embedding for query: {e}")
            raise
