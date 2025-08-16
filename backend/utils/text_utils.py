from docling.document_converter import DocumentConverter
from typing import Iterator
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

class DoclingPDFLoader(BaseLoader):
    def __init__(self, file_path:str | list[str]) -> None:
        self.file_paths = file_path if isinstance(file_path,list) else [file_path]
        self.convertor = DocumentConverter()

    def lazy_load(self) -> Iterator[Document]:
        for source in self.file_paths:
            d1_doc = self.convertor.convert(source).document
            text = d1_doc.export_to_markdown()
            yield Document(page_content=text, metadata = {"source":source})