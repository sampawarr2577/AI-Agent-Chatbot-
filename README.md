# AI Document QA Agent

An intelligent document question-answering system that processes text documents and tables using Retrieval-Augmented Generation (RAG) with a FastAPI backend and Streamlit frontend.

***

## Features

- **Document Processing**: Supports PDF, DOCX, XLSX, and TXT files  
- **Text and Table Extraction**: Uses DocLing for effective document pre-processing  
- **Vector Search**: In-memory FAISS vector database for fast similarity search  
- **Conversational QA**: Context-aware question answering with chat history  
- **Interactive UI**: User-friendly Streamlit interface  

***

## Technology Stack

- **Backend**: FastAPI with LangChain  
- **Frontend**: Streamlit  
- **LLM**: OpenAI GPT-3.5-turbo  
- **Embeddings**: OpenAI text-embedding-3-small  
- **Vector Database**: FAISS (in-memory)  
- **Document Processing**: PyPDF, python-docx, pandas, DocLing  

***

## Installation

1. Clone the repository  
   ```bash
   git clone https://github.com/sampawarr2577/AI-Agent-Chatbot-.git
   cd AI-AGENT_CHATBOT-
   ```

2. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables  
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` file and add your `OPENAI_API_KEY`  

5. Start the backend  
   ```bash
   cd backend  
   python main.py
   ```

6. Start the frontend (in a new terminal)  
   ```bash
   cd frontend  
   streamlit run app.py
   ```

***

## Usage

- Upload documents (PDF, DOCX, XLSX, TXT) from the sidebar  
- Ask questions about your uploaded documents in the chat interface  
- View source citations and document previews in the expanded source section  
- Manage uploaded documents (view and delete) from the sidebar  

***

## API Endpoints

- `POST /documents/upload` - Upload and process documents  
- `POST /chat` - Send chat messages and receive answers  
- `GET /documents` - List all processed documents  
- `DELETE /documents/{document_id}` - Delete a specific document  
- `GET /health` - Health check of the service  

***

## Configuration

Main settings available in `backend/config.py`:  
- `OPENAI_API_KEY`: Your OpenAI API key  
- `MAX_FILE_SIZE_MB`: Max file upload size (default 50MB)  
- `CHUNK_SIZE`: Text chunk size during processing (default 1000)  
- `VECTOR_SEARCH_TOP_K`: Number of search results returned (default 5)  

***
