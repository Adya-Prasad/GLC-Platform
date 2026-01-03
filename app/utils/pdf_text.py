"""
PDF Text Extraction Utilities
Extract text from PDF documents using pdfminer with OCR fallback.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF file using pdfminer, with OCR fallback."""
    text = ""
    
    # Try pdfminer first
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        text = pdfminer_extract(filepath)
        if text and len(text.strip()) > 100:
            logger.info(f"Extracted {len(text)} chars from {filepath} using pdfminer")
            return text.strip()
    except Exception as e:
        logger.warning(f"pdfminer extraction failed: {e}")
    
    # Try PyPDF2 as secondary option
    try:
        import PyPDF2
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(pages)
            if text and len(text.strip()) > 100:
                logger.info(f"Extracted {len(text)} chars using PyPDF2")
                return text.strip()
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")
    
    # OCR fallback with pytesseract
    try:
        import pytesseract
        from pdf2image import convert_from_path
        images = convert_from_path(filepath, dpi=200)
        pages = [pytesseract.image_to_string(img) for img in images]
        text = "\n\n".join(pages)
        logger.info(f"Extracted {len(text)} chars using OCR")
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR extraction failed: {e}")
    
    return text


def extract_text_from_docx(filepath: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def extract_text_from_file(filepath: str) -> str:
    """Extract text from file based on extension."""
    path = Path(filepath)
    ext = path.suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(filepath)
    elif ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        logger.warning(f"Unsupported file type: {ext}")
        return ""
