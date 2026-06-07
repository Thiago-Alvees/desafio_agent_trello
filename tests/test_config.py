from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from trello_agent.config import GoogleSettings, load_chat_settings


class ChatConfigTests(unittest.TestCase):
    def test_loads_google_settings(self) -> None:
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "google-key"}, clear=True):
            settings = load_chat_settings(required=True)

        self.assertIsInstance(settings, GoogleSettings)
        self.assertEqual(settings.api_key, "google-key")

    def test_accepts_gemini_api_key_name(self) -> None:
        with patch.dict(
            os.environ,
            {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": "gemini-key"},
            clear=True,
        ):
            settings = load_chat_settings(required=True)

        self.assertIsInstance(settings, GoogleSettings)
        self.assertEqual(settings.api_key, "gemini-key")


if __name__ == "__main__":
    unittest.main()
