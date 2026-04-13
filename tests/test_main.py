import importlib.util
import json
import os
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = REPO_ROOT / "main.py"


def load_main_module():
    if not MAIN_PATH.exists():
        raise AssertionError(f"Expected Lambda entrypoint at {MAIN_PATH}")

    spec = importlib.util.spec_from_file_location("til_lambda_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PayloadTests(unittest.TestCase):
    def test_build_slack_payload_contains_scrum_template(self):
        module = load_main_module()
        payload_builder = getattr(module, "build_slack_payload", None)

        self.assertIsNotNone(payload_builder, "build_slack_payload() should exist")

        payload = payload_builder()

        self.assertEqual(payload["blocks"][0]["type"], "header")
        self.assertEqual(payload["blocks"][0]["text"]["text"], "데일리 스크럼")
        self.assertIn("데일리 스크럼 양식", payload["blocks"][3]["text"]["text"])
        self.assertIn("어제 한 일", payload["blocks"][3]["text"]["text"])
        self.assertIn("오늘 할 일", payload["blocks"][3]["text"]["text"])
        self.assertIn("매일 오전 10시 10분 자동 발송", payload["blocks"][5]["elements"][0]["text"])


class HandlerTests(unittest.TestCase):
    def test_lambda_handler_posts_to_slack_and_returns_success(self):
        module = load_main_module()

        recorded = {}

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(request, timeout=0):
            recorded["url"] = request.full_url
            recorded["headers"] = dict(request.header_items())
            recorded["body"] = request.data.decode("utf-8")
            recorded["timeout"] = timeout
            return FakeResponse()

        original_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        original_urlopen = module.urllib_request.urlopen
        os.environ["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/T000/B000/XXXX"
        module.urllib_request.urlopen = fake_urlopen

        try:
            result = module.lambda_handler({}, None)
        finally:
            module.urllib_request.urlopen = original_urlopen
            if original_webhook is None:
                os.environ.pop("SLACK_WEBHOOK_URL", None)
            else:
                os.environ["SLACK_WEBHOOK_URL"] = original_webhook

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Daily scrum reminder sent"}))
        self.assertEqual(recorded["url"], "https://hooks.slack.com/services/T000/B000/XXXX")
        self.assertEqual(recorded["timeout"], 5)
        self.assertIn("application/json", recorded["headers"].get("Content-type", ""))
        self.assertIn("데일리 스크럼", recorded["body"])


if __name__ == "__main__":
    unittest.main()
