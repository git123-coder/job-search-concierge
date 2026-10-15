import asyncio
import uuid
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.agent import root_agent

class JobSearchEngine:
    def __init__(self):
        self.app = App(name="job-search-concierge", root_agent=root_agent)
        self.runner = InMemoryRunner(app=self.app)

    async def create_session(self, user_id=None):
        if not user_id:
            user_id = f"user_{uuid.uuid4()}"
        session = await self.runner.session_service.create_session(
            app_name="job-search-concierge", user_id=user_id
        )
        return session

    async def process_message(self, user_input: str, session_id: str, user_id="test_user") -> str:
        response_text = ""
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
