import logging
import sys
from app.ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    pipeline = IngestionPipeline()
    file_count, chunk_count = pipeline.run()
    print(f"\n[SUCCESS] Ingested {file_count} 3GPP documents into {chunk_count} chunks.")

if __name__ == "__main__":
    main()
