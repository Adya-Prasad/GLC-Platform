"""
FAISS Index Utilities
Vector storage and retrieval using FAISS for semantic search.
"""

import logging
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

_faiss_available = True
try:
    import faiss
except ImportError:
    _faiss_available = False
    logger.warning("FAISS not available, using mock vector search")


class FAISSIndex:
    """Manages FAISS index for document chunk retrieval."""
    
    def __init__(self, loan_id: int, dimension: int = 384):
        self.loan_id = loan_id
        self.dimension = dimension
        self.index_path = settings.FAISS_INDEX_DIR / f"index_{loan_id}.faiss"
        self.mapping_path = settings.FAISS_INDEX_DIR / f"mapping_{loan_id}.pkl"
        self.index = None
        self.chunk_mapping: List[Dict[str, Any]] = []
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        if _faiss_available:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with open(self.mapping_path, 'rb') as f:
                    self.chunk_mapping = pickle.load(f)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
                self.chunk_mapping = []
        else:
            self.index = MockFAISSIndex(self.dimension)
            self.chunk_mapping = []
    
    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]]):
        """Add embeddings with metadata to the index."""
        if len(embeddings) == 0:
            return
        embeddings = embeddings.astype(np.float32)
        if _faiss_available:
            self.index.add(embeddings)
        else:
            self.index.add(embeddings)
        self.chunk_mapping.extend(metadata)
        self._save_index()
    
    def search(self, query_embedding: np.ndarray, k: int = 6) -> List[Dict[str, Any]]:
        """Search for similar chunks."""
        query = query_embedding.astype(np.float32).reshape(1, -1)
        k = min(k, len(self.chunk_mapping)) if self.chunk_mapping else 0
        if k == 0:
            return []
        if _faiss_available:
            distances, indices = self.index.search(query, k)
        else:
            distances, indices = self.index.search(query, k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.chunk_mapping) and idx >= 0:
                result = self.chunk_mapping[idx].copy()
                result['distance'] = float(distances[0][i])
                result['score'] = 1 / (1 + float(distances[0][i]))
                results.append(result)
        return results
    
    def _save_index(self):
        if _faiss_available and self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
        with open(self.mapping_path, 'wb') as f:
            pickle.dump(self.chunk_mapping, f)
    
    def clear(self):
        if _faiss_available:
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            self.index = MockFAISSIndex(self.dimension)
        self.chunk_mapping = []
        if self.index_path.exists():
            self.index_path.unlink()
        if self.mapping_path.exists():
            self.mapping_path.unlink()


class MockFAISSIndex:
    """Mock FAISS index for development without FAISS."""
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = []
    
    def add(self, embeddings: np.ndarray):
        self.vectors.extend(embeddings)
    
    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        if not self.vectors:
            return np.array([[0.0] * k]), np.array([[-1] * k])
        vectors = np.array(self.vectors)
        distances = np.linalg.norm(vectors - query, axis=1)
        indices = np.argsort(distances)[:k]
        return np.array([distances[indices]]), np.array([indices])


def get_index(loan_id: int) -> FAISSIndex:
    """Get or create FAISS index for a loan application."""
    return FAISSIndex(loan_id)
