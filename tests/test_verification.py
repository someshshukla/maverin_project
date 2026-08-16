import pytest
from app.ingestion.metadata import ChunkMetadata
from app.verification.evidence import EvidenceEvaluator
from app.verification.claims import ClaimVerifier
from app.verification.grounding import GroundingVerifier

@pytest.fixture
def sample_chunk():
    return ChunkMetadata(
        spec_number="23.501",
        title="System Architecture",
        release="Rel-18",
        version="18.4.0",
        section="5.3.2",
        section_title="AMF Functions",
        page=42,
        source_url="https://3gpp.org",
        document_id="TS_23.501_Rel-18",
        chunk_id="chunk_1",
        text="The Access and Mobility Management Function (AMF) handles UE registration."
    )

def test_evidence_evaluator(sample_chunk):
    evaluator = EvidenceEvaluator(threshold=0.35)
    
    # Sufficient case
    res_valid = evaluator.evaluate("What is AMF role?", [(sample_chunk, 0.85)])
    assert res_valid.sufficient is True
    
    # Low confidence score case
    res_low = evaluator.evaluate("What is AMF role?", [(sample_chunk, 0.10)])
    assert res_low.sufficient is False
    
    # Empty case
    res_empty = evaluator.evaluate("Random query", [])
    assert res_empty.sufficient is False

def test_claim_verifier(sample_chunk):
    verifier = ClaimVerifier()
    claims = ["The AMF handles UE registration.", "Quantum computing is used by gNB."]
    
    verified, all_supported = verifier.verify_claims(claims, [(sample_chunk, 0.90)])
    assert len(verified) == 2
    assert len(verified[0].source_chunk_ids) > 0
    assert len(verified[1].source_chunk_ids) == 0
    assert all_supported is False

def test_grounding_verifier(sample_chunk):
    gv = GroundingVerifier()
    
    # Refusal string
    grounded, claims = gv.verify("I could not find sufficient evidence in the indexed 3GPP specifications to answer this reliably.", [])
    assert grounded is True
    assert len(claims) == 0
