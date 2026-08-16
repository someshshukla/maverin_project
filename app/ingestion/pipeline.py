import os
import json
import logging
from typing import List, Tuple
from app.config.settings import settings
from app.ingestion.downloader import download_or_generate_dataset
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import StructureAwareChunker
from app.ingestion.metadata import ChunkMetadata
from app.retrieval.vector_store import VectorStore
from app.retrieval.bm25 import BM25Retriever

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self, raw_dir: str = settings.RAW_DATA_DIR, index_dir: str = settings.INDEX_DIR):
        self.raw_dir = raw_dir
        self.index_dir = index_dir
        self.chunker = StructureAwareChunker()

    def run(self) -> Tuple[int, int]:
        """Runs the ingestion pipeline: downloads/parses data, creates chunks, and saves vector/BM25 indices."""
        logger.info("Step 1: Preparing raw 3GPP standards dataset...")
        files = download_or_generate_dataset(self.raw_dir)
        
        logger.info(f"Step 2: Parsing {len(files)} files...")
        all_sections = []
        for file_path in files:
            sections = DocumentParser.parse_file(file_path)
            all_sections.extend(sections)
            
        logger.info(f"Step 3: Chunking {len(all_sections)} sections with structure-aware chunker...")
        all_chunks: List[ChunkMetadata] = self.chunker.process_document(all_sections)
        
        logger.info(f"Generated total {len(all_chunks)} chunks.")
        
        # Ensure index dir exists
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Save chunks metadata json
        chunks_json_path = os.path.join(self.index_dir, "chunks_metadata.json")
        with open(chunks_json_path, "w", encoding="utf-8") as f:
            json.dump([c.to_dict() for c in all_chunks], f, indent=2)
            
        logger.info("Step 4: Building FAISS vector store index...")
        vector_store = VectorStore(self.index_dir)
        vector_store.build_index(all_chunks)
        
        logger.info("Step 5: Building BM25 lexical index...")
        bm25_retriever = BM25Retriever(self.index_dir)
        bm25_retriever.build_index(all_chunks)
        
        logger.info("Ingestion pipeline completed successfully!")
        return len(files), len(all_chunks)
