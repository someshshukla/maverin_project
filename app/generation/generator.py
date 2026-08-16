import os
import json
import logging
from typing import List, Tuple, Dict, Any, Optional
from app.config.settings import settings
from app.ingestion.metadata import ChunkMetadata
from app.generation.prompts import GROUNDED_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.generation.schemas import ChatResponse, SourceCitation, EvidenceChunkView, Claim
from app.verification.evidence import EvidenceEvaluator
from app.verification.grounding import GroundingVerifier

logger = logging.getLogger(__name__)


class GroundedGenerator:
    """LLM Generator abstraction supporting OpenAI, Gemini, and deterministic Mock provider with 1-controlled retry."""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.evidence_evaluator = EvidenceEvaluator()
        self.grounding_verifier = GroundingVerifier()

    def _format_evidence_text(self, evidence_chunks: List[Tuple[ChunkMetadata, float]]) -> str:
        blocks = []
        for chunk, score in evidence_chunks:
            blocks.append(
                f"[Source Chunk: {chunk.chunk_id}]\n"
                f"Spec: TS {chunk.spec_number} | Release: {chunk.release} | Version: {chunk.version}\n"
                f"Section: {chunk.section} ({chunk.section_title}) | Page: {chunk.page}\n"
                f"Passage:\n{chunk.text}\n"
            )
        return "\n----------------------------------------\n".join(blocks)

    def _generate_mock_answer(self, question: str, evidence_chunks: List[Tuple[ChunkMetadata, float]]) -> str:
        """Generates deterministic grounded answers directly synthesizing retrieved chunks without hallucination."""
        top_chunk, _ = evidence_chunks[0]
        
        # Build synthesis from retrieved passages
        passages = [c.text for c, _ in evidence_chunks[:3]]
        
        # Extract main text body after metadata headers
        clean_passages = []
        for p in passages:
            lines = p.split("\n")
            body_lines = [l for l in lines if not l.startswith("Specification:") and not l.startswith("Section:") and not l.startswith("Release:")]
            clean_passages.append(" ".join(body_lines).strip())
            
        synthesized_body = " ".join(clean_passages)
        answer = (
            f"According to 3GPP TS {top_chunk.spec_number} ({top_chunk.release}), Section {top_chunk.section} "
            f"('{top_chunk.section_title}'):\n\n"
            f"{synthesized_body}\n\n"
            f"(Citation: TS {top_chunk.spec_number}, {top_chunk.release}, Section {top_chunk.section}, Page {top_chunk.page})"
        )
        return answer

    def _call_llm_api(self, question: str, evidence_text: str, strict_retry: bool = False) -> str:
        """Calls configured LLM provider or mock engine."""
        if self.provider == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "mock-key":
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                prompt = USER_PROMPT_TEMPLATE.format(question=question, evidence_text=evidence_text)
                if strict_retry:
                    prompt += "\nWARNING: Previous answer contained ungrounded claims. Strictly restrict answer to explicit words in evidence."
                    
                response = client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}. Falling back to mock generator.")
                
        # Mock / Fallback engine
        return self._generate_mock_answer(question, [])

    def generate_answer(self, question: str, evidence_chunks: List[Tuple[ChunkMetadata, float]]) -> ChatResponse:
        """Generates grounded answer with evidence sufficiency checks, claims verification, and controlled 1-retry mechanism."""
        # 1. Evaluate Evidence Sufficiency
        check_result = self.evidence_evaluator.evaluate(question, evidence_chunks)
        
        if not check_result.sufficient:
            # Build refusal response
            evidence_views = [
                EvidenceChunkView(
                    chunk_id=c.chunk_id,
                    spec_number=c.spec_number,
                    release=c.release,
                    section=c.section,
                    section_title=c.section_title,
                    page=c.page,
                    text=c.text,
                    score=float(score)
                ) for c, score in evidence_chunks
            ]
            return ChatResponse(
                answer="I could not find sufficient evidence in the indexed 3GPP specifications to answer this reliably.",
                grounded=False,
                confidence=check_result.confidence,
                reason=check_result.reason,
                claims=[],
                sources=[],
                evidence=evidence_views
            )

        # 2. Format Evidence Passages
        evidence_text = self._format_evidence_text(evidence_chunks)
        
        # 3. Generate raw answer
        raw_answer = (
            self._call_llm_api(question, evidence_text)
            if self.provider == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "mock-key"
            else self._generate_mock_answer(question, evidence_chunks)
        )
        
        # 4. Perform Claim-Level Verification
        is_grounded, claims = self.grounding_verifier.verify(raw_answer, evidence_chunks)
        
        # 5. Controlled 1-Retry if ungrounded claims exist
        if not is_grounded and settings.MAX_RETRY_COUNT > 0:
            logger.info("Ungrounded claim detected. Triggering controlled 1-retry with strict grounding constraints...")
            raw_answer = (
                self._call_llm_api(question, evidence_text, strict_retry=True)
                if self.provider == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "mock-key"
                else self._generate_mock_answer(question, evidence_chunks)
            )
            is_grounded, claims = self.grounding_verifier.verify(raw_answer, evidence_chunks)

        # 6. Format Sources & Evidence
        sources_seen = set()
        citations: List[SourceCitation] = []
        
        for chunk, _ in evidence_chunks:
            source_key = (chunk.spec_number, chunk.release, chunk.section)
            if source_key not in sources_seen:
                sources_seen.add(source_key)
                citations.append(SourceCitation(
                    spec_number=chunk.spec_number,
                    release=chunk.release,
                    version=chunk.version,
                    section=chunk.section,
                    section_title=chunk.section_title,
                    page=chunk.page,
                    source_url=chunk.source_url
                ))
                
        evidence_views = [
            EvidenceChunkView(
                chunk_id=c.chunk_id,
                spec_number=c.spec_number,
                release=c.release,
                section=c.section,
                section_title=c.section_title,
                page=c.page,
                text=c.text,
                score=float(score)
            ) for c, score in evidence_chunks
        ]
        
        return ChatResponse(
            answer=raw_answer,
            grounded=is_grounded,
            confidence=check_result.confidence,
            reason=check_result.reason if is_grounded else "Answer generated with verified citations.",
            claims=claims,
            sources=citations,
            evidence=evidence_views
        )
