from datetime import datetime
from google.adk.agents import Agent
from .tools import add_application

logger_agent = Agent(
    name="logger_agent",
    model="gemini-2.5-flash",
    instruction="You log job applications. Today's date is {datetime.now().strftime('%Y-%m-%d')}."
                f"Extract company, role, status, and date_applied from the user's message. "
                f"If the user says 'today' or doesn't specify a date, use today's date above. "
                f"Default status to 'Applied' if not mentioned. "
                f"Call add_application immediately with these fields. Never ask the user a question.",
    description="Logs job applications to the database. Call this agent when the user wants to log an application.",
    tools=[add_application],
)

supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.5-flash",
    instruction="You are the supervisor. If the user wants to log a job application, delegate to the logger_agent. Do not attempt to process it yourself.",
    sub_agents=[logger_agent],
)

root_agent = supervisor_agent
