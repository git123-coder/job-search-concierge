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
                
                Rules for when NO logging fields are detected (e.g., 'Hi'):
                - Do not create a record.
                - Respond conversationally and clearly communicate: "I can help log your application. Just provide any one of: Status, Company, Role, Date (optional)".
                
                Rules for when AT LEAST ONE logging field is detected (EVEN if it is just a Status like 'Applied'):
                - Immediately create a record using add_application.
                - Preserve extraction metadata: Before applying any defaults, track exactly which fields were extracted from the user and which were missing.
                - Fill missing fields with defaults BEFORE calling add_application (Status -> Applied, Company -> TBD, Role -> TBD, Date -> Today's date).
                - After the record is created, inform the user EXACTLY which values were assumed automatically (based on what was actually missing from their original input, not by comparing final values to defaults).
                - Do NOT report a field as assumed if the user provided it (even if the provided value happens to match the default, such as 'Applied' or 'today').
                - Remind them which information is still incomplete based solely on the originally missing fields.
                - Tell the user they can update the record now or later using the returned Record ID (use the exact record_id returned by add_application).
                - Do not update the record automatically from subsequent messages.""",
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
