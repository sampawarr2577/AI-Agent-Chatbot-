from typing import Dict, Any
from utils.file_utils import validate_file_type
from config import settings
from pathlib import Path
import tempfile
from utils.logger import logger
from typing import List, Tuple, Dict, Any
import pandas as pd
from utils.text_utils import DoclingPDFLoader
import fitz
import os
import time
import uuid
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from ocrmypdf.hocrtransform import HocrTransform
from pypdf import PdfWriter, PdfReader

class DocumentService:
    def __init__(self):
        pass

    async def process_document(self, file_content:bytes, filename:str) -> Dict[str,Any]:
        """Process uploaded document"""

        if not validate_file_type(filename):
            raise ValueError(f"unsupported file type, Supported file types: .pdf, .txt, .docx")
        
        file_size_mb = len(file_content)/(1024*1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise ValueError(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size({settings.MAX_FILE_SIZE_MB}MB)")
        
        file_extension = Path(filename).suffix.lower()
        temp_file_path = self.save_temp_file(file_content, file_extension)

        try:
            if file_extension == ".pdf":
                md_text_content = self.process_pdf(temp_file_path)

            else:
                raise ValueError (f"Unsupported file type: {file_extension}")
            

            return {
                "filename":filename,
            }


    def save_temp_file(self, file_content:bytes, extension:str) -> str:
        """save uploaded file to temporary location"""
        temp_file = tempfile.NamedTemporaryFile(
            delete = False,
            suffix = extension,
            dir = settings.UPLOAD_FOLDER
        )

        temp_file.write(file_content)
        temp_file.close()
        return temp_file.name
    

    def get_markdown(self, file_path:str)-> list:
        """Read the input file and convert into markdown"""
        loader = DoclingPDFLoader(file_path=file_path)
        docs = loader.load()
        return docs
        
    def is_scanned_pdf(pdf_path:str)-> bool:
        """
        Detect if a PDF is scanned (image-based) or contains selectable text.
        Returns True if scanned, False otherwise.
        """
        pdf = fitz.open(pdf_path)
        for page in pdf:
            text = page.get_text()
            if text.strip():
                return False  # Found actual text → Not scanned
        return True
    
    def process_pdf(self, file_path:str)-> str:
        """Process pdf to extract markdown text from it"""
        try:
            if self.is_scanned_pdf(file_path):
                md_text = self.ocr_and_replace_pdf(file_path)
            else:
                md_text = self.get_markdown(file_path)

        except Exception as e:
            print(f"Error processing PDF: {e}")
            raise ValueError(f"Error processing PDF file: {str(e)}")
        return md_text
    
    def _unique_tmp_path(self,suffix: str) -> str:
        """Create a unique temp file path without opening the file."""
        return os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}{suffix}")


    def _save_pixmap_png_atomic(self,pix: fitz.Pixmap, target_path: str, retries: int = 3, delay: float = 0.1) -> None:
        """Save pixmap to PNG path with retries to avoid transient Windows locks."""
        for attempt in range(retries):
            try:
                # Ensure parent dir exists
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                # If file exists, remove it first (best effort)
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except Exception:
                        pass
                pix.save(target_path)  # This calls fz_save_pixmap_as_png internally
                return
            except Exception as e:
                if attempt == retries - 1:
                    raise
                time.sleep(delay)


    def _render_pdf_pages_to_images(self,pdf_path: str, dpi: int = 300) -> List[str]:
        """Render each page of a PDF to a PNG and return the paths, avoiding open handles."""
        img_paths: List[str] = []
        doc = fitz.open(pdf_path)
        try:
            for page_index in range(len(doc)):
                page = doc[page_index]
                pix = page.get_pixmap(dpi=dpi)
                img_path = self._unique_tmp_path(".png")
                self._save_pixmap_png_atomic(pix, img_path)
                img_paths.append(img_path)
        finally:
            # Ensure the document is fully closed before any deletes
            doc.close()
        return img_paths


    def _merge_pdfs(self,single_page_paths: List[str], out_path: str) -> None:
        writer = PdfWriter()
        for p in single_page_paths:
            reader = PdfReader(p)
            for i in range(len(reader.pages)):
                writer.add_page(reader.pages[i])
        with open(out_path, "wb") as f:
            writer.write(f)


    def ocr_and_replace_pdf(self,pdf_path: str, dpi: int = 300) -> None:
        """Run OCR on scanned PDF using docTR, create a searchable PDF, and replace the original."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Input PDF not found: {pdf_path}")

        logger.info(f"Running OCR on: {pdf_path}")

        # 1) Load PDF into docTR
        docs = DocumentFile.from_pdf(pdf_path)

        # 2) Model + inference
        predictor = ocr_predictor(pretrained=True)
        result = predictor(docs)

        # 3) Export per-page hOCR/XML
        xml_pages: List[Tuple[bytes, object]] = result.export_as_xml()

        # 4) Render pages to images (no pre-opened files)
        page_images = self._render_pdf_pages_to_images(pdf_path, dpi=dpi)

        if len(xml_pages) != len(page_images):
            raise RuntimeError(
                f"Page count mismatch between OCR output ({len(xml_pages)}) and rendered images ({len(page_images)})"
            )

        single_page_outputs: List[str] = []
        hocr_files: List[str] = []
        try:
            # 5) Build searchable single-page PDFs
            for i, (xml_bytes, _xml_tree) in enumerate(xml_pages):
                # Write hOCR to a path (not an open file handle)
                hocr_path = self._unique_tmp_path(".hocr")
                with open(hocr_path, "wb") as hf:
                    hf.write(xml_bytes)
                hocr_files.append(hocr_path)

                out_pdf_path = self._unique_tmp_path(".pdf")

                hocr = HocrTransform(hocr_filename=hocr_path, dpi=float(dpi))
                hocr.to_pdf(
                    out_filename=out_pdf_path,
                    image_filename=page_images[i]
                )
                single_page_outputs.append(out_pdf_path)

            # 6) Merge to final
            merged_pdf_path = self._unique_tmp_path(".pdf")
            self._merge_pdfs(single_page_outputs, merged_pdf_path)

            # 7) Replace original atomically
            os.replace(merged_pdf_path, pdf_path)
            logger.info(f"OCR complete. Replaced original file: {pdf_path}")

        finally:
            # Cleanup temps. Ensure nothing holds open handles to these paths.
            for p in page_images:
                try:
                    os.remove(p)
                except Exception:
                    pass
            for p in single_page_outputs:
                try:
                    os.remove(p)
                except Exception:
                    pass
            for p in hocr_files:
                try:
                    os.remove(p)
                except Exception:
                    pass
