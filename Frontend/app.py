import streamlit as st
import time
from components.sidebar import render_sidebar
from components.result_tabs import render_output_tabs

st.set_page_config(page_title="OmniBrain", layout="wide")

# Render the sidebar and catch the user's settings
app_config = render_sidebar()

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="OmniBrain Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished alignment and spacing
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stStatus { margin-top: 1rem; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MOCK BACKEND CLIENT (For Frontend Testing)
# ==========================================
def mock_agent_stream(prompt):
    """Simulates the LangGraph supervisor routing tasks to different agents."""
    steps = [
        ("Parsing complex tables using Vision-Language Model (VLM)...", "Extracted Q3 balance sheet showing 12% margin expansion."),
        ("Querying FAISS/Qdrant vector database for semantic context...", "Found 3 relevant paragraphs regarding risk factors in Chapter 4."),
        ("Executing Text-to-SQL agent on historical stock data...", "SELECT ticker, close FROM stock_history WHERE date >= '2025-01-01';\nReturned 180 rows."),
        ("Running Langfuse evaluations & NeMo Guardrails check...", "Output verified: Toxicity 0.0, Grounding Score: 0.98. No hallucinations detected.")
    ]
    for status_text, detail in steps:
        time.sleep(1.5)  # Simulate API latency
        yield status_text, detail

# ==========================================
# MAIN WORKSPACE LAYOUT
# ==========================================
st.title("Financial Analysis Workspace")
st.write("Submit complex queries spanning semantic text, embedded tables, and historical database patterns.")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display historical messages from the session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there were multimodal outputs generated for this turn, re-display them
        if "tabs_data" in message:
            t1, t2, t3 = st.tabs(["📊 Investment Memo", "🖼️ Retrieved Assets", "🛡️ Guardrail Logs"])
            with t1: st.markdown(message["tabs_data"]["memo"])
            with t2: st.info("Visual charts cited in this turn.")
            with t3: st.json(message["tabs_data"]["logs"])

# ==========================================
# CHAT INPUT & ORCHESTRATION TRACE
# ==========================================
if user_input := st.chat_input("Ask OmniBrain (e.g., 'Analyze Q3 net margins against historical valuation spikes')"):
    
    # 1. Render User Input immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # 2. Open Assistant Response Container
    with st.chat_message("assistant"):
        
        # Real-time Agent Trace / Chain of Thought container
        with st.status("Supervisor Agent initializing routing plan...", expanded=True) as status:
            agent_details = []
            
            # Stream events from the orchestrator
            for status_update, detail_text in mock_agent_stream(user_input):
                status.update(label=status_update)
                # Nest expanders inside the tracking area to inspect raw tool outputs
                with st.expander(f"Details: {status_update[:30]}..."):
                    st.code(detail_text)
                agent_details.append((status_update, detail_text))
                
            status.update(label="Synthesis complete! Document memo compiled.", state="complete")
            
        # 3. Present Multimodal Output & Citation Panel using Tabs
        st.markdown("---")
        memo_tab, assets_tab, guardrails_tab = st.tabs([
            "📊 Investment Memo", 
            "🖼️ Retrieved Assets", 
            "🛡️ Guardrail Logs"
        ])
        
        # Sample structured results to demonstrate component rendering
        mock_memo = f"""
        ### Executive Investment Memo
        Based on the analyzed context from the uploaded dossier and historical data:
        
        *   **Current Margin Performance:** The parsing of the embedded Q3 tables indicates a **12% operating margin expansion**, driven largely by a sharp reduction in cost of goods sold (COGS).
        *   **Historical Context:** Cross-referencing this pattern via Text-to-SQL against the database confirms this is the highest margin milestone recorded since Q2 2022.
        *   **Risk Mitigation:** Grounding metrics verified by NeMo ensure zero external hallucination outside the source data bounds.
        """
        
        with memo_tab:
            st.markdown(mock_memo)
            
        with assets_tab:
            st.write("### Extracted Source Citations")
            st.caption("The Vision agent isolated the following graphical element to back up the memo:")
            # Replace with a real layout or st.image when integrating image_agent tags
            st.image(
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=600", 
                caption="Figure 3.2: Operating Margin Trends vs COGS (Extracted Page 42)", 
                use_container_width=True
            )
            
        with guardrails_tab:
            mock_logs = {"toxicity_score": 0.00, "context_grounding": 0.98, "latency_ms": 4820}
            st.json(mock_logs)
            
        # Save complete state into session history so it persists when UI redraws
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Analysis finalized. See the tabs below for complete details.",
            "tabs_data": {
                "memo": mock_memo,
                "logs": mock_logs
            }
        })