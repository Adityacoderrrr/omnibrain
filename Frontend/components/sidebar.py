import streamlit as st

def render_sidebar():
    """Renders the sidebar and returns the current configuration state."""
    with st.sidebar:
        st.title("🧠 OmniBrain Control")
        st.caption("Agentic Multi-Modal RAG Orchestrator")
        st.divider()
        
        # Document Ingestion
        st.subheader("1. Document Ingestion")
        uploaded_file = st.file_uploader(
            "Upload Corporate Financial PDFs", 
            type=["pdf"], 
            accept_multiple_files=False
        )
        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name}")
            
        st.divider()
        
        # Agent Activations
        st.subheader("2. Target Tools")
        enable_sql = st.toggle("Enable Text-to-SQL Agent", value=True)
        enable_vision = st.toggle("Enable Vision-Language Agent", value=True)
        enable_search = st.toggle("Enable Vector Search Agent", value=True)
        
        st.divider()
        
        # System Status Indicators
        st.subheader("3. Infrastructure Status")
        qdrant_status = "🟢 Ready" if enable_search else "🔴 Off"
        sql_status = "🟢 Ready" if enable_sql else "🔴 Off"
        
        st.markdown(f"**Qdrant Vector DB:** {qdrant_status}")
        st.markdown(f"**Historical SQL DB:** {sql_status}")
        st.markdown("**Guardrail Engine:** 🟢 Ready")
        
        # Return the settings so app.py can use them
        return {
            "uploaded_file": uploaded_file,
            "enable_sql": enable_sql,
            "enable_vision": enable_vision,
            "enable_search": enable_search
        }