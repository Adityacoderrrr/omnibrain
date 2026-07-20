import streamlit as st

def render_output_tabs(memo_text: str, image_url: str, logs: dict):
    """Renders the final agent outputs into distinct, scannable tabs."""
    memo_tab, assets_tab, guardrails_tab = st.tabs([
        "📊 Investment Memo", 
        "🖼️ Retrieved Assets", 
        "🛡️ Guardrail Logs"
    ])
    
    with memo_tab:
        st.markdown(memo_text)
        
    with assets_tab:
        st.write("### Extracted Source Citations")
        st.caption("Visual elements isolated by the Vision Agent to support the memo:")
        if image_url:
            st.image(image_url, use_container_width=True)
        else:
            st.info("No visual assets were required for this query.")
            
    with guardrails_tab:
        st.write("### NeMo & Langfuse Validation")
        st.json(logs)