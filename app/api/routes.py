import os
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from app.config.settings import settings
from app.generation.schemas import ChatRequest, ChatResponse
from app.query.query_parser import QueryParser
from app.retrieval.hybrid import HybridRetriever
from app.generation.generator import GroundedGenerator

router = APIRouter()

# Initialize retriever and generator singletons
retriever = HybridRetriever()
generator = GroundedGenerator()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    index_exists = os.path.exists(os.path.join(settings.INDEX_DIR, "chunks_metadata.json"))
    return {
        "status": "healthy",
        "index_loaded": index_exists,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL
    }


@router.get("/documents")
def list_documents() -> List[Dict[str, Any]]:
    """Returns list of indexed 3GPP documents and total chunks."""
    meta_path = os.path.join(settings.INDEX_DIR, "chunks_metadata.json")
    if not os.path.exists(meta_path):
        return []
        
    with open(meta_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    # Group by document
    docs: Dict[str, Dict[str, Any]] = {}
    for c in chunks:
        doc_id = c.get("document_id", "Unknown")
        if doc_id not in docs:
            docs[doc_id] = {
                "document_id": doc_id,
                "spec_number": c.get("spec_number"),
                "title": c.get("title"),
                "release": c.get("release"),
                "version": c.get("version"),
                "source_url": c.get("source_url"),
                "chunk_count": 0
            }
        docs[doc_id]["chunk_count"] += 1
        
    return list(docs.values())


@router.post("/search")
def search_evidence(query: str = Query(..., description="Search query"), top_k: int = Query(5, description="Number of results")):
    """Performs raw hybrid search and reranking on 3GPP index."""
    query_info = QueryParser.parse_query(query)
    results = retriever.retrieve(
        query=query,
        spec_filter=query_info.get("specification"),
        release_filter=query_info.get("release"),
        rerank_top_k=top_k
    )
    
    output = []
    for chunk, score in results:
        output.append({
            "chunk_id": chunk.chunk_id,
            "spec_number": chunk.spec_number,
            "release": chunk.release,
            "section": chunk.section,
            "section_title": chunk.section_title,
            "page": chunk.page,
            "score": round(float(score), 4),
            "text": chunk.text
        })
    return {"query": query, "results": output}


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Main RAG Chatbot endpoint for asking 3GPP standards questions."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    # 1. Query Analysis
    query_info = QueryParser.parse_query(request.question)
    
    # 2. Hybrid Retrieval + Reranking
    retrieved_chunks = retriever.retrieve(
        query=request.question,
        spec_filter=query_info.get("specification"),
        release_filter=query_info.get("release")
    )
    
    # 3. Grounded Answer Generation & Verification
    response = generator.generate_answer(request.question, retrieved_chunks)
    return response
