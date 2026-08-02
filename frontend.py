"""
OmniBrain Streamlit Frontend Application.

Provides a modern, high-performance web dashboard for PDF document upload,
background status tracking, multi-modal query orchestration, source citation inspection,
confidence score rendering, and LangGraph agent execution trace visualization.

Run with:
    streamlit run frontend.py
"""

import os
import uuid
import requests
import streamlit as st
from typing import Dict, Any, List

# Configuration Defaults
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Streamlit Page Setup
st.set_page_config(
    page_title="OmniBrain — Multi-Modal RAG Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphism & High-Contrast Typography)
st.markdown("""
<style>
    /* Dark Theme Customization */
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header Container */
    .header-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Title Badge */
    .badge-tag {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Citation Card */
    .citation-box {
        background-color: #161b22;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }

    /* Trace Pill */
    .trace-step {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 6px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #58a6ff;
    }

    /* Metric Box */
    .metric-pill {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 8px 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "active_document_id" not in st.session_state:
    st.session_state["active_document_id"] = None
if "uploaded_documents" not in st.session_state:
    st.session_state["uploaded_documents"] = {}
if "session_id" not in st.session_state:
    st.session_state["session_id"] = f"session_{uuid.uuid4().hex[:8]}"
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.title("🧠 OmniBrain Control")
    st.caption("Enterprise Multi-Modal Agentic Orchestrator")
    
    backend_url = st.text_input("FastAPI Backend URL", value=DEFAULT_BACKEND_URL)
    session_id_input = st.text_input("Active Session ID", value=st.session_state["session_id"])
    st.session_state["session_id"] = session_id_input
    
    # Backend Health Check
    try:
        health_resp = requests.get(f"{backend_url}/health", timeout=2)
        if health_resp.status_code == 200:
            st.success("🟢 Backend Connected", icon="✅")
        else:
            st.error("🔴 Backend Offline", icon="⚠️")
    except Exception:
        st.warning("⚠️ Backend Service Unavailable")

    st.markdown("---")
    st.subheader("📄 Document Inventory")
    
    if st.session_state["uploaded_documents"]:
        doc_options = list(st.session_state["uploaded_documents"].keys())
        selected_doc = st.selectbox(
            "Select Active Document ID",
            options=doc_options,
            format_func=lambda d: f"{st.session_state['uploaded_documents'][d]['filename']} ({d[:8]}...)"
        )
        st.session_state["active_document_id"] = selected_doc
    else:
        st.info("No documents uploaded yet.")

# --- MAIN DASHBOARD HEADER ---
st.markdown("""
<div class="header-card">
    <span class="badge-tag">Enterprise Architecture</span>
    <h1 style="margin-top: 8px; margin-bottom: 4px; font-size: 2.2rem; color: #f0f6fc;">
        OmniBrain Orchestrator
    </h1>
    <p style="color: #8b949e; font-size: 1.05rem; margin-bottom: 0;">
        Intelligent multi-agent RAG reasoning across text documents, tabular data, visual chart regions, and relational databases with MemorySaver session persistence.
    </p>
</div>
""", unsafe_allow_html=True)

# Layout Columns
col_upload, col_query = st.columns([1, 1.8], gap="large")

# --- COLUMN 1: DOCUMENT INGESTION & PROCESSING ---
with col_upload:
    st.header("1. Ingestion Pipeline")
    uploaded_file = st.file_uploader("Upload Document (PDF)", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("🚀 Upload & Ingest PDF", use_container_width=True):
            with st.spinner("Uploading document to backend..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{backend_url}/documents/upload", files=files, timeout=10)
                    
                    if response.status_code == 202:
                        data = response.json()
                        doc_id = data["document_id"]
                        
                        st.session_state["uploaded_documents"][doc_id] = {
                            "filename": uploaded_file.name,
                            "status": data["status"],
                            "submitted_at": data["submitted_at"]
                        }
                        st.session_state["active_document_id"] = doc_id
                        st.success(f"Document submitted! ID: `{doc_id}`")
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as exc:
                    st.error(f"Upload error: {str(exc)}")

    # Polling Status for Active Document
    if st.session_state["active_document_id"]:
        active_id = st.session_state["active_document_id"]
        doc_meta = st.session_state["uploaded_documents"].get(active_id, {})
        
        st.subheader("Document Ingestion Telemetry")
        st.write(f"**Filename:** `{doc_meta.get('filename')}`")
        st.write(f"**Document ID:** `{active_id}`")
        
        status_placeholder = st.empty()
        
        if st.button("🔄 Refresh Status", use_container_width=True):
            try:
                status_resp = requests.get(f"{backend_url}/documents/{active_id}/status", timeout=5)
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    st.session_state["uploaded_documents"][active_id]["status"] = status_data["status"]
                    st.toast(f"Status updated: {status_data['status']}")
            except Exception as exc:
                st.error(f"Status check error: {exc}")

        current_status = st.session_state["uploaded_documents"][active_id].get("status", "unknown")
        
        if current_status == "ready":
            status_placeholder.success("Status: Ready for Agentic Querying ✅")
        elif current_status == "failed":
            status_placeholder.error("Status: Ingestion Failed ❌")
        else:
            status_placeholder.info(f"Status: {current_status.upper()} ⏳")

# --- COLUMN 2: MULTI-AGENT QUERY & REASONING ---
with col_query:
    st.header("2. Agentic Reasoning & Queries")
    
    active_doc_id = st.session_state.get("active_document_id")
    
    if not active_doc_id:
        st.warning("Please upload or select an active document in the sidebar to enable queries.")
    else:
        st.caption(f"Target Document: `{active_doc_id}` | Session: `{st.session_state['session_id']}`")
        
        # Sample Query Templates
        st.markdown("**Quick Query Presets:**")
        preset_cols = st.columns(3)
        query_input_value = ""
        
        if preset_cols[0].button("📊 SQL Analytics"):
            query_input_value = "What is total sales revenue in the US database records?"
        if preset_cols[1].button("📈 Visual Chart"):
            query_input_value = "What trend does the figure on page 2 illustrate?"
        if preset_cols[2].button("📄 Text Summary"):
            query_input_value = "Summarize the annual summary paragraph in the text."

        question = st.text_area("Ask a question across text, charts, or relational databases:", value=query_input_value, height=100)
        
        if st.button("⚡ Execute Agent Workflow", type="primary", use_container_width=True):
            if not question.strip():
                st.error("Please enter a question prompt.")
            else:
                with st.spinner("Supervisor orchestrating LangGraph multi-agent pipeline..."):
                    try:
                        payload = {
                            "document_id": active_doc_id,
                            "question": question,
                            "session_id": st.session_state["session_id"]
                        }
                        query_resp = requests.post(f"{backend_url}/query", json=payload, timeout=30)
                        
                        if query_resp.status_code == 200:
                            res_data = query_resp.json()
                            
                            # Render Tabbed Output Panel
                            st.markdown("---")
                            memo_tab, assets_tab, guardrails_tab = st.tabs([
                                "📊 Answer & Memo", 
                                "🖼️ Retrieved Assets", 
                                "🛡️ Guardrail Logs & Trace"
                            ])
                            
                            with memo_tab:
                                st.subheader("Consolidated Response")
                                st.markdown(res_data.get('answer', ''))
                                sql_expl = res_data.get("sql_explanation")
                                if sql_expl:
                                    st.info(f"💡 **SQL Explanation**: {sql_expl}")

                            with assets_tab:
                                st.subheader("Source Citations & Attributions")
                                citations = res_data.get("citations", [])
                                if citations:
                                    for cit in citations:
                                        st.markdown(
                                            f"""<div class="citation-box">
                                                <strong>Page {cit.get('page', 1)} | Type: {cit.get('source_type', 'text').upper()}</strong><br/>
                                                <span style="color: #8b949e;">{cit.get('snippet', 'N/A')}</span>
                                            </div>""",
                                            unsafe_allow_html=True
                                        )
                                else:
                                    st.info("No external visual or text citations attached.")

                            with guardrails_tab:
                                conf_scores = res_data.get("confidence_scores", {})
                                if conf_scores:
                                    st.subheader("Confidence Telemetry")
                                    conf_cols = st.columns(len(conf_scores))
                                    for idx, (agent_k, score_v) in enumerate(conf_scores.items()):
                                        conf_cols[idx].metric(label=f"Agent [{agent_k.upper()}]", value=f"{score_v * 100:.0f}%")

                                st.subheader("LangGraph Telemetry & Execution Trace")
                                trace_steps = res_data.get("agent_trace", [])
                                for step in trace_steps:
                                    st.markdown(f'<div class="trace-step">➔ {step}</div>', unsafe_allow_html=True)

                            # Persist session state message
                            st.session_state["messages"].append({
                                "role": "user", "content": question
                            })
                            st.session_state["messages"].append({
                                "role": "assistant", 
                                "content": res_data.get("answer", ""),
                                "res_data": res_data
                            })

                        else:
                            st.error(f"Query execution failed ({query_resp.status_code}): {query_resp.text}")
                    except Exception as exc:
                        st.error(f"Execution exception: {str(exc)}")


st.markdown("---")
st.caption("OmniBrain Platform — Enterprise Multi-Modal Agentic RAG Orchestrator")
