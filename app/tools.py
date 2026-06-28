import csv
import os
import datetime
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
        return {"status": "success", "record_id": row_id, "message": success_msg}
    except Exception as e:
        error_msg = f"Failed to write to CSV: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}

def get_applications(tool_context: ToolContext) -> dict:
    """Retrieves all job applications from the database.
    
    Returns:
        A dict containing a list of application records.
    """
    agent_name = tool_context.node.name if tool_context and tool_context.node else "UnknownAgent"
    tool_name = "get_applications"
    
    try:
        if not os.path.exists(CSV_FILE):
            audit_log(agent_name, tool_name, "SUCCESS", "File does not exist, returned empty.")
            return {"status": "success", "data": []}
            
        data = []
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        audit_log(agent_name, tool_name, "SUCCESS", f"Retrieved {len(data)} applications.")
        return {"status": "success", "data": data}
    except Exception as e:
        error_msg = f"Failed to read CSV: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}

def calculate_analytics(tool_context: ToolContext) -> dict:
    """Calculates analytics for job applications (counts and response rate).
    
    Returns:
        A dict containing the calculated metrics.
    """
    agent_name = tool_context.node.name if tool_context and tool_context.node else "UnknownAgent"
    tool_name = "calculate_analytics"
    
    apps_resp = get_applications(tool_context)
    if apps_resp.get("status") == "error":
        audit_log(agent_name, tool_name, "FAILURE", "Failed to get applications.")
        return apps_resp
        
    data = apps_resp.get("data", [])
    total = len(data)
    interview_count = sum(1 for row in data if row.get("status") == "Interview")
    offer_count = sum(1 for row in data if row.get("status") == "Offer")
    rejection_count = sum(1 for row in data if row.get("status") == "Rejected")
    
    responded = interview_count + offer_count + rejection_count
    response_rate = (responded / total * 100) if total > 0 else 0.0
    
    metrics = {
        "total_applications": total,
        "interview_count": interview_count,
        "offer_count": offer_count,
        "rejection_count": rejection_count,
        "response_rate": round(response_rate, 2)
    }
    
    audit_log(agent_name, tool_name, "SUCCESS", f"Calculated analytics on {total} apps.")
    return {"status": "success", "data": metrics}

def find_stale_applications(days: int, tool_context: ToolContext) -> dict:
    """Finds applications that are stale (status is 'Applied' and older than the given number of days).
    
    Args:
        days: The number of days after which an application is considered stale.
    Returns:
        A dict containing the list of stale applications.
    """
    agent_name = tool_context.node.name if tool_context and tool_context.node else "UnknownAgent"
    tool_name = "find_stale_applications"
    
    apps_resp = get_applications(tool_context)
    if apps_resp.get("status") == "error":
        audit_log(agent_name, tool_name, "FAILURE", "Failed to get applications.")
        return apps_resp
        
    now = datetime.datetime.now()
    stale_apps = []
    for row in apps_resp.get("data", []):
        if row.get("status") == "Applied" and row.get("date_applied"):
            date_app = datetime.datetime.strptime(row["date_applied"], "%Y-%m-%d")
            if (now - date_app).days > days:
                stale_apps.append(row)
                
    audit_log(agent_name, tool_name, "SUCCESS", f"Found {len(stale_apps)} stale applications.")
    return {"status": "success", "data": stale_apps}

def update_status(id: int, company: str, role: str, status: str, date_applied: str, tool_context: ToolContext) -> dict:
    """Updates an existing application by ID.
    
    Args:
        id: The Record ID to update.
        company: The company name (optional, only if updating).
        role: The role (optional, only if updating).
        status: The new status (optional, only if updating).
        date_applied: The date applied (optional, only if updating).
    """
    agent_name = tool_context.node.name if tool_context and tool_context.node else "UnknownAgent"
    tool_name = "update_status"
    
    try:
        if not os.path.exists(CSV_FILE):
            return {"status": "error", "message": "No records found."}
            
        data = []
        updated = False
        updated_row = None
        
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row["id"]) == str(id):
                    if company: row["company"] = company
                    if role: row["role"] = role
                    if status: row["status"] = status
                    if date_applied: row["date_applied"] = date_applied
                    row["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updated_row = row
                    updated = True
                data.append(row)
                
        if not updated:
            return {"status": "error", "message": f"Record #{id} not found."}
            
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(data)
            
        audit_log(agent_name, tool_name, "SUCCESS", f"Updated record #{id}.")
        return {"status": "success", "message": "Record updated.", "record": updated_row}
    except Exception as e:
        error_msg = f"Failed to update CSV: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}
