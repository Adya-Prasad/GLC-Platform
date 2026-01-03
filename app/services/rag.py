"""
RAG Service
Retrieval-Augmented Generation for document analysis and verification.
"""

import logging
from typing import List, Dict, Any
from app.services.nlp import nlp_service
from app.utils.faiss_index import get_index
from app.core.config import EXTRACTION_QUESTIONS

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for document retrieval and QA composition."""
    
    def __init__(self):
        self.top_k = 6
    
    def retrieve_passages(self, loan_app_id: int, query: str, k: int = 6) -> List[Dict[str, Any]]:
        """Retrieve relevant passages for a query."""
        index = get_index(loan_app_id)
        query_embedding = nlp_service.embed_text(query)
        results = index.search(query_embedding, k=k)
        return results
    
    def answer_question(self, loan_app_id: int, question: str) -> Dict[str, Any]:
        """Answer a question using RAG over document chunks."""
        passages = self.retrieve_passages(loan_app_id, question, k=self.top_k)
        
        if not passages:
            return {
                'question': question,
                'answer': 'No relevant documents found',
                'confidence': 0.0,
                'evidence': []
            }
        
        # Get passage texts
        passage_texts = [p['chunk_text'] for p in passages]
        
        # Use RAG composition
        result = nlp_service.extract_with_rag(question, passage_texts)
        
        return {
            'question': question,
            'answer': result.get('answer', ''),
            'confidence': result.get('confidence', 0.5),
            'evidence': [{'doc_id': p.get('document_id'), 'text': p['chunk_text'][:200], 'score': p.get('score', 0)} for p in passages[:3]]
        }
    
    def run_extraction_questions(self, loan_app_id: int) -> Dict[str, Dict[str, Any]]:
        """Run all standard extraction questions."""
        results = {}
        for question in EXTRACTION_QUESTIONS:
            key = question.lower().replace(' ', '_').replace('?', '')[:30]
            results[key] = self.answer_question(loan_app_id, question)
        return results
    
    def verify_claim(self, loan_app_id: int, claim: str) -> Dict[str, Any]:
        """Verify a claim against document evidence."""
        passages = self.retrieve_passages(loan_app_id, claim, k=4)
        
        if not passages:
            return {
                'claim': claim,
                'verified': False,
                'confidence': 0.0,
                'conclusion': 'No evidence found',
                'evidence': []
            }
        
        # Check if claim is supported by passages
        combined = ' '.join([p['chunk_text'] for p in passages])
        result = nlp_service.extract_answer(f"Does the document support: {claim}?", combined)
        
        confidence = result.get('confidence', 0)
        verified = confidence >= 0.6
        conclusion = 'Verified' if verified else 'Unclear' if confidence >= 0.4 else 'Unverified'
        
        return {
            'claim': claim,
            'verified': verified,
            'confidence': confidence,
            'conclusion': conclusion,
            'evidence': [{'doc_id': p.get('document_id'), 'text': p['chunk_text'][:200]} for p in passages[:2]]
        }


rag_service = RAGService()
