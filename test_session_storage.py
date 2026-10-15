import os
import unittest
import datetime
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools import ToolContext
from google.adk.events.event_actions import EventActions
from google.adk.events.event import Event

from app.tools import (
    add_application,
    get_applications,
    update_status,
    calculate_analytics,
    find_stale_applications,
)
from app.skills import analyze_job_search
from app.security import AUDIT_LOG_FILE


class TestSessionStorage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_service = InMemorySessionService()
        if os.path.exists("applications.csv"):
            os.remove("applications.csv")

    async def _create_context(self, user_id: str, session_id: str = None):
        session = await self.session_service.create_session(
            app_name="job-search-concierge",
            user_id=user_id,
            session_id=session_id
        )
        actions = EventActions()
        ctx = ToolContext(
            InvocationContext(
                session=session,
                session_service=self.session_service,
                invocation_id=f"inv_{session.id}"
            ),
            event_actions=actions
        )
        return session, ctx, actions

    async def _commit_context(self, session, actions):
        event = Event(author="tool", actions=actions)
        await self.session_service.append_event(session, event)

    async def _resume_context(self, user_id: str, session_id: str):
        session = await self.session_service.get_session(
            app_name="job-search-concierge",
            user_id=user_id,
            session_id=session_id
        )
        actions = EventActions()
        ctx = ToolContext(
            InvocationContext(
                session=session,
                session_service=self.session_service,
                invocation_id=f"inv_next_{session.id}"
            ),
            event_actions=actions
        )
        return session, ctx, actions

    async def test_empty_session_behavior(self):
        """Verify behavior on an empty session."""
        _, ctx, _ = await self._create_context(user_id="user_empty")

        # get_applications
        apps_resp = get_applications(ctx)
        self.assertEqual(apps_resp["status"], "success")
        self.assertEqual(apps_resp["data"], [])

        # calculate_analytics
        analytics_resp = calculate_analytics(ctx)
        self.assertEqual(analytics_resp["status"], "success")
        metrics = analytics_resp["data"]
        self.assertEqual(metrics["total_applications"], 0)
        self.assertEqual(metrics["interview_count"], 0)
        self.assertEqual(metrics["offer_count"], 0)
        self.assertEqual(metrics["rejection_count"], 0)
        self.assertEqual(metrics["response_rate"], 0.0)

        # find_stale_applications
        stale_resp = find_stale_applications(14, ctx)
        self.assertEqual(stale_resp["status"], "success")
        self.assertEqual(stale_resp["data"], [])

        # update_status on empty session
        update_resp = update_status(1, "Google", "SWE", "Interview", "", ctx)
        self.assertEqual(update_resp["status"], "error")
        self.assertEqual(update_resp["message"], "No records found.")

        # skills.analyze_job_search
        skill_resp = analyze_job_search(ctx)
        self.assertEqual(skill_resp["status"], "success")
        self.assertEqual(skill_resp["data"]["total_applications"], 0)

        # Verify applications.csv was never created
        self.assertFalse(os.path.exists("applications.csv"))

    async def test_all_five_operations(self):
        """Verify add, get, update, analytics, and find_stale operations."""
        session, ctx, actions = await self._create_context(user_id="user_ops")

        # 1. Add applications
        res1 = add_application("Google", "Backend Engineer", "Applied", "2026-01-01", ctx)
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["record_id"], 1)

        res2 = add_application("Microsoft", "Frontend Engineer", "Interview", "2026-02-01", ctx)
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["record_id"], 2)

        res3 = add_application("Meta", "ML Engineer", "Offer", "2026-03-01", ctx)
        self.assertEqual(res3["status"], "success")
        self.assertEqual(res3["record_id"], 3)

        res4 = add_application("Apple", "iOS Dev", "Rejected", "2026-04-01", ctx)
        self.assertEqual(res4["status"], "success")
        self.assertEqual(res4["record_id"], 4)

        # Commit state to session service
        await self._commit_context(session, actions)

        # 2. Get applications in a resumed context turn
        session, ctx2, actions2 = await self._resume_context("user_ops", session.id)
        get_res = get_applications(ctx2)
        self.assertEqual(get_res["status"], "success")
        self.assertEqual(len(get_res["data"]), 4)
        self.assertEqual(get_res["data"][0]["company"], "Google")
        self.assertEqual(get_res["data"][1]["company"], "Microsoft")

        # 3. Update status
        up_res = update_status(1, "", "", "Interview", "", ctx2)
        self.assertEqual(up_res["status"], "success")
        self.assertEqual(up_res["record"]["status"], "Interview")
        self.assertEqual(up_res["record"]["company"], "Google") # untouched
        self.assertTrue(up_res["record"]["last_updated"] != "")
        await self._commit_context(session, actions2)

        # 4. Calculate analytics
        session, ctx3, _ = await self._resume_context("user_ops", session.id)
        analytics_res = calculate_analytics(ctx3)
        self.assertEqual(analytics_res["status"], "success")
        metrics = analytics_res["data"]
        self.assertEqual(metrics["total_applications"], 4)
        # Record 1 updated to Interview, Record 2 is Interview, Record 3 is Offer, Record 4 is Rejected
        self.assertEqual(metrics["interview_count"], 2)
        self.assertEqual(metrics["offer_count"], 1)
        self.assertEqual(metrics["rejection_count"], 1)
        self.assertEqual(metrics["response_rate"], 100.0)

        # 5. Find stale applications (Google is now Interview, let's add an old Applied one)
        _, ctx_stale, actions_stale = await self._resume_context("user_ops", session.id)
        add_application("OldCorp", "Legacy Dev", "Applied", "2020-01-01", ctx_stale)
        await self._commit_context(session, actions_stale)

        _, ctx_stale_check, _ = await self._resume_context("user_ops", session.id)
        stale_res = find_stale_applications(30, ctx_stale_check)
        self.assertEqual(stale_res["status"], "success")
        stale_companies = [r["company"] for r in stale_res["data"]]
        self.assertIn("OldCorp", stale_companies)
        self.assertNotIn("Google", stale_companies) # Google is Interview

        # Verify applications.csv was never created
        self.assertFalse(os.path.exists("applications.csv"))

    async def test_session_isolation(self):
        """Requirement 14: Confirm user A's records are completely invisible to user B."""
        # Create two sessions against the SAME session service
        sess_a, ctx_a, actions_a = await self._create_context(user_id="user_a", session_id="sess_a_123")
        sess_b, ctx_b, actions_b = await self._create_context(user_id="user_b", session_id="sess_b_456")

        # User A adds applications
        res_a1 = add_application("SecretCorp A", "Staff Eng", "Applied", "2026-05-01", ctx_a)
        self.assertEqual(res_a1["status"], "success")
        await self._commit_context(sess_a, actions_a)

        # User B queries applications
        apps_b = get_applications(ctx_b)
        self.assertEqual(apps_b["status"], "success")
        self.assertEqual(apps_b["data"], [], "User B must not see User A's applications!")

        # User B adds their own application
        res_b1 = add_application("PublicCorp B", "Junior Dev", "Applied", "2026-05-02", ctx_b)
        self.assertEqual(res_b1["status"], "success")
        await self._commit_context(sess_b, actions_b)

        # Resumed session queries
        _, ctx_a_res, _ = await self._resume_context("user_a", sess_a.id)
        _, ctx_b_res, _ = await self._resume_context("user_b", sess_b.id)

        apps_a_final = get_applications(ctx_a_res)["data"]
        apps_b_final = get_applications(ctx_b_res)["data"]

        self.assertEqual(len(apps_a_final), 1)
        self.assertEqual(apps_a_final[0]["company"], "SecretCorp A")

        self.assertEqual(len(apps_b_final), 1)
        self.assertEqual(apps_b_final[0]["company"], "PublicCorp B")

        # Verify User B cannot update User A's record
        up_attempt = update_status(1, "HackedCorp", "", "Offer", "", ctx_b_res)
        # ID 1 in User B's session corresponds to PublicCorp B, not SecretCorp A
        self.assertEqual(up_attempt["record"]["company"], "HackedCorp")
        # Check User A's record was NOT modified
        apps_a_recheck = get_applications(ctx_a_res)["data"]
        self.assertEqual(apps_a_recheck[0]["company"], "SecretCorp A")

        # Verify applications.csv was never created
        self.assertFalse(os.path.exists("applications.csv"))

    async def test_error_handling(self):
        """Verify error handling on invalid inputs."""
        session, ctx, _ = await self._create_context(user_id="user_err")

        # Invalid status
        res1 = add_application("Acme", "SWE", "InvalidStatus", "2026-01-01", ctx)
        self.assertEqual(res1["status"], "error")
        self.assertIn("Status must be one of", res1["message"])

        # Invalid date format
        res2 = add_application("Acme", "SWE", "Applied", "01/01/2026", ctx)
        self.assertEqual(res2["status"], "error")
        self.assertIn("Date must be a valid YYYY-MM-DD string", res2["message"])

        # Record not found when updating
        # First add one record so list is not empty
        add_application("Acme", "SWE", "Applied", "2026-01-01", ctx)
        res3 = update_status(999, "Acme", "SWE", "Interview", "", ctx)
        self.assertEqual(res3["status"], "error")
        self.assertIn("Record #999 not found.", res3["message"])

        # Verify applications.csv was never created
        self.assertFalse(os.path.exists("applications.csv"))

    async def test_audit_log_privacy(self):
        """Requirement 13: audit.log must never log company or role names."""
        # Record file size or clear
        initial_size = os.path.getsize(AUDIT_LOG_FILE) if os.path.exists(AUDIT_LOG_FILE) else 0

        _, ctx, _ = await self._create_context(user_id="user_audit")
        secret_company = "TopSecretQuantumAI_XYZ789"
        secret_role = "PrincipalHyperdriveEngineer_ABC123"

        add_application(secret_company, secret_role, "Applied", "2026-06-01", ctx)
        update_status(1, secret_company, secret_role, "Interview", "", ctx)
        get_applications(ctx)
        calculate_analytics(ctx)
        find_stale_applications(10, ctx)

        with open(AUDIT_LOG_FILE, "r") as f:
            f.seek(initial_size)
            new_logs = f.read()

        self.assertNotIn(secret_company, new_logs, "Company name leaked into shared audit.log!")
        self.assertNotIn(secret_role, new_logs, "Role name leaked into shared audit.log!")

        # Verify each newly written log line format: timestamp | agent | tool | status
        for line in new_logs.strip().splitlines():
            parts = [p.strip() for p in line.split("|")]
            self.assertEqual(len(parts), 4, f"Audit log line must have exactly 4 parts: {line}")
            self.assertIn(parts[3], ["SUCCESS", "FAILURE"])


if __name__ == "__main__":
    unittest.main()
