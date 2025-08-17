import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import time
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="AI Document QA Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.stChat > div {
    padding-bottom: 1rem;
}
.citation-box {
    background-color: #f0f2f6;
    border-left: 4px solid #ff6b6b;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 0.5rem;
}
.table-info {
    background-color: #e8f4fd;
    border-left: 4px solid #1f77b4;
    padding: 0.5rem;
    margin: 0.3rem 0;
    border-radius: 0.3rem;
    font-size: 0.9em;
}
.metric-container {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'documents' not in st.session_state:
    st.session_state.documents = []

if 'last_upload_time' not in st.session_state:
    st.session_state.last_upload_time = None

# Helper functions
def make_api_request(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Make API request with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        elif method == "DELETE":
            response = requests.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return {"success": True, "data": response.json()}
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def load_documents():
    """Load documents list from API"""
    result = make_api_request("/documents")
    if result["success"]:
        st.session_state.documents = result["data"]["documents"]
    else:
        st.error(f"Failed to load documents: {result['error']}")

def upload_document(uploaded_file) -> bool:
    """Upload document to API"""
    try:
        # Convert Streamlit uploaded file into a proper tuple for requests
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),   # Ensure we pass bytes, not the file object
                uploaded_file.type or "application/octet-stream"
            )
        }

        result = make_api_request("/documents/upload", method="POST", files=files)

        if result["success"]:
            doc_info = result["data"]

            st.success(f"✅ Document '{uploaded_file.name}' processed successfully!")
            st.success(
                f"📊 Created {doc_info.get('total_chunks', 0)} chunks "
                f"({doc_info.get('text_chunks', 0)} text, {doc_info.get('table_chunks', 0)} tables)"
            )

            # Update documents list
            load_documents()
            st.session_state.last_upload_time = datetime.now()
            return True

        else:
            st.error(f"❌ Upload failed: {result['error']}")
            return False

    except Exception as e:
        st.error(f"❌ Upload error: {str(e)}")
        return False


def send_chat_message(message: str) -> Dict[str, Any]:
    """Send chat message to API"""
    chat_data = {
        "message": message,
        "session_id": st.session_state.session_id
    }
    
    result = make_api_request("/chat", method="POST", json=chat_data, headers={"Content-Type": "application/json"})
    
    if result["success"]:
        return result["data"]
    else:
        return {
            "answer": f"❌ Error: {result['error']}",
            "sources": [],
            "session_id": st.session_state.session_id,
            "success": False
        }

# Sidebar for document management
with st.sidebar:
    st.title("📚 Document Management")
    
    # Document upload section
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=['pdf', 'txt', 'docx',"xlsx"],
        help="Upload PDF, text, or Word documents (max 50MB)",
        key="file_uploader"
    )
    
    if uploaded_file is not None:
        # Show file info
        file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {file_size_mb:.1f} MB")
        st.write(f"**Type:** {uploaded_file.type}")
        
        if st.button("Process Document", type="primary", key="upload_btn"):
            with st.spinner("Processing document..."):
                if upload_document(uploaded_file):
                    # Clear the file uploader
                    st.rerun()
    
    # Documents list section
    st.subheader("📄 Processed Documents")
    
    if st.button("🔄 Refresh Documents", key="refresh_docs"):
        load_documents()
    
    # Load documents on first run
    if not st.session_state.documents:
        load_documents()
    
    if st.session_state.documents:
        for doc in st.session_state.documents:
            with st.expander(f"📄 {doc['filename']}", expanded=False):
                st.write(f"**Document ID:** `{doc['document_id'][:12]}...`")
                st.write(f"**Total Chunks:** {doc['total_chunks']}")
                st.write(f"**Text Chunks:** {doc['text_chunks']}")
                st.write(f"**Table Chunks:** {doc['table_chunks']}")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_{doc['document_id']}", help="Delete this document"):
                    result = make_api_request(f"/documents/{doc['document_id']}", method="DELETE")
                    if result["success"]:
                        st.success("Document deleted successfully!")
                        load_documents()
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {result['error']}")
    else:
        st.info("No documents uploaded yet. Upload a document to get started!")
    
    # Session management
    st.divider()
    st.subheader("💬 Session Info")
    
    st.write(f"**Session ID:** `{st.session_state.session_id[:12]}...`")
    st.write(f"**Messages:** {len([m for m in st.session_state.chat_history if m['role'] == 'user'])}")
    
    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.chat_history = []
        # Also clear on server side
        make_api_request(f"/sessions/{st.session_state.session_id}", method="DELETE")
        st.success("Chat history cleared!")
        st.rerun()

