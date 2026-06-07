from __future__ import annotations

import unittest

from trello_agent.chat import TrelloChatSession
from trello_agent.config import GoogleSettings
from trello_agent.service import TrelloService
from trello_agent.tools import TrelloToolRegistry

from tests.fakes import FakeTrelloClient


class FakeGateway:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.reset_calls = 0

    def send_message(self, user_message: str) -> str:
        self.messages.append(user_message)
        return f"eco: {user_message}"

    def reset(self) -> None:
        self.reset_calls += 1


class TrelloChatSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        service = TrelloService(FakeTrelloClient())
        tools = TrelloToolRegistry(service)
        settings = GoogleSettings(api_key="test-key", model="gemini-2.5-flash")
        self.gateway = FakeGateway()
        self.session = TrelloChatSession(settings, tools, gateway=self.gateway)

    def test_chat_session_delegates_to_gateway(self) -> None:
        reply = self.session.ask("Quais boards eu tenho?")

        self.assertEqual(reply, "eco: Quais boards eu tenho?")
        self.assertEqual(self.gateway.messages, ["Quais boards eu tenho?"])

    def test_reset_delegates_to_gateway(self) -> None:
        self.session.reset()

        self.assertEqual(self.gateway.reset_calls, 1)


if __name__ == "__main__":
    unittest.main()
