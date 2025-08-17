import os
import pickle
import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document

from config import settings
from services.embedding_service import EmbeddingService

class VectorService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.index = None
        self.documents = []
        self.index_path = os.path.join(settings.VECTOR_STORE_PATH, "faiss_index")
        self.docs_path = os.path.join(settings.VECTOR_STORE_PATH, "documents.pkl")
        
        # Ensure vector store directory exists
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    async def add_documents(self, documents: List[Document]) -> str:
        """Add documents to the vector store"""
        if not documents:
            return "No documents to add"
        
        try:
            # Extract text content
            texts = [doc.page_content for doc in documents]
            
            # Generate embeddings
            embeddings = await self.embedding_service.embed_documents(texts)
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Initialize or update FAISS index
            if self.index is None:
                # Create new index
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            # Add embeddings to index
            self.index.add(embeddings_array)
            
            # Store documents
            self.documents.extend(documents)
            
            # Persist to disk
            self._save_index()
            
            return f"Added {len(documents)} documents to vector store"
            
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            raise
    
    async def similarity_search(self, query: str, k: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        """Perform similarity search"""
        if self.index is None or self.index.ntotal == 0:
            return []

        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_query(query)
            query_vector = np.array([query_embedding], dtype='float32')
            
            # Search in FAISS index
            distances, all_indices = self.index.search(query_vector, min(k, self.index.ntotal))
            scores = distances[0]       # shape (k,)
            indices = all_indices    # shape (k,)

            results = []
            for score, idx in zip(scores, indices):
                idx = int(idx)  # convert to native Python int
                if 0 <= idx < len(self.documents):
                    doc = self.documents[idx]

                    # Apply filters if provided
                    if filters and not self._matches_filters(doc.metadata, filters):
                        continue

                    results.append({
                        'document': doc,
                        'similarity_score': float(score),
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    })

            return results

        except Exception as e:
            print(f"Error performing similarity search: {e}")
            return []

    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """Check if document metadata matches the provided filters"""
        for key, value in filters.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
            
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
                
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def _load_index(self):
        """Load FAISS index and documents from disk"""
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                print(f"Loaded vector store with {len(self.documents)} documents")
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.index = None
                self.documents = []
    
    def get_document_count(self) -> int:
        """Get total number of documents in the vector store"""
        return len(self.documents)
    
    def get_documents_by_filename(self, filename: str) -> List[Document]:
        """Get all documents for a specific filename"""
        return [doc for doc in self.documents if doc.metadata.get('filename') == filename]
    
    def clear_documents(self, document_id: Optional[str] = None):
        """Clear all documents or documents for a specific document_id"""
        if document_id:
            # Remove specific document
            original_count = len(self.documents)
            self.documents = [doc for doc in self.documents if doc.metadata.get('document_id') != document_id]
            removed_count = original_count - len(self.documents)
            
            # Rebuild index after removal
            if removed_count > 0:
                self._rebuild_index()
                
            return f"Removed {removed_count} chunks for document {document_id}"
        else:
            # Clear all
            self.documents = []
            self.index = None
            self._save_index()
            return "Cleared all documents"
    
    async def _rebuild_index(self):
        """Rebuild the FAISS index after document removal"""
        if not self.documents:
            self.index = None
            self._save_index()
            return
        
        try:
            # Extract text content
            texts = [doc.page_content for doc in self.documents]
            
            # Generate embeddings
            embeddings = await self.embedding_service.embed_documents(texts)
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Create new index
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings_array)
            
            # Save updated index
            self._save_index()
            
        except Exception as e:
            print(f"Error rebuilding index: {e}")
