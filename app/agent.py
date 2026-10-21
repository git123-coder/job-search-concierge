from datetime import datetime
from functools import cached_property
from typing import Any
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import Client, types
from .tools import add_application, get_applications, calculate_analytics, find_stale_applications, update_status
from .skills import analyze_job_search

class KeyInjectedGemini(Gemini):
    """Gemini model subclass that injects a per-session API key without touching global/environment state."""
    api_key: str = ""

    @cached_property
    def api_client(self) -> Client:
        base_url, api_version = self._base_url_and_api_version
        kwargs_for_http_options: dict[str, Any] = {
            'headers': self._tracking_headers(),
            'retry_options': self.retry_options,
            'base_url': base_url,
        }
        if api_version:
            kwargs_for_http_options['api_version'] = api_version

        kwargs: dict[str, Any] = {
            'http_options': types.HttpOptions(**kwargs_for_http_options),
            'api_key': self.api_key,
        }
        if self.model.startswith('projects/'):
            kwargs['enterprise'] = True

        return Client(**kwargs)

#=======
def build_root_agent(api_key: str = None) -> Agent:
    """Builds the agent tree with an optionally injected API key."""
    model_val = KeyInjectedGemini(model="gemini-flash-lite-latest", api_key=api_key) if api_key else "gemini-flash-lite-latest"
    logger = Agent(
        name="logger_agent",
        model=model_val,
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
                    
                    Rules for RECORD UPDATING (e.g. 'Update Record #23', 'Role: SWE'):
                    - If the user explicitly asks to update a record by ID, or provides fields in reply to an ongoing update conversation:
                    - Use the update_status tool. Pass ONLY the fields the user explicitly provides. Do NOT overwrite existing fields unless explicitly provided by the user.
                    - Do NOT create a new record using add_application during an update session.
                    - After a successful update, report the complete current record to the user.
                    - If the record has missing or TBD fields, ask the user ONLY for the FIRST missing field. If multiple fields are provided at once, update all of them before asking for the next missing field.
                    - If the record is fully complete, ask "What would you like to update?". Do NOT incorrectly state it is incomplete.
                    - Clear conversational update state and resume normal logging mode when: the record is complete, the user finishes, or the user cancels.
                    - If the user asks to update a record that does not exist, report it as not found and do not create a new record.


        Rules for when AT LEAST ONE logging field is detected (and it is NOT an update request):
        - Immediately create a record using add_application.
        - Preserve extraction metadata: Before applying any defaults, track exactly which fields were extracted from the user and which were missing.
        - Fill missing fields with defaults BEFORE calling add_application (Status -> Applied, Company -> TBD, Role -> TBD, Date -> Today's date).
        - After the record is created, inform the user EXACTLY which values were assumed automatically (based on what was actually missing from their original input, not by comparing final values to defaults).
        - Do NOT report a field as assumed if the user provided it (even if the provided value happens to match the default, such as 'Applied' or 'today').
        - Remind them which information is still incomplete based solely on the originally missing fields.
        - Tell the user they can update the record now or later using the returned Record ID (use the exact record_id returned by add_application).
        # pyrefly: ignore[missing-import]
        - Do not update the record automatically from subsequent messages.""",
            description="Logs job applications to the database. Call this agent when the user wants to log an application.",
        tools=[add_application, update_status],
        )
    insights = Agent(
        name="insights_agent",
        model=model_val,
        instruction="You answer questions about application counts and response rates. Use the get_applications and calculate_analytics tools to gather data to answer the user's questions. When answering broader progress questions such as 'How is my job search going?' or 'Give me an overview of my job search.', use the analyze_job_search tool.",
        description="Provides analytics and insights about job applications.",
        tools=[get_applications, calculate_analytics, analyze_job_search],
    )
    strategy = Agent(
        name="strategy_agent",
        model=model_val,
        instruction="When asked what to follow up on or what to do next, use the get_applications, calculate_analytics, and find_stale_applications tools to identify stale applications and recommend specific next actions. Allow it to use analyze_job_search when generating recommendations.",
        description="Provides strategy and recommends next actions for job applications.",
        tools=[get_applications, calculate_analytics, find_stale_applications, analyze_job_search],
    )

    supervisor = Agent(
        name="supervisor_agent",
        model=model_val,
        instruction="You are the supervisor. If the user wants to log a new job application or update an existing application record, delegate to the logger_agent. If the user asks for application counts, analytics, or how they are doing, delegate to the insights_agent. If the user asks what to follow up on or what to do next, delegate to the strategy_agent. Do not attempt to process the request yourself.",
        sub_agents=[logger, insights, strategy],
    )
    return supervisor
    
root_agent = build_root_agent()
logger_agent = root_agent.sub_agents[0]
insights_agent = root_agent.sub_agents[1]
strategy_agent = root_agent.sub_agents[2]
supervisor_agent = root_agent