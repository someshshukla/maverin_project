from typing import List, Tuple
from app.ingestion.metadata import ChunkMetadata
from app.verification.claims import ClaimVerifier
from app.generation.schemas import Claim

class GroundingVerifier:
    """Post-generation verifier that ensures zero ungrounded claims are output to the user."""

    def __init__(self):
        self.claim_verifier = ClaimVerifier()

    def verify(self, answer_text: str, evidence_chunks: List[Tuple[ChunkMetadata, float]]) -> Tuple[bool, List[Claim]]:
        if "I could not find sufficient evidence" in answer_text:
            return True, []
            
        claims_str = self.claim_verifier.extract_claims(answer_text)
        verified_claims, all_supported = self.claim_verifier.verify_claims(claims_str, evidence_chunks)
        
        return all_supported, verified_claims
