import os
import json
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class VectorStore:
    """FAISS vector store with SentenceTransformers embedding model."""
    
    def __init__(self, index_dir: str = settings.INDEX_DIR, model_name: str = settings.EMBEDDING_MODEL):
        self.index_dir = index_dir
        self.model_name = model_name
        self.chunks: List[ChunkMetadata] = []
        self.index = None
        self.encoder = None
        self._load_encoder()
        
    def _load_encoder(self):
        """Loads SentenceTransformer encoder or uses fallback TF-IDF/embeddings if offline."""
        if SentenceTransformer:
            try:
                self.encoder = SentenceTransformer(self.model_name)
            except Exception:
                self.encoder = None
        else:
            self.encoder = None

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Embeds text using SentenceTransformer or a deterministic vector fallback."""
        if self.encoder:
            embeddings = self.encoder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.astype('float32')
        else:
            # Deterministic fallback embedding representation for environments without weights downloaded
            from sklearn.feature_extraction.text import TfidfVectorizer
            vectorizer = TfidfVectorizer(max_features=384)
            vecs = vectorizer.fit_transform(texts).toarray()
            if vecs.shape[1] < 384:
                padded = np.zeros((vecs.shape[0], 384), dtype='float32')
                padded[:, :vecs.shape[1]] = vecs
                vecs = padded
            # Normalize vectors
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return (vecs / norms).astype('float32')

    def build_index(self, chunks: List[ChunkMetadata]):
        """Builds FAISS L2/Cosine index and saves to disk."""
        self.chunks = chunks
        texts = [c.text for c in chunks]
        embeddings = self._get_embeddings(texts)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings) if faiss else None
        dim = embeddings.shape[1]
        
        if faiss:
            self.index = faiss.IndexFlatIP(dim)  # Inner Product on normalized vectors = Cosine Sim
            self.index.add(embeddings)
            
            # Save FAISS index and metadata
            faiss_path = os.path.join(self.index_dir, "faiss.index")
            faiss.write_index(self.index, faiss_path)
        else:
            self.index = embeddings  # fallback numpy matrix
            np.save(os.path.join(self.index_dir, "embeddings.npy"), embeddings)
            
        meta_path = os.path.join(self.index_dir, "vector_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in chunks], f, indent=2)

    def load_index(self) -> bool:
        """Loads FAISS index and chunk metadata from disk."""
        meta_path = os.path.join(self.index_dir, "vector_metadata.json")
        faiss_path = os.path.join(self.index_dir, "faiss.index")
        
        if not os.path.exists(meta_path):
            return False
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_dicts = json.load(f)
            self.chunks = [ChunkMetadata.from_dict(d) for d in meta_dicts]
            
        if faiss and os.path.exists(faiss_path):
            self.index = faiss.read_index(faiss_path)
        elif os.path.exists(os.path.join(self.index_dir, "embeddings.npy")):
            self.index = np.load(os.path.join(self.index_dir, "embeddings.npy"))
        else:
            return False
            
        return True

    def search(self, query: str, top_k: int = 20, spec_filter: Optional[str] = None, release_filter: Optional[str] = None) -> List[Tuple[ChunkMetadata, float]]:
        """Searches vector index with optional metadata filtering."""
        if not self.chunks or self.index is None:
            if not self.load_index():
                return []
                
        query_vec = self._get_embeddings([query])
        if faiss:
            faiss.normalize_L2(query_vec)
            scores, indices = self.index.search(query_vec, min(top_k * 3, len(self.chunks)))
            scores = scores[0]
            indices = indices[0]
        else:
            # Numpy cosine similarity fallback
            norms = np.linalg.norm(query_vec, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            query_vec_norm = query_vec / norms
            sims = np.dot(self.index, query_vec_norm.T).flatten()
            indices = np.argsort(sims)[::-1][:min(top_k * 3, len(self.chunks))]
            scores = sims[indices]

        results = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx]
            
            # Apply metadata filters if specified
            if spec_filter and spec_filter not in chunk.spec_number and chunk.spec_number not in spec_filter:
                continue
            if release_filter and release_filter.lower() != chunk.release.lower():
                continue
                
            results.append((chunk, float(score)))
            if len(results) >= top_k:
                break
                
        return results
