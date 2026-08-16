from typing import List, Tuple
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata
from app.generation.schemas import SufficiencyCheckResult

class EvidenceEvaluator:
    """Evaluates whether retrieved 3GPP passages provide sufficient evidence to answer the query."""

    def __init__(self, threshold: float = settings.GROUNDING_THRESHOLD):
        self.threshold = threshold

    def evaluate(self, query: str, retrieved_chunks: List[Tuple[ChunkMetadata, float]]) -> SufficiencyCheckResult:
        if not retrieved_chunks:
            return SufficiencyCheckResult(
                sufficient=False,
                confidence=0.0,
                reason="No evidence chunks were retrieved from the 3GPP index."
            )

        top_chunk, top_score = retrieved_chunks[0]
        
        # Check against score threshold
        if top_score < self.threshold:
            return SufficiencyCheckResult(
                sufficient=False,
                confidence=round(float(top_score), 2),
                reason=f"Top retrieval score ({top_score:.2f}) is below confidence threshold ({self.threshold:.2f})."
            )

        # Check keyword presence in top passages
        import re
        query_terms = [t.lower() for t in re.findall(r'\b[a-zA-Z0-9_\-\.]+\b', query) if len(t) >= 2 and t.lower() not in {"what", "is", "the", "of", "in", "to", "for", "and", "or", "according"}]
        combined_text = " ".join([c.text.lower() for c, _ in retrieved_chunks[:3]])
        matched_terms = [t for t in query_terms if t in combined_text]

        if query_terms and len(matched_terms) == 0:
            return SufficiencyCheckResult(
                sufficient=False,
                confidence=0.25,
                reason="Retrieved passages do not contain key entities from the user query."
            )

        # Sufficient evidence found
        calc_confidence = min(0.99, max(0.50, float(top_score * 0.8 + (len(matched_terms) / (len(query_terms) + 1)) * 0.2)))
        return SufficiencyCheckResult(
            sufficient=True,
            confidence=round(calc_confidence, 2),
            reason=f"Sufficient evidence found in section {top_chunk.section} of TS {top_chunk.spec_number}."
        )
