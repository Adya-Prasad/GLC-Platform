import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('esg_rag.log'),
        logging.StreamHandler()
    ]
)

# Directory for storing processed documents metadata
PROCESSED_DOCS_DIR = "./processed_docs"
os.makedirs(PROCESSED_DOCS_DIR, exist_ok=True)

def validate_document_path(doc_path):
    """Validate that the document path exists and is accessible"""
    path = Path(doc_path)
    if not path.exists():
        logging.error(f"Document not found: {doc_path}")
        return False
    
    if not path.is_file():
        logging.error(f"Path is not a file: {doc_path}")
        return False
    
    # Check file extension
    valid_extensions = {'.pdf', '.docx', '.doc', '.txt', '.csv', '.json'}
    if path.suffix.lower() not in valid_extensions:
        logging.warning(f"Unsupported file type: {path.suffix}. Attempting to process as text.")
    
    logging.info(f"Document validated: {doc_path}")
    return True

def format_json_response(questions, answers, metadata=None):
    """
    Format the ESG RAG responses into a structured JSON format
    
    Args:
        questions: List of questions asked
        answers: List of corresponding answers
        metadata: Optional metadata about the processing
    
    Returns:
        Dictionary formatted for JSON output
    """
    response = {
        "timestamp": datetime.now().isoformat(),
        "document": metadata.get("document_path") if metadata else None,
        "organization": "LMA - Loan Management Association",
        "analysis_type": "ESG Report Analysis",
        "total_questions": len(questions),
        "results": []
    }
    
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        result_entry = {
            "question_id": i,
            "question": question,
            "answer": answer if answer else "NOT FOUND",
            "status": "found" if answer and answer != "NOT FOUND" else "not_found"
        }
        response["results"].append(result_entry)
    
    # Add summary
    found_count = sum(1 for r in response["results"] if r["status"] == "found")
    response["summary"] = {
        "questions_answered": found_count,
        "questions_not_found": len(questions) - found_count,
        "completion_rate": f"{(found_count / len(questions) * 100):.1f}%"
    }
    
    if metadata:
        response["processing_info"] = {
            "processing_time": metadata.get("processing_time"),
            "chunks_processed": metadata.get("chunks_processed"),
            "model_used": metadata.get("model_used")
        }
    
    return response

def get_esg_questions():
    """
    Return the predefined ESG questions for LMA loan management analysis
    """
    return [
        "What is the use of proceeds?",
        "List the KPIs and their baseline values.",
        "Is there a management of proceeds description?",
        "What is the SPT target and the target year?",
        "Does the report specify external review or verification procedures?",
        "What are the Scope 1, 2, and 3 emissions?",
        "What are the Nationally Determined Contributions (NDCs), sector-specific pathways, taxonomies, or national carbon budgets?",
        "What is the capital expenditure (CapEx)?",
        "What is the operational expenditure (OpEx)?",
        "What are the sustainability performance targets?",
        "Is there a framework alignment (e.g., GRI, SASB, TCFD)?",
        "What are the environmental risk factors identified?",
        "What are the social impact metrics?",
        "What governance structures are in place for ESG oversight?"
    ]

def log_processing_start(doc_path):
    """Log the start of document processing"""
    logging.info("="*80)
    logging.info("ESG RAG ANALYSIS STARTED")
    logging.info(f"Document: {doc_path}")
    logging.info(f"Organization: LMA - Loan Management Association")
    logging.info("="*80)

def log_processing_end(success=True):
    """Log the end of document processing"""
    logging.info("="*80)
    if success:
        logging.info("ESG RAG ANALYSIS COMPLETED SUCCESSFULLY")
    else:
        logging.error("ESG RAG ANALYSIS FAILED")
    logging.info("="*80)

def save_results_to_file(json_response, output_path=None):
    """
    Save JSON results to a file
    
    Args:
        json_response: Dictionary to save
        output_path: Optional custom output path
    """
    import json
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"esg_analysis_{timestamp}.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_response, f, indent=2, ensure_ascii=False)
        logging.info(f"Results saved to: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Failed to save results: {e}")
        return None