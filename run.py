import warnings
warnings.filterwarnings( "ignore", message=".*JSON_SCHEMA_FOR_FUNC_DECL.*", 
category=UserWarning, module="google.adk.tools.function_tool" )

import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import root_agent

async def main():
    app = App(name="job-search-concierge", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    
    session = await runner.session_service.create_session(
        app_name="job-search-concierge", user_id="test_user"
    )
    
    print("Running end-to-end test...")
    requests = [
        "Update Record #23 Status Interview",
        "Update Record #23 Company Google Role SDE Status Interview",
        "Update Record #23",
        "Update Record #24",
        "Role: SWE",
        "Update Record #999",
        "Update Record #23",
        "Company: Microsoft",
        "SWE",
        "Status: Interview",
        "Cancel",
        "Update Record #999",
        "Applied to Netflix for backend dev today",
        "Applied",
        "Microsoft",
        "Microsoft SWE",
        "Interview at Google",
        "Applied to Microsoft for SWE today",
        "Hi",
        "How many applications have I submitted?",
        "What should I follow up on?",
        "How is my job search going?"
    ]
    
    for user_input in requests:
        print(f"\nUser: {user_input}")
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=user_input)]),
        ):
            if event.content:
                text = ""
                for part in event.content.parts:
                    if getattr(part, 'text', None):
                        text += part.text
                if text:
                    print(f"Agent: {text}")
            
    print("\n--- applications.csv ---")
    try:
        with open("applications.csv", "r") as f:
            print(f.read())
    except FileNotFoundError:
        print("Not found.")

    print("\n--- audit.log ---")
    try:
        with open("audit.log", "r") as f:
            print(f.read())
    except FileNotFoundError:
        print("Not found.")

if __name__ == "__main__":
    asyncio.run(main())
