import os
import pytest
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import StructureAwareChunker
from app.ingestion.metadata import ChunkMetadata

def test_txt_parser(tmp_path):
    sample_txt = tmp_path / "TS_23.501_Rel-18.txt"
    sample_txt.write_text(
        "Specification: TS 23.501\nTitle: System Architecture\nRelease: Rel-18\nVersion: 18.4.0\nSource URL: https://3gpp.org\n"
        "============================================================\n"
        "Chapter/Section: 5.3.2\nSection Title: AMF Functions\nPage: 42\n----------------------------------------\n"
        "The AMF manages registration and mobility.\n"
    )
    
    sections = DocumentParser.parse_txt(str(sample_txt))
    assert len(sections) == 1
    assert sections[0]["spec_number"] == "23.501"
    assert sections[0]["section"] == "5.3.2"
    assert sections[0]["page"] == 42

def test_structure_aware_chunker():
    chunker = StructureAwareChunker(max_chunk_chars=100)
    section_data = {
        "spec_number": "23.501",
        "title": "System Architecture",
        "release": "Rel-18",
        "version": "18.4.0",
        "section": "5.3.2",
        "section_title": "AMF Functions",
        "page": 42,
        "source_url": "https://3gpp.org",
        "document_id": "TS_23.501_Rel-18",
        "text": "Paragraph 1: Registration management.\n\nParagraph 2: Mobility management.\n\nParagraph 3: Connection management."
    }
    
    chunks = chunker.chunk_section(section_data)
    assert len(chunks) >= 2
    assert isinstance(chunks[0], ChunkMetadata)
    assert "Specification: TS 23.501" in chunks[0].text
    assert "Section: 5.3.2" in chunks[0].text
