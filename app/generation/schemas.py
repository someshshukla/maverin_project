from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Claim(BaseModel):
    text: str = Field(description="Substantive factual claim extracted from the answer")
    source_chunk_ids: List[str] = Field(default_factory=list, description="IDs of source chunks supporting this claim")

class SourceCitation(BaseModel):
    spec_number: str
    release: str
    version: Optional[str] = None
    section: str
    section_title: Optional[str] = None
    page: Optional[int] = None
    source_url: Optional[str] = None

class EvidenceChunkView(BaseModel):
    chunk_id: str
    spec_number: str
    release: str
    section: str
    section_title: str
    page: Optional[int] = None
    text: str
    score: float

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    grounded: bool
    confidence: float
    reason: Optional[str] = None
    claims: List[Claim] = Field(default_factory=list)
    sources: List[SourceCitation] = Field(default_factory=list)
    evidence: List[EvidenceChunkView] = Field(default_factory=list)

class SufficiencyCheckResult(BaseModel):
    sufficient: bool
    confidence: float
    reason: str
