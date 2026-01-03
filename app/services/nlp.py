"""
NLP Service
Natural Language Processing using HuggingFace models for text extraction and analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import numpy as np

# Lazy imports to avoid loading models until needed
_embedding_model = None
_qa_pipeline = None
_summarizer = None

logger = logging.getLogger(__name__)


def get_embedding_model():
    """Lazy load the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import settings
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            _embedding_model = MockEmbeddingModel()
    return _embedding_model


def get_qa_pipeline():
    """Lazy load the QA pipeline."""
    global _qa_pipeline
    if _qa_pipeline is None:
        try:
            from transformers import pipeline
            from app.core.config import settings
            logger.info(f"Loading QA model: {settings.QA_MODEL}")
            _qa_pipeline = pipeline("question-answering", model=settings.QA_MODEL)
            logger.info("QA model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load QA model: {e}")
            _qa_pipeline = MockQAPipeline()
    return _qa_pipeline


def get_summarizer():
    """Lazy load the summarization model."""
    global _summarizer
    if _summarizer is None:
        try:
            from transformers import pipeline
            from app.core.config import settings
            logger.info(f"Loading RAG/summarization model: {settings.RAG_MODEL}")
            _summarizer = pipeline("text2text-generation", model=settings.RAG_MODEL)
            logger.info("Summarization model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load summarization model: {e}")
            _summarizer = MockSummarizer()
    return _summarizer


class MockEmbeddingModel:
    """Mock embedding model for development without GPU."""
    
    def encode(self, texts: List[str], **kwargs) -> np.ndarray:
        """Generate random embeddings for testing."""
        if isinstance(texts, str):
            texts = [texts]
        # Return consistent random embeddings based on text hash
        embeddings = []
        for text in texts:
            np.random.seed(hash(text) % 2**32)
            embeddings.append(np.random.randn(384).astype(np.float32))
        return np.array(embeddings)


class MockQAPipeline:
    """Mock QA pipeline for development without GPU."""
    
    def __call__(self, question: str, context: str, **kwargs) -> Dict[str, Any]:
        """Return mock QA results based on keywords."""
        context_lower = context.lower()
        
        # Simple keyword-based extraction
        if "use of proceeds" in question.lower():
            if "wind" in context_lower:
                return {"answer": "Construction of wind energy facilities", "score": 0.85}
            elif "solar" in context_lower:
                return {"answer": "Solar panel installation and maintenance", "score": 0.82}
            elif "renewable" in context_lower:
                return {"answer": "Renewable energy infrastructure development", "score": 0.80}
        
        if "kpi" in question.lower() or "baseline" in question.lower():
            return {"answer": "CO2 emissions reduction, energy efficiency metrics", "score": 0.75}
        
        if "spt" in question.lower() or "target" in question.lower():
            return {"answer": "30% reduction by 2030", "score": 0.78}
        
        if "scope" in question.lower() or "emission" in question.lower():
            return {"answer": "Scope 1: 25000 tCO2, Scope 2: 10000 tCO2, Scope 3: 5000 tCO2", "score": 0.72}
        
        # Default response
        return {"answer": context[:200] if len(context) > 200 else context, "score": 0.60}


class MockSummarizer:
    """Mock summarizer for development without GPU."""
    
    def __call__(self, text: str, **kwargs) -> List[Dict[str, str]]:
        """Return simplified summary."""
        # Simple extractive summary - take first few sentences
        sentences = text.split('. ')[:3]
        summary = '. '.join(sentences)
        if not summary.endswith('.'):
            summary += '.'
        return [{"generated_text": summary}]


class NLPService:
    """Main NLP service for text analysis and extraction."""
    
    def __init__(self):
        self.chunk_size = 500  # tokens
        self.chunk_overlap = 50
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        model = get_embedding_model()
        return model.encode([text])[0]
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        model = get_embedding_model()
        return model.encode(texts, show_progress_bar=True)
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for embedding.
        Returns list of dicts with chunk_text, start_char, end_char.
        """
        # Simple word-based chunking (approximating tokens)
        words = text.split()
        chunks = []
        
        # Approximate tokens as words (rough estimate)
        chunk_words = self.chunk_size
        overlap_words = self.chunk_overlap
        
        start_idx = 0
        chunk_index = 0
        
        while start_idx < len(words):
            end_idx = min(start_idx + chunk_words, len(words))
            chunk_words_list = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words_list)
            
            # Calculate character positions
            if start_idx == 0:
                start_char = 0
            else:
                start_char = len(' '.join(words[:start_idx])) + 1
            
            end_char = start_char + len(chunk_text)
            
            chunks.append({
                'chunk_index': chunk_index,
                'chunk_text': chunk_text,
                'start_char': start_char,
                'end_char': end_char,
                'token_count': len(chunk_words_list)
            })
            
            # Move to next chunk with overlap
            start_idx = end_idx - overlap_words if end_idx < len(words) else len(words)
            chunk_index += 1
        
        return chunks
    
    def extract_answer(self, question: str, context: str) -> Dict[str, Any]:
        """
        Use extractive QA to answer a question from context.
        Returns answer text and confidence score.
        """
        qa = get_qa_pipeline()
        
        try:
            result = qa(question=question, context=context[:4096])  # Limit context length
            return {
                'answer': result['answer'],
                'confidence': result['score'],
                'question': question
            }
        except Exception as e:
            logger.error(f"QA extraction error: {e}")
            return {
                'answer': '',
                'confidence': 0.0,
                'question': question,
                'error': str(e)
            }
    
    def extract_with_rag(
        self, 
        question: str, 
        passages: List[str],
        max_length: int = 256
    ) -> Dict[str, Any]:
        """
        Use RAG to compose answer from multiple passages.
        """
        summarizer = get_summarizer()
        
        # Combine passages
        combined_context = "\n\n".join(passages[:5])  # Limit to top 5 passages
        
        # Create RAG prompt
        prompt = f"""Based on the following context, answer the question concisely.

