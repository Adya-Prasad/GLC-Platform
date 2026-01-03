"""
File Storage Utilities
Manage file uploads and storage for documents.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.core.config import settings


def get_upload_dir(loan_app_id: int) -> Path:
    """Get upload directory for a loan application."""
    upload_dir = settings.UPLOAD_DIR / str(loan_app_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def save_upload_file(upload_file: UploadFile, loan_app_id: int) -> str:
    """Save uploaded file and return the filepath."""
    upload_dir = get_upload_dir(loan_app_id)
    
    # Sanitize filename
    filename = os.path.basename(upload_file.filename or "document")
    filepath = upload_dir / filename
    
    # Handle duplicates
    counter = 1
    original_stem = filepath.stem
    while filepath.exists():
        filepath = upload_dir / f"{original_stem}_{counter}{filepath.suffix}"
        counter += 1
    
    # Save file
    with open(filepath, "wb") as f:
        content = await upload_file.read()
        f.write(content)
    
    return str(filepath)


def delete_file(filepath: str) -> bool:
    """Delete a file if it exists."""
    try:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            return True
    except Exception:
        pass
    return False


def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except Exception:
        return 0


def get_file_type(filename: str) -> str:
    """Get file type from filename."""
    ext = Path(filename).suffix.lower()
    type_map = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return type_map.get(ext, 'application/octet-stream')
