import pytest
from app.ingestion.metadata import ChunkMetadata
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever

@pytest.fixture
def sample_chunks():
    return [
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
            text="The Access and Mobility Management Function (AMF) handles UE registration and NAS security."
        ),
        ChunkMetadata(
            spec_number="24.501",
            title="NAS Protocol",
            release="Rel-18",
            version="18.2.0",
            section="10.2.1",
            section_title="T3510 Timer",
            page=110,
            source_url="https://3gpp.org",
            document_id="TS_24.501_Rel-18",
            chunk_id="chunk_2",
            text="Timer T3510 is started when the UE transmits a REGISTRATION REQUEST message. Default is 15 seconds."
        )
    ]

def test_vector_store(tmp_path, sample_chunks):
    vs = VectorStore(index_dir=str(tmp_path))
    vs.build_index(sample_chunks)
    
    results = vs.search("What does AMF do?", top_k=2)
    assert len(results) > 0
    assert results[0][0].spec_number == "23.501"

def test_bm25_retriever(tmp_path, sample_chunks):
    bm25 = BM25Retriever(index_dir=str(tmp_path))
    bm25.build_index(sample_chunks)
    
    results = bm25.search("T3510 timer", top_k=2)
    assert len(results) > 0
    assert results[0][0].spec_number == "24.501"

def test_hybrid_retriever(tmp_path, sample_chunks):
    vs = VectorStore(index_dir=str(tmp_path))
    vs.build_index(sample_chunks)
    
    bm25 = BM25Retriever(index_dir=str(tmp_path))
    bm25.build_index(sample_chunks)
    
    hybrid = HybridRetriever(vector_store=vs, bm25_retriever=bm25)
    results = hybrid.retrieve("AMF registration", spec_filter="23.501")
    assert len(results) > 0
    assert results[0][0].spec_number == "23.501"
