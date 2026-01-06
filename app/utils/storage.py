"""
File Storage Utilities
Manage file uploads and storage for documents.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile
from app.core.config import settings


# Document category to standardized filename mapping
DOCUMENT_CATEGORY_NAMES = {
    "sustainability_report": "sustainability_report",
    "eia": "environmental_impact_assessment",
    "certification_1": "certification_primary",
    "certification_2": "certification_secondary",
    "additional_data": "additional_data",
    "general": "document"
}


def get_loan_dir(loan_id: str) -> Path:
    """Get directory for a loan application using loan_id (LOAN_1, LOAN_2, etc.)."""
    loan_dir = settings.UPLOAD_DIR / loan_id
    loan_dir.mkdir(parents=True, exist_ok=True)
    return loan_dir


def get_upload_dir(loan_id: int) -> Path:
    """Get upload directory for a loan application (legacy support using numeric id)."""
    upload_dir = settings.UPLOAD_DIR / str(loan_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


async def save_upload_file(
    upload_file: UploadFile, 
    loan_id: int,
    loan_id_str: str = None,
    category: str = "general"
) -> str:
    """
    Save uploaded file with standardized naming.
    
    Args:
        upload_file: The uploaded file
        loan_id: Numeric loan ID (for backward compatibility)
        loan_id_str: String loan ID (LOAN_1, LOAN_2, etc.)
        category: Document category for naming
    
    Returns:
        Filepath where file was saved
    """
    # Use string loan_id if provided, otherwise use numeric
    if loan_id_str:
        upload_dir = get_loan_dir(loan_id_str)
    else:
        upload_dir = get_upload_dir(loan_id)
    
    # Get original file extension
    original_filename = upload_file.filename or "document"
    ext = Path(original_filename).suffix.lower()
    
    # Get standardized name based on category
    base_name = DOCUMENT_CATEGORY_NAMES.get(category, category)
    
    # Create standardized filename
    filename = f"{base_name}{ext}"
    filepath = upload_dir / filename
    
    # Handle duplicates by adding timestamp
    if filepath.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}{ext}"
        filepath = upload_dir / filename
    
    # Save file
    with open(filepath, "wb") as f:
        content = await upload_file.read()
        f.write(content)
    
    return str(filepath)


def save_application_json(loan_id_str: str, application_data: Dict[str, Any]) -> str:
    """
    Save raw application data as JSON file in the loan directory.
    
    Args:
        loan_id_str: String loan ID (LOAN_1, LOAN_2, etc.)
        application_data: Raw application data dictionary
    
    Returns:
        Filepath where JSON was saved
    """
    loan_dir = get_loan_dir(loan_id_str)
    
    # Add metadata
    json_data = {
        "loan_id": loan_id_str,
        "submitted_at": datetime.utcnow().isoformat(),
        "application_data": application_data
    }
    
    # Save as JSON
    json_path = loan_dir / "application_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
    
    return str(json_path)


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
        '.json': 'application/json',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return type_map.get(ext, 'application/octet-stream')


def get_standardized_filename(category: str, original_filename: str) -> str:
    """Get standardized filename for a document category."""
    ext = Path(original_filename).suffix.lower()
    base_name = DOCUMENT_CATEGORY_NAMES.get(category, category)
    return f"{base_name}{ext}"
