import datetime
from google.adk.tools import ToolContext
from .security import validate_application, audit_log

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
    agent_name = tool_context.node.name if tool_context and getattr(tool_context, "node", None) else "UnknownAgent"
    tool_name = "add_application"
    
    error = validate_application(company, role, status, date_applied)
    if error:
        audit_log(agent_name, tool_name, "FAILURE", error)
        return {"status": "error", "message": error}
        
    try:
        apps = list(tool_context.state.get("applications", [])) if (tool_context and hasattr(tool_context, "state")) else []
        row_id = max((int(app.get("id", 0)) for app in apps), default=0) + 1
        
        new_record = {
            "id": row_id,
            "company": company,
            "role": role,
            "status": status,
            "date_applied": date_applied,
            "last_updated": ""
        }
        
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["applications"] = apps + [new_record]
            
        success_msg = f"Logged application: {company} - {role}"
        audit_log(agent_name, tool_name, "SUCCESS")
        return {"status": "success", "record_id": row_id, "message": success_msg}
    except Exception as e:
        error_msg = f"Failed to log application: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}

def get_applications(tool_context: ToolContext) -> dict:
    """Retrieves all job applications from the database.
    
    Returns:
        A dict containing a list of application records.
    """
    agent_name = tool_context.node.name if tool_context and getattr(tool_context, "node", None) else "UnknownAgent"
    tool_name = "get_applications"
    
    try:
        apps = list(tool_context.state.get("applications", [])) if (tool_context and hasattr(tool_context, "state")) else []
        audit_log(agent_name, tool_name, "SUCCESS")
        return {"status": "success", "data": apps}
    except Exception as e:
        error_msg = f"Failed to retrieve applications: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}

def calculate_analytics(tool_context: ToolContext) -> dict:
    """Calculates analytics for job applications (counts and response rate).
    
    Returns:
        A dict containing the calculated metrics.
    """
    agent_name = tool_context.node.name if tool_context and getattr(tool_context, "node", None) else "UnknownAgent"
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
    
    audit_log(agent_name, tool_name, "SUCCESS")
    return {"status": "success", "data": metrics}

def find_stale_applications(days: int, tool_context: ToolContext) -> dict:
    """Finds applications that are stale (status is 'Applied' and older than the given number of days).
    
    Args:
        days: The number of days after which an application is considered stale.
    Returns:
        A dict containing the list of stale applications.
    """
    agent_name = tool_context.node.name if tool_context and getattr(tool_context, "node", None) else "UnknownAgent"
    tool_name = "find_stale_applications"
    
    apps_resp = get_applications(tool_context)
    if apps_resp.get("status") == "error":
        audit_log(agent_name, tool_name, "FAILURE", "Failed to get applications.")
        return apps_resp
        
    now = datetime.datetime.now()
    stale_apps = []
    for row in apps_resp.get("data", []):
        if row.get("status") == "Applied" and row.get("date_applied"):
            try:
                date_app = datetime.datetime.strptime(row["date_applied"], "%Y-%m-%d")
                if (now - date_app).days > days:
                    stale_apps.append(row)
            except ValueError:
                continue
                
    audit_log(agent_name, tool_name, "SUCCESS")
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
    agent_name = tool_context.node.name if tool_context and getattr(tool_context, "node", None) else "UnknownAgent"
    tool_name = "update_status"
    
    try:
        apps = list(tool_context.state.get("applications", [])) if (tool_context and hasattr(tool_context, "state")) else []
        if not apps:
            return {"status": "error", "message": "No records found."}
            
        data = []
        updated = False
        updated_row = None
        
        for row in apps:
            row_copy = dict(row)
            if str(row_copy.get("id")) == str(id):
                if company: row_copy["company"] = company
                if role: row_copy["role"] = role
                if status: row_copy["status"] = status
                if date_applied: row_copy["date_applied"] = date_applied
                row_copy["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_row = row_copy
                updated = True
            data.append(row_copy)
            
        if not updated:
            return {"status": "error", "message": f"Record #{id} not found."}
            
        if tool_context and hasattr(tool_context, "state"):
            tool_context.state["applications"] = data
            
        audit_log(agent_name, tool_name, "SUCCESS")
        return {"status": "success", "message": "Record updated.", "record": updated_row}
    except Exception as e:
        error_msg = f"Failed to update application: {str(e)}"
        audit_log(agent_name, tool_name, "FAILURE", error_msg)
        return {"status": "error", "message": error_msg}

