import os
import re
from typing import List, Dict, Any
from app.ingestion.metadata import ChunkMetadata

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

class DocumentParser:
    """Structure-aware 3GPP document parser for PDF and structured TXT documents."""
    
    @staticmethod
    def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        """Parses PDF document preserving pages and section hierarchy using PyMuPDF."""
        if not fitz:
            raise ImportError("PyMuPDF (fitz) is not installed.")
            
        doc = fitz.open(file_path)
        filename = os.path.basename(file_path)
        
        # Regex heuristics for 3GPP header detection
        spec_match = re.search(r'TS[_\s]?(\d{2}\.\d{3})', filename, re.IGNORECASE)
        spec_number = spec_match.group(1) if spec_match else "Unknown"
        rel_match = re.search(r'Rel[_\-]?(\d{2})', filename, re.IGNORECASE)
        release = f"Rel-{rel_match.group(1)}" if rel_match else "Rel-18"
        
        parsed_sections = []
        current_section = "1.0"
        current_title = "General"
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Simple line-by-line section header detection
            lines = text.split("\n")
            page_text_blocks = []
            
            for line in lines:
                line_str = line.strip()
                # Match section pattern like "5.3.2 Registration Management"
                header_match = re.match(r'^(\d+(\.\d+)+)\s+(.+)$', line_str)
                if header_match:
                    current_section = header_match.group(1)
                    current_title = header_match.group(3)
                page_text_blocks.append(line_str)
                
            page_content = "\n".join(page_text_blocks).strip()
            if page_content:
                parsed_sections.append({
                    "spec_number": spec_number,
                    "title": f"3GPP TS {spec_number} Specification",
                    "release": release,
                    "version": "18.0.0",
                    "section": current_section,
                    "section_title": current_title,
                    "page": page_num + 1,
                    "source_url": f"https://www.3gpp.org/ftp/Specs/archive/",
                    "document_id": f"TS_{spec_number}_{release}",
                    "text": page_content
                })
                
        doc.close()
        return parsed_sections

    @staticmethod
    def parse_txt(file_path: str) -> List[Dict[str, Any]]:
        """Parses structured text file representing 3GPP standards."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        filename = os.path.basename(file_path)
        spec_match = re.search(r'TS[_\s]?(\d{2}\.\d{3})', content, re.IGNORECASE) or re.search(r'TS[_\s]?(\d{2}\.\d{3})', filename, re.IGNORECASE)
        spec_number = spec_match.group(1) if spec_match else "23.501"
        
        rel_match = re.search(r'Release:\s*(Rel-\d+)', content) or re.search(r'Rel[_\-]?(\d{2})', filename, re.IGNORECASE)
        release = rel_match.group(1) if hasattr(rel_match, 'group') and rel_match.group(1).startswith("Rel") else "Rel-18"
        
        title_match = re.search(r'Title:\s*(.+)', content)
        title = title_match.group(1).strip() if title_match else f"3GPP TS {spec_number} Specification"
        
        ver_match = re.search(r'Version:\s*(.+)', content)
        version = ver_match.group(1).strip() if ver_match else "18.0.0"
        
        url_match = re.search(r'Source URL:\s*(.+)', content)
        source_url = url_match.group(1).strip() if url_match else "https://www.3gpp.org/ftp/Specs/"
        
        # Split by section divider
        sections_data = []
        raw_sections = content.split("Chapter/Section:")
        
        for sec in raw_sections[1:]:
            lines = sec.strip().split("\n")
            sec_num = lines[0].strip()
            sec_title = "General"
            page_num = 1
            content_start_idx = 1
            
            for i, line in enumerate(lines[1:], start=1):
                if line.startswith("Section Title:"):
                    sec_title = line.replace("Section Title:", "").strip()
                elif line.startswith("Page:"):
                    try:
                        page_num = int(line.replace("Page:", "").strip())
                    except ValueError:
                        page_num = 1
                elif line.startswith("---"):
                    content_start_idx = i + 1
                    break
                    
            body_text = "\n".join(lines[content_start_idx:]).strip()
            if body_text:
                sections_data.append({
                    "spec_number": spec_number,
                    "title": title,
                    "release": release,
                    "version": version,
                    "section": sec_num,
                    "section_title": sec_title,
                    "page": page_num,
                    "source_url": source_url,
                    "document_id": f"TS_{spec_number}_{release}",
                    "text": body_text
                })
                
        return sections_data

    @classmethod
    def parse_file(cls, file_path: str) -> List[Dict[str, Any]]:
        """Main entry point to parse PDF or TXT 3GPP documents."""
        if file_path.endswith(".pdf"):
            return cls.parse_pdf(file_path)
        else:
            return cls.parse_txt(file_path)
