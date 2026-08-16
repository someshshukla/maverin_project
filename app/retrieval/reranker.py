import logging
from typing import List, Tuple
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None


class Reranker:
    """Cross-Encoder reranking module for retrieved candidates."""
    
    def __init__(self, model_name: str = settings.RERANKER_MODEL):
        self.model_name = model_name
        self.model = None
        self._load_model()
        
    def _load_model(self):
        if CrossEncoder:
            try:
                self.model = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder model {self.model_name}: {e}. Using fallback score reranker.")
                self.model = None

    def rerank(self, query: str, candidates: List[Tuple[ChunkMetadata, float]], top_k: int = settings.RERANK_TOP_K) -> List[Tuple[ChunkMetadata, float]]:
        """Reranks (chunk, initial_score) candidates and returns top_k highest relevance chunks."""
        if not candidates:
            return []
            
        if self.model:
            pairs = [[query, chunk.text] for chunk, _ in candidates]
            scores = self.model.predict(pairs)
            scored_candidates = [(candidates[i][0], float(scores[i])) for i in range(len(candidates))]
        else:
            # Fallback reranker using term density + initial hybrid score
            query_terms = set(query.lower().split())
            scored_candidates = []
            for chunk, initial_score in candidates:
                chunk_lower = chunk.text.lower()
                matches = sum(1 for t in query_terms if t in chunk_lower)
                density = matches / (len(query_terms) + 1)
                boosted_score = initial_score * 0.4 + density * 0.6
                scored_candidates.append((chunk, float(boosted_score)))
                
        # Sort by rerank score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]
