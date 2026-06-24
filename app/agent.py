from google.adk.agents import Agent
from .tools import add_application, get_applications, calculate_analytics

logger_agent = Agent(
    name="logger_agent",
    model="gemini-2.5-flash",
    instruction="You log applications. Extract company, role, status, and date_applied, then call add_application.",
    description="Logs job applications to the database. Call this agent when the user wants to log an application.",
    tools=[add_application],
)

insights_agent = Agent(
    name="insights_agent",
    model="gemini-2.5-flash",
    instruction="You answer questions about application counts and response rates. Use the get_applications and calculate_analytics tools to gather data to answer the user's questions.",
    description="Provides analytics and insights about job applications.",
    tools=[get_applications, calculate_analytics],
)

supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-2.5-flash",
    instruction="You are the supervisor. If the user wants to log a job application, delegate to the logger_agent. If the user asks for application counts, analytics, or how they are doing, delegate to the insights_agent. Do not attempt to process the request yourself.",
    sub_agents=[logger_agent, insights_agent],
)

root_agent = supervisor_agent
