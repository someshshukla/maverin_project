from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class ChunkMetadata:
    spec_number: str         # e.g., "23.501"
    title: str               # e.g., "System Architecture for the 5G System"
    release: str             # e.g., "Rel-18"
    version: str             # e.g., "18.5.0"
    section: str             # e.g., "5.3.2"
    section_title: str       # e.g., "Registration Management"
    page: Optional[int]      # e.g., 42
    source_url: str          # e.g., "https://www.3gpp.org/ftp/Specs/archive/23_series/23.501/"
    document_id: str         # e.g., "TS_23.501_Rel-18"
    chunk_id: str            # e.g., "TS_23.501_Rel-18_sec5.3.2_c0"
    text: str                # Full text content of chunk

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkMetadata":
        return cls(**data)
