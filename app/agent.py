from datetime import datetime
from google.adk.agents import Agent
from .tools import add_application, get_applications, calculate_analytics, find_stale_applications, update_status
from .skills import analyze_job_search

logger_agent = Agent(
    name="logger_agent",
    model="gemini-flash-lite-latest",
    instruction=f"""
                You log job applications. 
                Today's date is {datetime.now().strftime('%Y-%m-%d')}.
                Extract the following fields whenever present from the user's message:
                - company
                - role
                - status
                - date_applied
                
                Rules:
                - Support partial information. Missing fields should simply remain empty internally (e.g., pass empty strings).
                - Do NOT apply default values.
                - Do NOT prompt for missing fields or ask the user a question.
                - Call add_application immediately with whatever fields were extracted.""",
    description="Logs job applications to the database. Call this agent when the user wants to log an application.",
    tools=[add_application, update_status],
)

insights_agent = Agent(
    name="insights_agent",
    model="gemini-flash-lite-latest",
    instruction="You answer questions about application counts and response rates. Use the get_applications and calculate_analytics tools to gather data to answer the user's questions. When answering broader progress questions such as 'How is my job search going?' or 'Give me an overview of my job search.', use the analyze_job_search tool.",
    description="Provides analytics and insights about job applications.",
    tools=[get_applications, calculate_analytics, analyze_job_search],
)

strategy_agent = Agent(
    name="strategy_agent",
    model="gemini-flash-lite-latest",
    instruction="When asked what to follow up on or what to do next, use the get_applications, calculate_analytics, and find_stale_applications tools to identify stale applications and recommend specific next actions. Allow it to use analyze_job_search when generating recommendations.",
    description="Provides strategy and recommends next actions for job applications.",
    tools=[get_applications, calculate_analytics, find_stale_applications, analyze_job_search],
)

supervisor_agent = Agent(
    name="supervisor_agent",
    model="gemini-flash-lite-latest",
    instruction="You are the supervisor. If the user wants to log a job application, delegate to the logger_agent. If the user asks for application counts, analytics, or how they are doing, delegate to the insights_agent. If the user asks what to follow up on or what to do next, delegate to the strategy_agent. Do not attempt to process the request yourself.",
    sub_agents=[logger_agent, insights_agent, strategy_agent],
)

root_agent = supervisor_agent
