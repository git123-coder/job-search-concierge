import streamlit as st
import asyncio
import logging
import uuid
from app.engine import JobSearchEngine

st.set_page_config(
    page_title="Job Search Concierge",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Hide Streamlit toolbar actions, header action elements, deploy button, main menu, footer, and GitHub links
# Keep sidebar expand/collapse controls visible and interactive
st.markdown(
    """
    <style>
    [data-testid="stToolbarActions"],
    [data-testid="stToolbarActionButton"],
    [data-testid="stHeaderActionElements"],
    .stAppDeployButton,
    #MainMenu,
    footer,
    header a[href*="github.com"] {
        visibility: hidden !important;
        display: none !important;
    }

    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: inline-flex !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar informational panel
with st.sidebar:
    st.subheader("About")
    st.markdown(
        "**Job Search Concierge** helps track job applications, "
        "view analytics, and find stale applications."
    )
    st.markdown("---")
    st.markdown("**Example Commands:**")
    st.markdown("- *Applied to Google for SWE*")
    st.markdown("- *Show all applications*")
    st.markdown("- *What are my stats?*")
    st.markdown("- *Find stale applications*")

# Main page BYOK flow (at the top, above chat)
api_key_input = st.text_input(
    "Gemini API Key",
    type="password",
    value=st.session_state.get("gemini_api_key", ""),
    help="Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).",
    placeholder="Enter your Gemini API key...",
)

api_key = api_key_input.strip()
st.session_state.gemini_api_key = api_key

# Initialize session identity
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user_{uuid.uuid4()}"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Create or recreate engine if key exists and changed
if api_key:
    if "engine" not in st.session_state or st.session_state.get("current_api_key") != api_key:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        existing_state = None
        existing_session_id = st.session_state.get("session_id")
        if "engine" in st.session_state and existing_session_id:
            try:
                existing_state = loop.run_until_complete(
                    st.session_state.engine.get_session_state(
                        st.session_state.user_id, existing_session_id
                    )
                )
            except Exception as e:
                logging.error("Failed to retrieve existing session state: %s", type(e).__name__)
                existing_state = None

        st.session_state.engine = JobSearchEngine(api_key=api_key)
        new_session = loop.run_until_complete(
            st.session_state.engine.create_session(
                user_id=st.session_state.user_id,
                session_id=existing_session_id,
                state=existing_state
            )
        )
        st.session_state.session_id = new_session.id
        st.session_state.current_api_key = api_key

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input with key validation
if not api_key:
    st.info("Enter your Gemini API key above to start")
    st.chat_input("Message Job Search Concierge...", disabled=True)
else:
    if prompt := st.chat_input("Message Job Search Concierge..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response_text = loop.run_until_complete(
                        st.session_state.engine.process_message(
                            prompt, 
                            st.session_state.session_id, 
                            user_id=st.session_state.user_id
                        )
                    )
                    if response_text:
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    # Log diagnostic details server-side; never log or expose the key
                    logging.error(
                        "Agent execution error for session %s: %s: %s",
                        st.session_state.session_id,
                        type(e).__name__,
                        str(e)[:150]
                    )
                    st.error("Invalid or rate-limited API key. Please check it.")


