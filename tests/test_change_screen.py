import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from tools.change_screen.tool import ComparisonScreen, TextScreen, change_screen
from tools.set_screen_enabled.tool import set_screen_enabled


class ChangeScreenTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.requests = []
        self.status = 202
        self.reply = {"id": 1, "status": "accepted"}
        case = self

        class Receiver(BaseHTTPRequestHandler):
            def do_POST(self):
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
        result = await change_screen(id=1, screen=TextScreen(type="text", content=text))
        self.assertEqual(self.requests, [("/v1/screens/send", "Bearer fixture-key",
                                         {"id": 1, "screen": {"type": "text", "content": text}})])
        self.assertEqual(result, {"id": 1, "status": "accepted"})

    async def test_rejection_and_wrong_screen_are_not_success(self):
        self.status = 404
        with self.assertRaisesRegex(ValueError, "recognize screen"):
            await change_screen(1, TextScreen(type="text", content="dashboard"))
        self.status = 200
        self.reply = {"id": 2, "status": "accepted"}
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            await change_screen(1, TextScreen(type="text", content="dashboard"))

    async def test_sleep_requires_confirmation_from_the_kiosk(self):
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            await set_screen_enabled(1, False)
        self.reply = {"id": 1, "status": "applied"}
        self.assertEqual(await set_screen_enabled(1, True), self.reply)
        self.assertEqual([request[2] for request in self.requests],
                         [{"id": 1, "enabled": False}, {"id": 1, "enabled": True}])

    async def test_comparison_payload(self):
        screen = ComparisonScreen(type="comparison", option1="English", option2="Spanish")
        await change_screen(1, screen)
        self.assertEqual(self.requests[0][2], {"id": 1, "screen": {
            "type": "comparison", "option1": "English", "option2": "Spanish"}})

    async def test_offline_is_an_error_and_is_not_retried(self):
        self.status = 409
        with self.assertRaisesRegex(ValueError, "offline"):
            await change_screen(1, TextScreen(type="text", content="dashboard"))
        self.assertEqual(len(self.requests), 1)

    async def test_queued_ack_is_rejected(self):
        self.reply = {"id": 1, "status": "queued"}
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            await change_screen(1, TextScreen(type="text", content="dashboard"))
