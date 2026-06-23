from google.adk.agents import Agent
from .tools import add_application

logger_agent = Agent(
    name="logger_agent",
    model="gemini-2.5-flash",
    instruction="You log applications. Extract company, role, status, and date_applied, then call add_application.",
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
