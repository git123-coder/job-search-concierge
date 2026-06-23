import datetime

ALLOWED_STATUSES = ["Applied", "Interview", "Offer", "Rejected"]
AUDIT_LOG_FILE = "audit.log"

def validate_application(company: str, role: str, status: str, date_applied: str) -> str | None:
    if not company or not company.strip():
        return "Company cannot be empty."
    if not role or not role.strip():
        return "Role cannot be empty."
    if status not in ALLOWED_STATUSES:
        return f"Status must be one of {ALLOWED_STATUSES}."
    try:
        datetime.datetime.strptime(date_applied, "%Y-%m-%d")
    except ValueError:
        return "Date must be a valid YYYY-MM-DD string."
    return None

def audit_log(agent_name: str, tool_name: str, status: str, message: str):
    timestamp = datetime.datetime.now().isoformat()
    log_line = f"{timestamp} | {agent_name} | {tool_name} | {status} | {message}\n"
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(log_line)
