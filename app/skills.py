from google.adk.tools import ToolContext
from .tools import get_applications, calculate_analytics, find_stale_applications

def analyze_job_search(tool_context: ToolContext) -> dict:
    """Analyzes the overall job search progress.
    
    Returns:
        A dict containing a structured summary with total applications, interviews, offers, rejections, response rate, stale applications count, and a short recommendation summary.
    """
    analytics_resp = calculate_analytics(tool_context)
    stale_resp = find_stale_applications(14, tool_context)
    
    metrics = analytics_resp.get("data", {}) if analytics_resp.get("status") == "success" else {}
    stale_apps = stale_resp.get("data", []) if stale_resp.get("status") == "success" else []
    
    total = metrics.get("total_applications", 0)
    response_rate = metrics.get("response_rate", 0.0)
    stale_count = len(stale_apps)
    
    if total == 0:
        recommendation = "You haven't logged any applications yet. Start applying!"
    elif response_rate == 0.0 and stale_count > 0:
        recommendation = f"You have {stale_count} stale applications. You should follow up to get some responses."
    elif response_rate > 20.0:
        recommendation = "Your response rate is great! Keep doing what you're doing."
    else:
        recommendation = "Keep applying and following up to improve your response rate."
        
    summary = {
        "total_applications": total,
        "interviews": metrics.get("interview_count", 0),
        "offers": metrics.get("offer_count", 0),
        "rejections": metrics.get("rejection_count", 0),
        "response_rate": response_rate,
        "stale_applications_count": stale_count,
        "recommendation_summary": recommendation
    }
    
    return {"status": "success", "data": summary}
