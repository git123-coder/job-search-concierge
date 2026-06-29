import asyncio
import warnings
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
