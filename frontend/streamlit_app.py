import streamlit as st
import requests
import os
import json

# Sync Streamlit Cloud secrets into os.environ
try:
    for k, v in st.secrets.items():
        if isinstance(v, str):
            os.environ.setdefault(k, v)
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="3GPP Standards AI Assistant",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ChatGPT-like sleek dark/light aesthetic
st.markdown("""
<style>
    /* Hide default Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 800px;
    }
    
    /* Header styling */
    .chat-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-color, #0F172A);
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .chat-subtitle {
        font-size: 0.95rem;
        color: var(--text-color, #64748B);
        opacity: 0.8;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* Badges */
    .badge-grounded {
        display: inline-flex;
        align-items: center;
        background-color: #DCFCE7;
        color: #15803D;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .badge-refusal {
        display: inline-flex;
        align-items: center;
        background-color: #FEE2E2;
        color: #B91C1C;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* Citation Tags */
    .citation-container {
        margin-top: 0.75rem;
        margin-bottom: 0.5rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
    }
    .citation-chip {
        background-color: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.3);
        color: var(--text-color, #0F172A);
        border-radius: 0.375rem;
        padding: 0.25rem 0.5rem;
        font-size: 0.82rem;
        font-weight: 500;
    }

    /* Evidence Block */
    .evidence-passage {
        background-color: rgba(148, 163, 184, 0.1);
        border-left: 3px solid #0EA5E9;
        padding: 0.6rem 0.8rem;
        border-radius: 0.25rem;
        font-size: 0.85rem;
        font-family: monospace;
        color: var(--text-color, #1E293B);
        margin-bottom: 0.5rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize Chat History in Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Controls, Quick Test Questions, and Corpus Info
with st.sidebar:
    st.markdown("### ⚙️ Developer & Controls")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### 💡 Quick Test Prompts")
    prompt_to_send = None
    if st.button("AMF Role in Registration", use_container_width=True):
        prompt_to_send = "What is the role of the AMF during UE registration?"
    if st.button("TS 24.501 T3510 Timer", use_container_width=True):
        prompt_to_send = "According to TS 24.501, what is T3510?"
    if st.button("5G Registration Steps", use_container_width=True):
        prompt_to_send = "What happens during the 5G registration procedure?"
    if st.button("UPF Key Functions", use_container_width=True):
        prompt_to_send = "What are the main functions of the User Plane Function (UPF)?"
    if st.button("Test Unanswerable Question", use_container_width=True):
        prompt_to_send = "What is the optimal coffee brewing temperature for 5G engineers?"

    st.divider()
    st.markdown("### 📚 Indexed Corpus")
    try:
        res = requests.get(f"{API_URL}/documents", timeout=2)
        if res.status_code == 200:
            docs = res.json()
            st.success(f"Loaded Specifications: {len(docs)}")
            for d in docs:
                st.caption(f"• **TS {d['spec_number']}** ({d['release']}) - {d['chunk_count']} chunks")
    except Exception:
        st.caption("• **TS 23.501** (Rel-18)\n• **TS 23.502** (Rel-18)\n• **TS 24.501** (Rel-18)\n• **TS 38.331** (Rel-18)")

    st.divider()
    st.markdown("### 🛡️ RAG Safeguards")
    st.caption("✓ Spec & Release Aware Retrieval\n✓ FAISS + BM25 Reciprocal Rank Fusion\n✓ Cross-Encoder Candidate Reranker\n✓ Evidence Sufficiency Threshold Check\n✓ Claim-Level Post-Gen Verification")


# Main ChatGPT Header
st.markdown('<div class="chat-title">📡 3GPP Standards AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="chat-subtitle">Grounded Q&A backed by official 3GPP specifications</div>', unsafe_allow_html=True)


# Render Existing Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant":
            # Display Grounded / Refusal Badge
            is_grounded = msg.get("grounded", False)
            confidence = msg.get("confidence", 0.0) * 100
            
            if is_grounded:
                st.markdown(f'<div class="badge-grounded">✓ Grounded (Confidence: {confidence:.0f}%)</div>', unsafe_allow_html=True)
            elif "could not find sufficient evidence" in msg["content"].lower():
                st.markdown(f'<div class="badge-refusal">⚠️ Insufficient Evidence / Refusal</div>', unsafe_allow_html=True)

            # Display Citations directly below answer
            sources = msg.get("sources", [])
            if sources:
                st.markdown("**Citations:**")
                citation_html = '<div class="citation-container">'
                for src in sources:
                    citation_html += f'<div class="citation-chip">📖 TS {src["spec_number"]} ({src["release"]}) | Sec {src["section"]} | Pg {src.get("page", "N/A")}</div>'
                citation_html += '</div>'
                st.markdown(citation_html, unsafe_allow_html=True)

            # Display Expandable Retrieved Evidence Drawer
            evidence = msg.get("evidence", [])
            if evidence:
                with st.expander(f"🔍 View Retrieved Evidence ({len(evidence)} passages)"):
                    for ev in evidence:
                        st.markdown(f"**[Chunk: {ev['chunk_id']}]** | TS {ev['spec_number']} ({ev['release']}) | Section {ev['section']} | Score: `{ev['score']:.4f}`")
                        st.markdown(f'<div class="evidence-passage">{ev["text"]}</div>', unsafe_allow_html=True)


# Process User Input (either typed or triggered from sidebar)
user_query = st.chat_input("Ask a question about 3GPP specifications...")
active_query = user_query or prompt_to_send

if active_query:
    # Append & display User message
    st.session_state.messages.append({"role": "user", "content": active_query})
    with st.chat_message("user"):
        st.markdown(active_query)

    # Process Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Retrieving authoritative 3GPP evidence..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"question": active_query},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                else:
                    data = None
            except Exception:
                # Standalone Python RAG Engine execution
                from app.query.query_parser import QueryParser
                from app.retrieval.hybrid import HybridRetriever
                from app.generation.generator import GroundedGenerator
                
                qp = QueryParser.parse_query(active_query)
                retriever = HybridRetriever()
                gen = GroundedGenerator()
                chunks = retriever.retrieve(active_query, spec_filter=qp.get("specification"), release_filter=qp.get("release"))
                resp_obj = gen.generate_answer(active_query, chunks)
                data = resp_obj.dict()

            if data:
                answer_text = data.get("answer", "")
                is_grounded = data.get("grounded", False)
                confidence = data.get("confidence", 0.0)
                sources = data.get("sources", [])
                evidence = data.get("evidence", [])

                # Render Answer text
                st.markdown(answer_text)

                # Render Grounded / Refusal Badge
                if is_grounded:
                    st.markdown(f'<div class="badge-grounded">✓ Grounded (Confidence: {confidence * 100:.0f}%)</div>', unsafe_allow_html=True)
                elif "could not find sufficient evidence" in answer_text.lower():
                    st.markdown(f'<div class="badge-refusal">⚠️ Insufficient Evidence / Refusal</div>', unsafe_allow_html=True)

                # Render Citations Chips
                if sources:
                    st.markdown("**Citations:**")
                    citation_html = '<div class="citation-container">'
                    for src in sources:
                        citation_html += f'<div class="citation-chip">📖 TS {src["spec_number"]} ({src["release"]}) | Sec {src["section"]} | Pg {src.get("page", "N/A")}</div>'
                    citation_html += '</div>'
                    st.markdown(citation_html, unsafe_allow_html=True)

                # Render Retrieved Evidence Drawer
                if evidence:
                    with st.expander(f"🔍 View Retrieved Evidence ({len(evidence)} passages)"):
                        for ev in evidence:
                            st.markdown(f"**[Chunk: {ev['chunk_id']}]** | TS {ev['spec_number']} ({ev['release']}) | Section {ev['section']} | Score: `{ev['score']:.4f}`")
                            st.markdown(f'<div class="evidence-passage">{ev["text"]}</div>', unsafe_allow_html=True)

                # Store assistant response in session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "grounded": is_grounded,
                    "confidence": confidence,
                    "sources": sources,
                    "evidence": evidence
                })
