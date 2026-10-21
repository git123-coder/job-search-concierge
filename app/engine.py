import asyncio
import logging
import uuid
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import build_root_agent, root_agent
logger = logging.getLogger(__name__)

class JobSearchEngine:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        root = build_root_agent(api_key=api_key) if api_key else root_agent
        self.app = App(name="job-search-concierge", root_agent=root)
        self.runner = InMemoryRunner(app=self.app)


    async def create_session(self, user_id=None, session_id=None, state=None):
        if not user_id:
            user_id = f"user_{uuid.uuid4()}"
        session = await self.runner.session_service.create_session(
                        app_name="job-search-concierge", user_id=user_id, session_id=session_id, state=state
        )
        return session

    async def get_session_state(self, user_id: str, session_id: str) -> dict:
        session = await self.runner.session_service.get_session(
            app_name="job-search-concierge", user_id=user_id, session_id=session_id
        )
        return dict(session.state) if session and session.state else {}
    
    async def process_message(self, user_input: str, session_id: str, user_id="test_user") -> str:
        response_text = ""
        try:
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=user_input)]),
        ):
                if event.content:
                    text = ""
                    for part in event.content.parts:
                        if getattr(part, 'text', None):
                            text += part.text
                    if text:
                        response_text += text
            return response_text
        except Exception as e:
            # Server-side diagnostic log; never log the key
            logger.error("Engine execution error for session %s: %s", session_id, type(e).__name__)
            raise