import re
from typing import List, Tuple, Dict, Any
from app.ingestion.metadata import ChunkMetadata
from app.generation.schemas import Claim

class ClaimVerifier:
    """Extracts factual claims from answer text and verifies support against source chunks."""

    @staticmethod
    def extract_claims(answer_text: str) -> List[str]:
        """Splits answer text into discrete factual sentence claims, filtering out citation headers/footers."""
        sentences = re.split(r'(?<=[.!?])\s+|\n\n', answer_text.strip())
        claims = []
        for s in sentences:
            st = s.strip()
            if not st or len(st) <= 15:
                continue
            if st.startswith("I could not find") or st.startswith("According to 3GPP") or st.startswith("(Citation:") or st.endswith(":"):
                continue
            claims.append(st)
        return claims

    def verify_claims(self, claims: List[str], evidence_chunks: List[Tuple[ChunkMetadata, float]]) -> Tuple[List[Claim], bool]:
        verified_claims = []
        all_supported = True
        
        evidence_text_map = {c.chunk_id: c.text.lower() for c, _ in evidence_chunks}
        
        for claim_text in claims:
            claim_words = set(re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', claim_text.lower()))
            # Remove basic stopwords
            stopwords = {"the", "a", "an", "is", "are", "was", "were", "of", "and", "or", "in", "to", "for", "with", "on", "by", "at", "it", "this", "that"}
            meaningful_words = claim_words - stopwords
            
            supporting_ids = []
            for chunk_id, text in evidence_text_map.items():
                matches = sum(1 for w in meaningful_words if w in text)
                overlap_ratio = matches / len(meaningful_words) if meaningful_words else 0
                if overlap_ratio >= 0.40:
                    supporting_ids.append(chunk_id)
                    
            if supporting_ids:
                verified_claims.append(Claim(text=claim_text, source_chunk_ids=supporting_ids))
            else:
                verified_claims.append(Claim(text=claim_text, source_chunk_ids=[]))
                all_supported = False
                
        return verified_claims, all_supported
