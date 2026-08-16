from typing import List, Tuple, Optional, Dict
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.reranker import Reranker

class HybridRetriever:
    """Hybrid Retriever combining FAISS Vector search and BM25 lexical search with Reciprocal Rank Fusion (RRF) and Reranking."""
    
    def __init__(self, vector_store: VectorStore = None, bm25_retriever: BM25Retriever = None, reranker: Reranker = None):
        self.vector_store = vector_store or VectorStore()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.reranker = reranker or Reranker()

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Tuple[ChunkMetadata, float]],
        bm25_results: List[Tuple[ChunkMetadata, float]],
        k: int = 60
    ) -> List[Tuple[ChunkMetadata, float]]:
        """Combines two ranked lists using Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, ChunkMetadata] = {}

        # Process vector results
        for rank, (chunk, score) in enumerate(vector_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        # Process BM25 results
        for rank, (chunk, score) in enumerate(bm25_results):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank + 1))

        # Sort by merged RRF score
        fused = [(chunk_map[cid], score) for cid, score in rrf_scores.items()]
        fused.sort(key=lambda x: x[1], reverse=True)
        return fused

    def retrieve(
        self,
        query: str,
        spec_filter: Optional[str] = None,
        release_filter: Optional[str] = None,
        top_k: int = settings.TOP_K,
        rerank_top_k: int = settings.RERANK_TOP_K
    ) -> List[Tuple[ChunkMetadata, float]]:
        """Full hybrid retrieval pipeline: Vector + BM25 -> RRF merge -> Cross-Encoder Reranker."""
        # 1. Fetch top K candidates from Vector search
        vec_candidates = self.vector_store.search(
            query, top_k=top_k, spec_filter=spec_filter, release_filter=release_filter
        )
        
        # 2. Fetch top K candidates from BM25 lexical search
        bm25_candidates = self.bm25_retriever.search(
            query, top_k=top_k, spec_filter=spec_filter, release_filter=release_filter
        )
        
        # 3. Combine with RRF
        fused_candidates = self.reciprocal_rank_fusion(vec_candidates, bm25_candidates)
        
        # If no candidates found with strict filter, fallback to unfiltered
        if not fused_candidates and (spec_filter or release_filter):
            vec_candidates = self.vector_store.search(query, top_k=top_k)
            bm25_candidates = self.bm25_retriever.search(query, top_k=top_k)
            fused_candidates = self.reciprocal_rank_fusion(vec_candidates, bm25_candidates)

        # 4. Cross-encoder rerank
        reranked = self.reranker.rerank(query, fused_candidates[:top_k], top_k=rerank_top_k)
        return reranked
