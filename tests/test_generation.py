import pytest
from app.ingestion.metadata import ChunkMetadata
from app.generation.generator import GroundedGenerator

@pytest.fixture
def sample_evidence():
    return [
        (
            ChunkMetadata(
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
                text="The Access and Mobility Management Function (AMF) performs registration management."
            ),
            0.92
        )
    ]

def test_grounded_generator_answer(sample_evidence):
    gen = GroundedGenerator()
    resp = gen.generate_answer("What is the role of the AMF?", sample_evidence)
    
    assert resp.grounded is True
    assert "23.501" in resp.answer
    assert len(resp.sources) > 0
    assert resp.sources[0].spec_number == "23.501"
    assert resp.sources[0].section == "5.3.2"

def test_grounded_generator_refusal():
    gen = GroundedGenerator()
    resp = gen.generate_answer("What is the price of Bitcoin in Rel-18?", [])
    
    assert resp.grounded is False
    assert "could not find sufficient evidence" in resp.answer
