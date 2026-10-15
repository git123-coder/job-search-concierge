import os
import asyncio
import warnings
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings( "ignore", message=".*JSON_SCHEMA_FOR_FUNC_DECL.*", 
category=UserWarning, module="google.adk.tools.function_tool" )

from app.engine import JobSearchEngine

async def main():
    engine = JobSearchEngine()
    session = await engine.create_session(user_id="test_user")
    
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
        response = await engine.process_message(user_input, session.id, user_id="test_user")
        if response:
            print(f"Agent: {response}")
            
    print("\n--- In-Memory Session Applications ---")
    session_data = await engine.runner.session_service.get_session(
        app_name="job-search-concierge", user_id="test_user", session_id=session.id
    )
    if session_data:
        print(session_data.state.get("applications", []))

    print("\n--- applications.csv Check ---")
    if os.path.exists("applications.csv"):
        print("WARNING: applications.csv was created!")
    else:
        print("Confirmed: applications.csv does NOT exist (session-only storage in use).")

    print("\n--- audit.log ---")
    try:
        with open("audit.log", "r") as f:
            print(f.read())
    except FileNotFoundError:
        print("Not found.")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        print("Note: GEMINI_API_KEY is not set in environment.")
        print("Running in-memory session storage test suite (test_session_storage.py)...")
        import unittest
        suite = unittest.defaultTestLoader.loadTestsFromName("test_session_storage")
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
    else:
        asyncio.run(main())


