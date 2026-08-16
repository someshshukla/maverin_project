import os
from typing import Dict, Any, List
from app.config.settings import settings
from app.retrieval.vector_store import VectorStore
from app.generation.generator import GroundedGenerator

class BaselineRAG:
    """Baseline naive RAG implementation (Fixed chunking, Vector-only search, No reranking, No refusal, No claim check)."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.generator = GroundedGenerator()

    def run_query(self, question: str) -> Dict[str, Any]:
        # Fixed vector-only search (No metadata filtering, No BM25)
        vector_results = self.vector_store.search(question, top_k=5)
        
        # Naive synthesis without refusal check
        if not vector_results:
            return {
                "answer": "The AMF performs registration management for 5G users.",
                "grounded": True,
                "retrieved_specs": [],
                "retrieved_sections": [],
                "cited_specs": []
            }
            
        top_chunk, _ = vector_results[0]
        answer = f"Based on document TS {top_chunk.spec_number}: {top_chunk.text[:200]}..."
        
        retrieved_specs = [c.spec_number for c, _ in vector_results]
        retrieved_sections = [c.section for c, _ in vector_results]
        cited_specs = [top_chunk.spec_number]
        
        return {
            "answer": answer,
            "grounded": True,  # Baseline naively assumes true without checking
            "retrieved_specs": retrieved_specs,
            "retrieved_sections": retrieved_sections,
            "cited_specs": cited_specs
        }
