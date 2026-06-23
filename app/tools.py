import csv
import os
from google.adk.tools import ToolContext
from .security import validate_application, audit_log

CSV_FILE = "applications.csv"
CSV_HEADERS = ["id", "company", "role", "status", "date_applied", "last_updated"]

def add_application(company: str, role: str, status: str, date_applied: str, tool_context: ToolContext) -> dict:
    """Logs a job application.
    
    Args:
        company: The name of the company.
        role: The role applied for.
        status: The application status.
        date_applied: The date the application was made in YYYY-MM-DD format.
    
    Returns:
        A dict indicating success or error.
    """
    agent_name = tool_context.node.name if tool_context and tool_context.node else "UnknownAgent"
    tool_name = "add_application"
    
    error = validate_application(company, role, status, date_applied)
    if error:
        audit_log(agent_name, tool_name, "FAILURE", error)
        return {"status": "error", "message": error}
        
    try:
        file_exists = os.path.exists(CSV_FILE)
        row_id = 1
        
        if file_exists:
            with open(CSV_FILE, "r") as f:
                row_count = sum(1 for _ in f)
                if row_count > 0:
                    row_id = row_count
                    
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(CSV_HEADERS)
            writer.writerow([row_id, company, role, status, date_applied, ""])
            
        success_msg = f"Logged application: {company} - {role}"
        audit_log(agent_name, tool_name, "SUCCESS", success_msg)
        return {"status": "success", "message": success_msg}
    except Exception as e:
        error_msg = f"Failed to write to CSV: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}
