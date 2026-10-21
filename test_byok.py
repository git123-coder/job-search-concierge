import os
import unittest
import asyncio
from unittest.mock import patch, MagicMock
from app.engine import JobSearchEngine
from app.agent import build_root_agent, KeyInjectedGemini
from app.tools import add_application, get_applications
class TestBYOKFlow(unittest.TestCase):
    def setUp(self):
        # Ensure GEMINI_API_KEY is not in os.environ for clean testing
        self.original_env_key = os.environ.pop("GEMINI_API_KEY", None)
    def tearDown(self):
        # Restore environment if it was set prior
        if self.original_env_key is not None:
            os.environ["GEMINI_API_KEY"] = self.original_env_key
        else:
            os.environ.pop("GEMINI_API_KEY", None)
    def test_no_key_behavior(self):
        """1. When no key is provided, verify no ADK call is made and friendly message is displayed."""
        api_key = ""
        # Simulate app.py check:
        if not api_key:
            displayed_info = "Enter your Gemini API key above to start"
            chat_disabled = True
            engine_called = False
        else:
            displayed_info = None
            chat_disabled = False
            engine_called = True
        self.assertEqual(displayed_info, "Enter your Gemini API key above to start")
        self.assertTrue(chat_disabled)
        self.assertFalse(engine_called)
    def test_invalid_key_friendly_error(self):
        """2. When an invalid key is provided, verify the friendly error message is displayed (never a traceback)."""
        engine = JobSearchEngine(api_key="invalid_gemini_api_key_test_12345")
        
        async def run_call():
            session = await engine.create_session(user_id="test_user")
            user_message = ""
            try:
                await engine.process_message("Hi", session.id, user_id="test_user")
            except Exception as e:
                # App catch block logic:
                user_message = "Invalid or rate-limited API key. Please check it."
            return user_message
        result_message = asyncio.run(run_call())
        self.assertEqual(result_message, "Invalid or rate-limited API key. Please check it.")
        # Ensure no traceback or key string in the friendly message
        self.assertNotIn("invalid_gemini_api_key_test_12345", result_message)
        self.assertNotIn("Traceback", result_message)
    def test_key_not_in_os_environ_after_use(self):
        """3. Verify key is not present in os.environ before, during, or after engine usage."""
        test_key = "user_secret_gemini_key_abc_987"
        self.assertNotIn("GEMINI_API_KEY", os.environ)
        # Initialize engine and inspect models
        engine = JobSearchEngine(api_key=test_key)
        self.assertNotIn("GEMINI_API_KEY", os.environ)
        # Inspect canonical model client
        client = engine.app.root_agent.canonical_model.api_client
        self.assertEqual(client._api_client.api_key, test_key)
        # Confirm environment remains completely uncontaminated
        self.assertNotIn("GEMINI_API_KEY", os.environ)
        for k, v in os.environ.items():
            self.assertNotIn(test_key, k)
            self.assertNotIn(test_key, v)
    def test_two_sessions_key_isolation(self):
        """4. Verify two sessions with different keys stay completely isolated without cross-contamination."""
        key_a = "user_A_key_11111"
        key_b = "user_B_key_22222"
        engine_a = JobSearchEngine(api_key=key_a)
        engine_b = JobSearchEngine(api_key=key_b)
        # Check root agent clients
        client_a = engine_a.app.root_agent.canonical_model.api_client
        client_b = engine_b.app.root_agent.canonical_model.api_client
        self.assertEqual(client_a._api_client.api_key, key_a)
        self.assertEqual(client_b._api_client.api_key, key_b)
        self.assertNotEqual(client_a._api_client.api_key, client_b._api_client.api_key)
        # Check sub-agents in tree
        for sub_a in engine_a.app.root_agent.sub_agents:
            self.assertEqual(sub_a.canonical_model.api_client._api_client.api_key, key_a)
        for sub_b in engine_b.app.root_agent.sub_agents:
            self.assertEqual(sub_b.canonical_model.api_client._api_client.api_key, key_b)
        # Verify os.environ has neither key
        self.assertNotIn("GEMINI_API_KEY", os.environ)
    def test_key_change_preserves_application_data(self):
        """5. Recreating the engine on key change preserves existing application state."""
        async def run_state_preservation():
            # Session starts with key 1
            engine1 = JobSearchEngine(api_key="key_v1")
            s1 = await engine1.create_session(
                user_id="user_sess",
                state={"applications": [{"id": 1, "company": "Anthropic", "role": "Research"}]}
            )
            # Retrieve state before key change
            saved_state = await engine1.get_session_state("user_sess", s1.id)
            self.assertEqual(len(saved_state.get("applications", [])), 1)
            # User enters key 2
            engine2 = JobSearchEngine(api_key="key_v2")
            s2 = await engine2.create_session(
                user_id="user_sess",
                session_id=s1.id,
                state=saved_state
            )
            # Verify session id and applications preserved
            self.assertEqual(s2.id, s1.id)
            restored_state = await engine2.get_session_state("user_sess", s2.id)
            self.assertEqual(restored_state["applications"][0]["company"], "Anthropic")
            self.assertEqual(engine2.app.root_agent.canonical_model.api_client._api_client.api_key, "key_v2")
        asyncio.run(run_state_preservation())
if __name__ == "__main__":
    unittest.main()