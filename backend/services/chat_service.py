from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
import uuid

from config import settings
from services.vector_service import VectorService
from models.chat import Source

class ChatService:
    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
        self.llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_CHAT_MODEL,
            temperature=0.7
        )
        
        # Simple session storage (in production, use Redis or database)
        self.sessions = {}
    
    async def get_response(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using RAG"""
        
        # Create session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'history': [],
                'created_at': str(uuid.uuid4())
            }
        
        try:
            # Search for relevant documents
            search_results = await self.vector_service.similarity_search(
                query=message,
                k=settings.VECTOR_SEARCH_TOP_K
            )
            
            # Format context from search results
            context_parts = []
            sources = []
            
            for result in search_results:
                doc = result['document']
                context_parts.append(f"Source: {doc.metadata['filename']}")
                context_parts.append(f"Content: {doc.page_content}")
                context_parts.append("---")
                
                # Create source information
                source = Source(
                    filename=doc.metadata['filename'],
                    chunk_id=doc.metadata['chunk_id'],
                    content_preview=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    chunk_type=doc.metadata.get('chunk_type', 'text'),
                    similarity_score=result['similarity_score']
                )
                
                # Add table-specific information
                if doc.metadata.get('chunk_type') == 'table':
                    source.table_info = {
                        'shape': doc.metadata.get('table_shape'),
                        'columns': doc.metadata.get('table_columns', [])
                    }
                
                sources.append(source)
            
            context = "\n".join(context_parts)
            
            # Get chat history
            chat_history = self._format_chat_history(session_id)
            
            # Create prompt
            prompt = self._create_prompt(context, chat_history, message)
            
            # Generate response
            response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
            answer = response.generations[0][0].text
            
            # Update session history
            self.sessions[session_id]['history'].append({
                'type': 'human',
                'content': message
            })
            self.sessions[session_id]['history'].append({
                'type': 'ai',
                'content': answer
            })
            
            # Keep only last 10 exchanges
            if len(self.sessions[session_id]['history']) > 20:
                self.sessions[session_id]['history'] = self.sessions[session_id]['history'][-20:]
            
            return {
                'answer': answer,
                'sources': [source.dict() for source in sources],
                'session_id': session_id,
                'success': True
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'answer': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'session_id': session_id,
                'success': False,
                'error_message': str(e)
            }
    
    def _format_chat_history(self, session_id: str) -> str:
        """Format chat history for context"""
        if session_id not in self.sessions:
            return ""
        
        history = self.sessions[session_id]['history']
        if not history:
            return ""
        
        formatted_history = []
        for entry in history[-10:]:  # Last 5 exchanges
            if entry['type'] == 'human':
                formatted_history.append(f"Human: {entry['content']}")
            else:
                formatted_history.append(f"Assistant: {entry['content']}")
        
        return "\n".join(formatted_history)
    
    def _create_prompt(self, context: str, chat_history: str, question: str) -> str:
        """Create the prompt for the LLM"""
        return f"""You are an AI assistant helping users understand documents and tables they've uploaded. 
                    Use the following context from the documents to answer the user's question accurately and cite your sources.

                    Context from documents:
                    {context}

                    Previous conversation:
                    {chat_history}

                    Instructions:
                    1. Answer based on the provided context from the uploaded documents
                    2. If the information is not in the context, clearly state that you cannot find the answer in the uploaded documents
                    3. When referencing tables, mention the table structure and specific data points
                    4. Be specific about which document or section your answer comes from
                    5. If multiple sources support your answer, mention them all
                    6. Keep your response concise but comprehensive

                    Current question: {question}

                    Answer:"""
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a chat session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                'session_id': session_id,
                'message_count': len(session['history']),
                'created_at': session['created_at']
            }
        return None
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
