import streamlit as st
from components.sidebar import render_sidebar
from components.result_tabs import render_output_tabs
from api_client import send_query_to_orchestrator

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="OmniBrain Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished alignment
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stStatus { margin-top: 1rem; margin-bottom: 1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# RENDER SIDEBAR & GET CONFIG
# ==========================================
# This calls the function we built yesterday and saves the user's toggles
app_config = render_sidebar()

# ==========================================
# MAIN WORKSPACE
# ==========================================
st.title("Financial Analysis Workspace")
st.write("Submit complex queries spanning semantic text, embedded tables, and historical database patterns.")

# Initialize chat history in session state so it doesn't disappear on reload
if "messages" not in st.session_state:
    st.session_state.messages = []

# Redraw previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message had multimodal tabs attached, redraw them
        if "tabs_data" in message:
            render_output_tabs(
                memo_text=message["tabs_data"]["memo"],
                image_url=message["tabs_data"]["image_url"],
                logs=message["tabs_data"]["logs"]
            )

# ==========================================
# CHAT INPUT & EXECUTION LOGIC
# ==========================================
if user_input := st.chat_input("Ask OmniBrain (e.g., 'Analyze Q3 net margins against historical valuation')"):
    
    # 1. Show the user's message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # 2. Trigger the Assistant's response
    with st.chat_message("assistant"):
        
        # Open a status box to show the "Waiter" (API client) updates
        with st.status("Initializing OmniBrain Orchestrator...", expanded=True) as status_box:
            
            final_data = None
            
            # Loop through the yielded items from our API Client
            for response_chunk in send_query_to_orchestrator(user_input, app_config):
                
                if response_chunk["type"] == "status":
                    # Update the status box label
                    status_box.update(label=response_chunk["label"])
                    # Add a drop-down detail for the UI
                    with st.expander(f"Detail: {response_chunk['label'][:30]}..."):
                        st.write(response_chunk["detail"])
                        
                elif response_chunk["type"] == "final_result":
                    # Catch the final payload and close the status box
                    final_data = response_chunk
                    status_box.update(label="Synthesis complete! Document memo compiled.", state="complete")
        
        # 3. Render the final output tabs if we got data back
        if final_data:
            st.markdown("---")
            render_output_tabs(
                memo_text=final_data["memo"],
                image_url=final_data["image_url"],
                logs=final_data["logs"]
            )
            
            # Save the assistant's final state to the chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Analysis finalized. See the tabs below for complete details.",
                "tabs_data": final_data
            })