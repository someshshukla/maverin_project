import streamlit as st
import requests
import json
import os

# Page configuration
st.set_page_config(
    page_title="3GPP Standards AI Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium 3GPP Telecom aesthetic
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .grounded-badge {
        display: inline-block;
        background-color: #DCFCE7;
        color: #15803D;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .refusal-badge {
        display: inline-block;
        background-color: #FEE2E2;
        color: #B91C1C;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .citation-card {
        background-color: #F8FAFC;
        border-left: 4px solid #0EA5E9;
        padding: 0.75rem 1rem;
        border-radius: 0.375rem;
        margin-bottom: 0.5rem;
        font-size: 0.92rem;
    }
    .evidence-block {
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        padding: 0.75rem;
        border-radius: 0.375rem;
        font-family: monospace;
        font-size: 0.85rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown('<div class="main-header">📡 3GPP Standards AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Grounded RAG System for 5G Telecommunications Specifications (TS 23.501, TS 23.502, TS 24.501, TS 38.331)</div>', unsafe_allow_html=True)

# Sidebar with indexed document details
with st.sidebar:
    st.header("📚 Document Corpus")
    try:
        res = requests.get(f"{API_URL}/documents", timeout=3)
        if res.status_code == 200:
            docs = res.json()
            st.success(f"Indexed Specifications: {len(docs)}")
            for d in docs:
                with st.expander(f"TS {d['spec_number']} ({d['release']})"):
                    st.write(f"**Title**: {d['title']}")
                    st.write(f"**Version**: {d['version']}")
                    st.write(f"**Chunks**: {d['chunk_count']}")
        else:
            st.warning("Backend API available, but no documents loaded.")
    except Exception:
        st.info("Local Ingestion active (Fallback mode).")
        
    st.divider()
    st.markdown("### 🛡️ Safeguards")
    st.markdown("- **Metadata Filtering**: Spec & Release Aware")
    st.markdown("- **Hybrid Search**: Vector + BM25 RRF")
    st.markdown("- **Reranker**: Cross-Encoder")
    st.markdown("- **Evidence Verification**: Strict Refusal Threshold")
    st.markdown("- **Claim Verification**: 1-Controlled Retry")

# Demo Question Selector
st.markdown("### 💡 Quick Test Questions")
col_a, col_b, col_c, col_d, col_e = st.columns(5)

selected_question = None
if col_a.button("AMF Role", use_container_width=True):
    selected_question = "What is the role of the AMF during UE registration?"
if col_b.button("TS 24.501 T3510", use_container_width=True):
    selected_question = "According to TS 24.501, what is T3510?"
if col_c.button("Registration Steps", use_container_width=True):
    selected_question = "What happens during the 5G registration procedure?"
if col_d.button("UPF Function", use_container_width=True):
    selected_question = "What are the main functions of the User Plane Function (UPF)?"
if col_e.button("Unanswerable", use_container_width=True):
    selected_question = "What is the optimal coffee brewing temperature for 5G engineers?"

# Input box
user_input = st.text_input("Ask a question about 3GPP standards:", value=selected_question or "", placeholder="e.g. What is the role of the AMF during UE registration?")
submit_btn = st.button("Submit Question", type="primary")

if submit_btn and user_input:
    with st.spinner("Retrieving authoritative 3GPP evidence, reranking, and verifying claims..."):
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"question": user_input},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
            else:
                st.error(f"Error from server: {response.text}")
                data = None
        except Exception as e:
            st.warning("Backend service offline. Processing query via direct python fallback...")
            from app.query.query_parser import QueryParser
            from app.retrieval.hybrid import HybridRetriever
            from app.generation.generator import GroundedGenerator
            
            qp = QueryParser.parse_query(user_input)
            retriever = HybridRetriever()
            gen = GroundedGenerator()
            chunks = retriever.retrieve(user_input, spec_filter=qp.get("specification"), release_filter=qp.get("release"))
            resp_obj = gen.generate_answer(user_input, chunks)
            data = resp_obj.dict()

        if data:
            st.divider()
            
            # Grounding Badge & Confidence
            is_grounded = data.get("grounded", False)
            confidence = data.get("confidence", 0.0) * 100
            
            if is_grounded:
                st.markdown(f'<div class="grounded-badge">✓ Grounded Answer (Confidence: {confidence:.0f}%)</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="refusal-badge">⚠️ Evidence Insufficient / Refusal (Confidence: {confidence:.0f}%)</div>', unsafe_allow_html=True)
                
            st.markdown("### Answer")
            st.markdown(data.get("answer", ""))
            
            # Sources Section
            sources = data.get("sources", [])
            if sources:
                st.markdown("### 📌 Citations & Sources")
                cols = st.columns(len(sources)) if len(sources) <= 4 else st.columns(4)
                for idx, src in enumerate(sources):
                    with cols[idx % len(cols)]:
                        st.markdown(
                            f"""
                            <div class="citation-card">
                                <strong>TS {src['spec_number']}</strong> ({src['release']})<br/>
                                <strong>Section {src['section']}</strong>: {src.get('section_title', '')}<br/>
                                Page {src.get('page', 'N/A')}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        
            # Retrieved Evidence Section
            evidence = data.get("evidence", [])
            if evidence:
                with st.expander(f"🔍 View Retrieved Evidence ({len(evidence)} chunks)"):
                    for ev in evidence:
                        st.markdown(f"**[Chunk: {ev['chunk_id']}]** | TS {ev['spec_number']} ({ev['release']}) | Section {ev['section']} ({ev['section_title']}) | Page {ev['page']} | **Relevance Score: {ev['score']:.4f}**")
                        st.markdown(f'<div class="evidence-block">{ev["text"]}</div>', unsafe_allow_html=True)
                        st.markdown("<br/>", unsafe_allow_html=True)
