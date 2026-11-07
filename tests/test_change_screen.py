import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from tools.change_screen.tool import change_screen


class ChangeScreenTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.requests = []
        self.status = 202
        self.reply = {"screen_id": 1, "status": "accepted"}
        case = self

        class Receiver(BaseHTTPRequestHandler):
            def do_PUT(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                case.requests.append((self.path, self.headers.get("Authorization"), body))
                self.send_response(case.status)
                self.end_headers()
                self.wfile.write(json.dumps(case.reply).encode())

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        self.enterContext(patch.dict(os.environ, {"RELAY_DISPLAY_URL": f"http://127.0.0.1:{server.server_port}",
                                                  "RELAY_DISPLAY_TOKEN": "fixture-key"}))

    async def test_forward_literal_text_and_report_only_acknowledged_state(self):
        text = '<b>Hello</b>\nCafé & tea.'
        result = await change_screen(1, "dashboard", text)
        self.assertEqual(self.requests, [("/v1/screens/1/state", "Bearer fixture-key",
                                         {"template": "dashboard", "text": text})])
        self.assertEqual(result, {"screen_id": 1, "template": "dashboard", "status": "accepted"})

    async def test_rejection_and_wrong_screen_are_not_success(self):
        self.status = 404
        with self.assertRaisesRegex(ValueError, "recognize screen"):
            await change_screen(1, "dashboard")
        self.status = 200
        self.reply = {"screen_id": 2, "status": "accepted"}
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            await change_screen(1, "dashboard")

    async def test_template_only_and_comparison_prompt(self):
        await change_screen(1, "google_calendar_view")
        prompt = "I want to compare a 3060 Ti vs a 4060 Ti"
        await change_screen(1, "comparison", prompt)
        self.assertEqual([body for _, _, body in self.requests], [
            {"template": "google_calendar_view", "text": ""},
            {"template": "comparison", "text": prompt},
        ])

    async def test_offline_is_an_error_and_is_not_retried(self):
        self.status = 409
        with self.assertRaisesRegex(ValueError, "offline"):
            await change_screen(1, "dashboard")
        self.assertEqual(len(self.requests), 1)

    async def test_queued_ack_is_rejected(self):
        self.reply = {"screen_id": 1, "status": "queued"}
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            await change_screen(1, "dashboard")
