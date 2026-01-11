# app/ai_services/embedding.py

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from app.ai_services.config import settings

logger = logging.getLogger(__name__)

VECTOR_PATH = Path(settings.VECTOR_STORE_PATH)
VECTOR_PATH.mkdir(parents=True, exist_ok=True)


class EmbeddingService:
    """
    Embedding service using sentence-transformers and FAISS.
    Lazy-loads models to avoid startup delays.
    """
    
    def __init__(self):
        self._model = None
        self._index = None
        self._metadata: List[Dict] = []
        self.index_file = VECTOR_PATH / "faiss_index.bin"
        self.metadata_file = VECTOR_PATH / "metadata.pkl"
        self._initialized = False
    
    def _ensure_model(self):
        """Lazy load the embedding model."""
        if self._model is not None:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _ensure_index(self):
        """Initialize or load FAISS index."""
        if self._initialized:
            return
        
        try:
            import faiss
            
            # Try to load existing index
            if self.index_file.exists() and self.metadata_file.exists():
                self._index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, 'rb') as f:
                    self._metadata = pickle.load(f)
                logger.info(f"Loaded existing index with {len(self._metadata)} chunks")
            else:
                # Create new index
                self._ensure_model()
                dim = self._model.get_sentence_embedding_dimension()
                self._index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity
                self._metadata = []
                logger.info(f"Created new FAISS index with dimension {dim}")
            
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise
    
    def _save_index(self):
        """Persist index / layer and metadata to disk."""
        try:
            import faiss
            faiss.write_index(self._index, str(self.index_file))
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self._metadata, f)
            logger.debug("Saved index to disk")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def add_chunks(self, chunks: List[Any], loan_id: int) -> int:
        """
        Add document chunks to the index.
        
        Args:
            chunks: List of Document objects with page_content and metadata
            loan_id: Loan application ID
        
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        self._ensure_model()
        self._ensure_index()
        
        # Extract texts from chunks
        texts = []
        for chunk in chunks:
            if hasattr(chunk, 'page_content'):
                texts.append(chunk.page_content)
            elif hasattr(chunk, 'text'):
                texts.append(chunk.text)
            elif isinstance(chunk, str):
                texts.append(chunk)
            else:
                texts.append(str(chunk))
        
        # Generate embeddings with normalization, required for cosine similarity with IndexFlatI
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        self._index.add(embeddings_array)
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            metadata = {}
            if hasattr(chunk, 'metadata'):
                metadata = chunk.metadata.copy() if chunk.metadata else {}
            
            self._metadata.append({
                "loan_id": loan_id,
                "text": texts[i],
                "source": metadata.get("source", ""),
                "page": metadata.get("page"),
                "doc_type": metadata.get("doc_type", "")
            })
        
        # Persist to disk
        self._save_index()
        
        logger.info(f"Added {len(chunks)} chunks for loan {loan_id}")
        return len(chunks)
    
    def search(
        self, 
        query: str, 
        loan_id: Optional[int] = None, 
        k: int = 5,
        doc_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using semantic similarity.
        
        Args:
            query: Search query text
            loan_id: Filter by loan ID (optional)
            k: Number of results to return
            doc_type: Filter by document type (optional)
        
        Returns:
            List of matching chunks with metadata
        """
        self._ensure_model()
        self._ensure_index()
        
        if self._index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self._model.encode(query, normalize_embeddings=True)
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search more than needed to allow for filtering
        search_k = min(k * 3, self._index.ntotal)
        scores, indices = self._index.search(query_array, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self._metadata):
                continue
            
            entry = self._metadata[idx]
            
            # Apply filters
            if loan_id is not None and entry.get("loan_id") != loan_id:
                continue
            
            if doc_type is not None and entry.get("doc_type") != doc_type:
                continue
            
            result = entry.copy()
            result["score"] = float(score)
            results.append(result)
            
            if len(results) >= k:
                break
        
        return results
    
    def get_stats(self, loan_id: Optional[int] = None) -> Dict[str, Any]:
        """Get index statistics."""
        self._ensure_index()
        
        if loan_id is not None:
            loan_chunks = [m for m in self._metadata if m.get("loan_id") == loan_id]
            return {
                "loan_id": loan_id,
                "chunk_count": len(loan_chunks),
                "sources": list(set(m.get("source", "") for m in loan_chunks))
            }
        
        return {
            "total_chunks": len(self._metadata),
            "index_size": self._index.ntotal if self._index else 0,
            "unique_loans": len(set(m.get("loan_id") for m in self._metadata))
        }
    
    def clear_loan(self, loan_id: int) -> int:
        """
        Remove all chunks for a specific loan.
        Note: Rebuilds the index since FAISS doesn't support deletion.
        """
        self._ensure_index()
        
        # Find chunks to keep
        keep_indices = [i for i, m in enumerate(self._metadata) if m.get("loan_id") != loan_id]
        removed_count = len(self._metadata) - len(keep_indices)
        
        if removed_count == 0:
            return 0
        
        # Rebuild index
        import faiss
        self._ensure_model()
        dim = self._model.get_sentence_embedding_dimension()
        new_index = faiss.IndexFlatIP(dim)
        
        new_metadata = []
        if keep_indices:
            texts = [self._metadata[i]["text"] for i in keep_indices]
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            new_index.add(np.array(embeddings).astype('float32'))
            new_metadata = [self._metadata[i] for i in keep_indices]
        
        self._index = new_index
        self._metadata = new_metadata
        self._save_index()
        
        logger.info(f"Removed {removed_count} chunks for loan {loan_id}")
        return removed_count


# Singleton instance - lazy loaded
embedding_service = EmbeddingService()
