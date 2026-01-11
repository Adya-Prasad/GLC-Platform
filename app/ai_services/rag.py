# app/ai_services/rag.py

import logging
import re
from typing import List, Dict, Any

from app.ai_services.config import settings, EXTRACTION_QUESTIONS
from app.ai_services.embedding import embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    Not just “RAG”, but a multi-strategy answer engine
    RAG Service using HuggingFace pipeline for Q&A.
    Lazy-loads models to avoid startup delays.
    """
    
    def __init__(self):
        self._qa_pipeline = None
        self._generator = None
    
    def _ensure_qa_pipeline(self):
        """Lazy load the QA pipeline."""
        if self._qa_pipeline is not None:
            return
        
        try:
            from transformers import pipeline
            self._qa_pipeline = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2",
                device=-1  # CPU
            )
            logger.info("Loaded QA pipeline: deepset/roberta-base-squad2")
        except Exception as e:
            logger.error(f"Failed to load QA pipeline: {e}")
            raise
    
    def _ensure_generator(self):
        """Lazy load text generation model."""
        if self._generator is not None:
            return
        
        try:
            from transformers import pipeline
            self._generator = pipeline(
                "text2text-generation",
                model=settings.RAG_LLM_MODEL,
                device=-1
            )
            logger.info(f"Loaded generator: {settings.RAG_LLM_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load generator: {e}")
            raise
    
    def _build_context(self, results: List[Dict], max_length: int = 3000) -> str:
        """Build context string from search results."""
        context_parts = []
        total_length = 0
        
        for result in results:
            text = result.get("text", "").strip()
            if not text:
                continue
            if total_length + len(text) > max_length:
                remaining = max_length - total_length
                if remaining > 200:
                    context_parts.append(text[:remaining])
                break
            context_parts.append(text)
            total_length += len(text)
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, results: List[Dict]) -> List[Dict]:
        """Format source metadata for output."""
        return [
            {
                "text_snippet": r.get("text", "")[:200],
                "source": r.get("source", ""),
                "score": round(r.get("score", 0), 3)
            }
            for r in results[:3]
        ]
    
    def _is_valid_answer(self, answer: str) -> bool:
        """Check if answer is meaningful and not garbage."""
        if not answer or len(answer.strip()) < 3:
            return False
        
        # Reject answers that are just numbers, roman numerals, or single words
        cleaned = answer.strip().lower()
        
        # Reject pure numbers or roman numerals
        if re.match(r'^[\d\.\,\(\)\[\]ivxlcdm\s]+$', cleaned):
            return False
        
        # Reject very short answers (likely fragments)
        if len(cleaned) < 10 and not any(c.isalpha() for c in cleaned):
            return False
        
        # Reject answers that are just punctuation or special chars
        if re.match(r'^[\W\d]+$', cleaned):
            return False
        
        # Reject common garbage patterns
        garbage_patterns = [
            r'^\([ivx]+\)\.?$',  # (i), (ii), (iii)
            r'^\[[ivx]+\]\.?$',  # [i], [ii], [iii]
            r'^\(\d+\)\.?$',     # (1), (2), (3)
            r'^[a-z]\)\.?$',     # a), b), c)
            r'^•\s*$',           # bullet points
            r'^\d+\.\s*$',       # numbered lists
        ]
        for pattern in garbage_patterns:
            if re.match(pattern, cleaned):
                return False
        
        return True

    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using T5 model - more reliable for complex questions."""
        try:
            self._ensure_generator()
            
            # Create a focused prompt
            prompt = f"""Act as Loan Manager and answer the question based on the context. If the answer is not in the context, say just "Not found".

Context: {context[:2000]}

Question: {question}

Answer:"""
            
            result = self._generator(
                prompt,
                max_new_tokens=100,
                do_sample=False,
                num_beams=2
            )
            
            answer = result[0]["generated_text"].strip()
            
            # Clean up common T5 artifacts
            if answer.lower().startswith("answer:"):
                answer = answer[7:].strip()
            
            return answer if self._is_valid_answer(answer) else None
            
        except Exception as e:
            logger.warning(f"Generation failed: {e}")
            return None
    
    def _extract_with_qa(self, question: str, context: str) -> tuple:
        """Use QA model for extraction, returns (answer, confidence)."""
        try:
            self._ensure_qa_pipeline()
            
            result = self._qa_pipeline(
                question=question,
                context=context,
                max_answer_len=150,
                handle_impossible_answer=True
            )
            
            answer = result.get("answer", "").strip()
            score = result.get("score", 0)
            
            # Only accept high-confidence, valid answers
            if score > 0.5 and self._is_valid_answer(answer):
                return answer, score
            
            return None, 0
            
        except Exception as e:
            logger.warning(f"QA extraction failed: {e}")
            return None, 0
    
    ## === Heart of the file === 
    def query(self, question: str, loan_id: int, doc_type: str = None) -> Dict[str, Any]:
        """
        RAG query combining retrieval with QA/generation.
        """
        # Search for relevant chunks
        results = embedding_service.search(question, loan_id=loan_id, k=settings.FAISS_TOP_K)
        
        if not results:
            return {
                "question": question,
                "answer": "No documents indexed for this loan.",
                "confidence": 0.0,
                "sources": []
            }
        
        context = self._build_context(results)
        
        if not context.strip():
            return {
                "question": question,
                "answer": "No relevant content found in documents.",
                "confidence": 0.0,
                "sources": []
            }
        
        # Try QA extraction first (faster, good for factual questions)
        qa_answer, qa_confidence = self._extract_with_qa(question, context)
        
        if qa_answer and qa_confidence > 0.6:
            return {
                "question": question,
                "answer": qa_answer,
                "confidence": float(qa_confidence),
                "sources": self._format_sources(results)
            }
        
        # Fall back to generative model for complex questions
        gen_answer = self._generate_answer(question, context)
        
        if gen_answer and gen_answer.lower() not in ["not found", "not found.", "unknown", "just not found"]:
            return {
                "question": question,
                "answer": gen_answer,
                "confidence": 0.7,  # Moderate confidence for generated
                "sources": self._format_sources(results)
            }
        
        # If QA had some answer (even low confidence), use it as last resort
        if qa_answer:
            return {
                "question": question,
                "answer": qa_answer,
                "confidence": float(qa_confidence),
                "sources": self._format_sources(results)
            }
        
        return {
            "question": question,
            "answer": "Could not extract a clear answer from the documents.",
            "confidence": 0.0,
            "sources": self._format_sources(results)
        }
    
    def chat(self, message: str, loan_id: int) -> Dict[str, Any]:
        """Chat interface - wraps query method."""
        result = self.query(message, loan_id)
        return {
            "answer": result["answer"],
            "confidence": result["confidence"],
            "sources": result["sources"]
        }
    
    def extract_all_questions(self, loan_id: int) -> List[Dict]:
        """Extract answers to all predefined LMA questions."""
        extractions = []
        
        for question in EXTRACTION_QUESTIONS:
            response = self.query(question, loan_id)
            
            answer = response["answer"]
            confidence = response["confidence"]
            
            # Determine if answer was actually found
            not_found_phrases = [
                "no documents", "not found", "could not extract", 
                "no relevant", "unknown", "not available"
            ]
            found = confidence > 0.3 and not any(p in answer.lower() for p in not_found_phrases)
            
            extractions.append({
                "question": question,
                "answer": answer if found else "Not found in documents",
                "confidence": confidence,
                "found": found
            })
        
        return extractions


# Singleton instance
rag_service = RAGService()
