import streamlit as st
import asyncio
from app.engine import JobSearchEngine

st.set_page_config(page_title="Job Search Concierge", layout="centered")

# Initialize engine and session
if "engine" not in st.session_state:
    st.session_state.engine = JobSearchEngine()

if "session_id" not in st.session_state:
    # Run async function to create session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    session = loop.run_until_complete(st.session_state.engine.create_session("streamlit_user"))
    st.session_state.session_id = session.id
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Message Job Search Concierge..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(
                st.session_state.engine.process_message(
                    prompt, 
                    st.session_state.session_id, 
                    user_id="streamlit_user"
                )
            )
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
