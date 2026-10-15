import datetime

ALLOWED_STATUSES = ["Applied", "Interview", "Offer", "Rejected"]
AUDIT_LOG_FILE = "audit.log"

def validate_application(company: str, role: str, status: str, date_applied: str) -> str | None:
    if status and status not in ALLOWED_STATUSES:
        return f"Status must be one of {ALLOWED_STATUSES}."
    if date_applied:
        try:
            datetime.datetime.strptime(date_applied, "%Y-%m-%d")
        except ValueError:
            return "Date must be a valid YYYY-MM-DD string."
    return None

def audit_log(agent_name: str, tool_name: str, status: str, message: str = ""):
    timestamp = datetime.datetime.now().isoformat()
    log_line = f"{timestamp} | {agent_name} | {tool_name} | {status}\n"
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(log_line)
