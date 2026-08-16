import os
import re
import json
import pickle
from typing import List, Tuple, Optional
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

def tokenize_3gpp_text(text: str) -> List[str]:
    """Tokenizer specifically preserving 3GPP identifiers like TS 23.501, T3510, 5G-GUTI, N1, N2."""
    # Convert to lowercase but preserve hyphenated/alphanumeric terms
    tokens = re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', text.lower())
    return tokens

class BM25Retriever:
    """BM25 Lexical Retriever for exact match on 3GPP identifiers and keywords."""
    
    def __init__(self, index_dir: str = settings.INDEX_DIR):
        self.index_dir = index_dir
        self.chunks: List[ChunkMetadata] = []
        self.bm25 = None

    def build_index(self, chunks: List[ChunkMetadata]):
        """Tokenizes chunks and builds BM25 index."""
        self.chunks = chunks
        corpus_tokens = [tokenize_3gpp_text(c.text) for c in chunks]
        
        if BM25Okapi:
            self.bm25 = BM25Okapi(corpus_tokens)
            bm25_path = os.path.join(self.index_dir, "bm25.pkl")
            with open(bm25_path, "wb") as f:
                pickle.dump(self.bm25, f)
        else:
            self.bm25 = corpus_tokens  # fallback
            
        meta_path = os.path.join(self.index_dir, "bm25_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in chunks], f, indent=2)

    def load_index(self) -> bool:
        """Loads BM25 index and chunk metadata from disk."""
        meta_path = os.path.join(self.index_dir, "bm25_metadata.json")
        bm25_path = os.path.join(self.index_dir, "bm25.pkl")
        
        if not os.path.exists(meta_path):
            return False
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_dicts = json.load(f)
            self.chunks = [ChunkMetadata.from_dict(d) for d in meta_dicts]
            
        if BM25Okapi and os.path.exists(bm25_path):
            with open(bm25_path, "rb") as f:
                self.bm25 = pickle.load(f)
        else:
            # Fallback simple keyword match
            corpus_tokens = [tokenize_3gpp_text(c.text) for c in self.chunks]
            self.bm25 = BM25Okapi(corpus_tokens) if BM25Okapi else corpus_tokens
            
        return True

    def search(self, query: str, top_k: int = 20, spec_filter: Optional[str] = None, release_filter: Optional[str] = None) -> List[Tuple[ChunkMetadata, float]]:
        """Searches BM25 index with tokenized query and metadata filter."""
        if not self.chunks or self.bm25 is None:
            if not self.load_index():
                return []
                
        query_tokens = tokenize_3gpp_text(query)
        if not query_tokens:
            return []
            
        if BM25Okapi and isinstance(self.bm25, BM25Okapi):
            scores = self.bm25.get_scores(query_tokens)
        else:
            # Fallback TF match score calculation
            scores = []
            q_set = set(query_tokens)
            for chunk_tokens in self.bm25:
                overlap = sum(1 for t in chunk_tokens if t in q_set)
                scores.append(float(overlap))
                
        # Sort indices by score descending
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        results = []
        for idx in sorted_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            
            # Apply metadata filters
            if spec_filter and spec_filter not in chunk.spec_number and chunk.spec_number not in spec_filter:
                continue
            if release_filter and release_filter.lower() != chunk.release.lower():
                continue
                
            results.append((chunk, score))
            if len(results) >= top_k:
                break
                
        return results