# Main chat interface
st.title("🤖 AI Document QA Agent")
st.markdown("Ask questions about your uploaded documents and tables!")

# Check if documents are available
if not st.session_state.documents:
    st.warning("⚠️ No documents available. Please upload some documents first to start asking questions.")

# Display chat history
chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display sources for assistant messages
            if message["role"] == "assistant" and "sources" in message and message["sources"]:
                with st.expander("📚 Sources & Citations", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        source_type = source.get('chunk_type', 'text')
                        
                        if source_type == 'table':
                            st.markdown(
                                f"""
                                <div class="table-info">
                                <strong>🔢 Table Source {i}:</strong> {source['filename']}<br>
                                <strong>Table Info:</strong> {source.get('table_info', {}).get('shape', 'Unknown shape')}<br>
                                <strong>Columns:</strong> {', '.join(source.get('table_info', {}).get('columns', []))}<br>
                                <em>Preview:</em> {source['content_preview']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="citation-box">
                                <strong>📄 Text Source {i}:</strong> {source['filename']}<br>
                                <em>Preview:</em> {source['content_preview']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_data = send_chat_message(prompt)
            
            answer = response_data['answer']
            sources = response_data.get('sources', [])
            
            st.markdown(answer)
            
            # Add to chat history with sources
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": answer,
                "sources": sources
            })
            
            # Display sources if available
            if sources:
                with st.expander("📚 Sources & Citations", expanded=False):
                    for i, source in enumerate(sources, 1):
                        source_type = source.get('chunk_type', 'text')
                        
                        if source_type == 'table':
                            st.markdown(
                                f"""
                                <div class="table-info">
                                <strong>🔢 Table Source {i}:</strong> {source['filename']}<br>
                                <strong>Table Info:</strong> {source.get('table_info', {}).get('shape', 'Unknown shape')}<br>
                                <strong>Columns:</strong> {', '.join(source.get('table_info', {}).get('columns', []))}<br>
                                <em>Preview:</em> {source['content_preview']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="citation-box">
                                <strong>📄 Text Source {i}:</strong> {source['filename']}<br>
                                <em>Preview:</em> {source['content_preview']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
            
            # Auto-refresh to show new message
            st.rerun()

# Footer with metrics
st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📄 Documents", len(st.session_state.documents))

with col2:
    total_chunks = sum(doc.get('total_chunks', 0) for doc in st.session_state.documents)
    st.metric("📊 Total Chunks", total_chunks)

with col3:
    st.metric("💬 Messages", len([m for m in st.session_state.chat_history if m["role"] == "user"]))

with col4:
    if st.session_state.last_upload_time:
        time_diff = datetime.now() - st.session_state.last_upload_time
        if time_diff.total_seconds() < 60:
            last_upload = "Just now"
        elif time_diff.total_seconds() < 3600:
            last_upload = f"{int(time_diff.total_seconds() / 60)}m ago"
        else:
            last_upload = f"{int(time_diff.total_seconds() / 3600)}h ago"
    else:
        last_upload = "Never"
    
    st.metric("⏰ Last Upload", last_upload)

# Add some helpful tips
with st.expander("💡 Tips for Better Results", expanded=False):
    st.markdown("""
    **For Text Documents:**
    - Ask specific questions about content, topics, or concepts
    - Request summaries or key points
    - Ask for quotes or specific information
    
    **For Tables:**
    - Ask about specific data values or comparisons
    - Request calculations or aggregations
    - Ask about trends or patterns in the data
    
    **General Tips:**
    - Be specific in your questions
    - Reference document names when asking about multiple documents
    - Ask follow-up questions to dive deeper into topics
    """)