Context:
{combined_context[:2000]}

Question: {question}

Answer:"""
        
        try:
            result = summarizer(prompt, max_length=max_length, min_length=20)
            return {
                'answer': result[0]['generated_text'],
                'question': question,
                'num_passages': len(passages)
            }
        except Exception as e:
            logger.error(f"RAG composition error: {e}")
            # Fallback to extractive QA on combined context
            return self.extract_answer(question, combined_context)
    
    def summarize_text(self, text: str, max_length: int = 150) -> str:
        """Generate a summary of the given text."""
        summarizer = get_summarizer()
        
        try:
            prompt = f"Summarize the following text:\n\n{text[:2000]}"
            result = summarizer(prompt, max_length=max_length, min_length=30)
            return result[0]['generated_text']
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            # Return first few sentences as fallback
            sentences = text.split('. ')[:3]
            return '. '.join(sentences) + '.'
    
    def extract_kpis(self, text: str) -> List[Dict[str, Any]]:
        """Extract KPIs and their values from text."""
        kpis = []
        
        # Common KPI patterns
        kpi_patterns = [
            ("CO2 emissions", "tCO2/year"),
            ("Scope 1 emissions", "tCO2"),
            ("Scope 2 emissions", "tCO2"),
            ("Scope 3 emissions", "tCO2"),
            ("Energy efficiency", "%"),
            ("Renewable energy share", "%"),
            ("Water consumption", "m³"),
            ("Waste reduction", "%"),
        ]
        
        for kpi_name, unit in kpi_patterns:
            result = self.extract_answer(
                f"What is the {kpi_name}?",
                text
            )
            if result['confidence'] > 0.5:
                kpis.append({
                    'kpi_name': kpi_name,
                    'unit': unit,
                    'extracted_value': result['answer'],
                    'confidence': result['confidence']
                })
        
        return kpis
    
    def classify_glp_category(self, use_of_proceeds: str) -> Tuple[str, float]:
        """
        Classify project into GLP category based on use of proceeds.
        Returns category and confidence score.
        """
        from app.core.config import GLP_CATEGORIES
        
        use_lower = use_of_proceeds.lower()
        
        # Simple keyword-based classification
        category_keywords = {
            "Renewable Energy": ["wind", "solar", "hydro", "geothermal", "renewable", "clean energy"],
            "Energy Efficiency": ["efficiency", "energy saving", "retrofit", "insulation", "led", "smart grid"],
            "Pollution Prevention and Control": ["pollution", "emission", "waste treatment", "air quality"],
            "Clean Transportation": ["electric vehicle", "ev", "public transport", "rail", "cycling", "hydrogen"],
            "Sustainable Water and Wastewater Management": ["water", "wastewater", "desalination", "irrigation"],
            "Green Buildings": ["green building", "leed", "breeam", "sustainable construction", "net zero building"],
            "Climate Change Adaptation": ["adaptation", "resilience", "flood defense", "climate risk"],
            "Terrestrial and Aquatic Biodiversity Conservation": ["biodiversity", "conservation", "habitat", "ecosystem"],
            "Eco-efficient and/or Circular Economy Adapted Products": ["circular", "recycling", "sustainable product"],
            "Environmentally Sustainable Management of Living Natural Resources and Land Use": ["sustainable forest", "agriculture", "land use"],
        }
        
        max_score = 0.0
        best_category = "Unknown"
        
        for category, keywords in category_keywords.items():
            matches = sum(1 for kw in keywords if kw in use_lower)
            if matches > 0:
                score = min(0.95, 0.5 + (matches * 0.15))
                if score > max_score:
                    max_score = score
                    best_category = category
        
        if max_score == 0:
            # Default to best guess based on common patterns
            if any(word in use_lower for word in ["energy", "power", "electricity"]):
                return "Renewable Energy", 0.4
            return "Unknown", 0.0
        
        return best_category, max_score


# Singleton instance
nlp_service = NLPService()
