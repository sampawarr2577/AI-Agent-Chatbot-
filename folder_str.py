import os

# Define folder structure
folders = [
    "backend",
    "backend/models",
    "backend/services",
    "backend/utils",
    "frontend",
    "data/uploads",
    "data/vector_store",
    "tests"
]

# Define files with their paths
files = [
    "backend/main.py",
    "backend/config.py",
    "backend/models/__init__.py",
    "backend/models/document.py",
    "backend/models/chat.py",
    "backend/services/__init__.py",
    "backend/services/document_service.py",
    "backend/services/embedding_service.py",
    "backend/services/vector_service.py",
    "backend/services/chat_service.py",
    "backend/utils/__init__.py",
    "backend/utils/file_utils.py",
    "backend/utils/text_utils.py",
    "frontend/app.py",
    "tests/test_document_service.py",
    "tests/test_chat_service.py"
]

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create files
for file in files:
    with open(file, "w", encoding="utf-8") as f:
        f.write("")  # Empty file placeholder

print("Folder structure created successfully.")
