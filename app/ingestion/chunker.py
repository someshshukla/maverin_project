import uuid
from typing import List, Dict, Any
from app.ingestion.metadata import ChunkMetadata

class StructureAwareChunker:
    """Structure-aware chunker that preserves 3GPP document hierarchy and section context."""
    
    def __init__(self, max_chunk_chars: int = 1000, overlap_chars: int = 150):
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_section(self, section_data: Dict[str, Any]) -> List[ChunkMetadata]:
        """Splits a section into one or more chunks with rich contextual headers."""
        text = section_data["text"]
        spec = section_data["spec_number"]
        release = section_data["release"]
        version = section_data["version"]
        sec_num = section_data["section"]
        sec_title = section_data["section_title"]
        page = section_data.get("page", 1)
        doc_id = section_data["document_id"]
        source_url = section_data.get("source_url", "")
        title = section_data.get("title", "")
        
        paragraphs = text.split("\n\n")
        chunks = []
        current_paras = []
        current_len = 0
        chunk_idx = 0
        
        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue
                
            if current_len + len(para_clean) > self.max_chunk_chars and current_paras:
                chunk_body = "\n\n".join(current_paras)
                chunk_id = f"{doc_id}_sec{sec_num}_c{chunk_idx}"
                
                # Contextual header prefix to assist semantic and BM25 retrieval
                contextual_text = (
                    f"Specification: TS {spec} | Release: {release} | "
                    f"Section: {sec_num} ({sec_title}) | Page: {page}\n"
                    f"{chunk_body}"
                )
                
                chunks.append(ChunkMetadata(
                    spec_number=spec,
                    title=title,
                    release=release,
                    version=version,
                    section=sec_num,
                    section_title=sec_title,
                    page=page,
                    source_url=source_url,
                    document_id=doc_id,
                    chunk_id=chunk_id,
                    text=contextual_text
                ))
                
                chunk_idx += 1
                current_paras = [para_clean]
                current_len = len(para_clean)
            else:
                current_paras.append(para_clean)
                current_len += len(para_clean)
                
        if current_paras:
            chunk_body = "\n\n".join(current_paras)
            chunk_id = f"{doc_id}_sec{sec_num}_c{chunk_idx}"
            contextual_text = (
                f"Specification: TS {spec} | Release: {release} | "
                f"Section: {sec_num} ({sec_title}) | Page: {page}\n"
                f"{chunk_body}"
            )
            chunks.append(ChunkMetadata(
                spec_number=spec,
                title=title,
                release=release,
                version=version,
                section=sec_num,
                section_title=sec_title,
                page=page,
                source_url=source_url,
                document_id=doc_id,
                chunk_id=chunk_id,
                text=contextual_text
            ))
            
        return chunks

    def process_document(self, sections: List[Dict[str, Any]]) -> List[ChunkMetadata]:
        all_chunks = []
        for sec in sections:
            all_chunks.extend(self.chunk_section(sec))
        return all_chunks
