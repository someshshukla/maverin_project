import re
from typing import Dict, Any, Optional, List

class QueryParser:
    """Deterministic & heuristic query analyzer to extract 3GPP specifications, releases, and key terms."""

    @staticmethod
    def parse_query(query: str) -> Dict[str, Any]:
        spec_number: Optional[str] = None
        release: Optional[str] = None
        
        # Match TS 23.501, TS23.502, 23.501, 38.331, etc.
        spec_match = re.search(r'\b(?:TS\s*)?(\d{2}\.\d{3})\b', query, re.IGNORECASE)
        if spec_match:
            spec_number = spec_match.group(1)
            
        # Match Rel-18, Rel 18, Release 18, Rel-17, etc.
        rel_match = re.search(r'\b(?:Rel(?:ease)?[\s\-]*)(\d{2})\b', query, re.IGNORECASE)
        if rel_match:
            release = f"Rel-{rel_match.group(1)}"

        # Extract 3GPP acronyms / capitalized identifiers
        keywords = re.findall(r'\b[A-Z0-9]{2,10}\b', query)
        # Filter out generic words
        stopwords = {"WHAT", "HOW", "WHY", "WHEN", "ACCORDING", "FROM", "INTO", "WITH", "THAT", "THIS"}
        keywords = [k for k in keywords if k not in stopwords]

        return {
            "specification": spec_number,
            "release": release,
            "keywords": keywords,
            "query": query
        }
