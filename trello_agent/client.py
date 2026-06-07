from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request

from trello_agent.config import TrelloSettings
from trello_agent.exceptions import TrelloAPIError


class TrelloClient:
    def __init__(self, settings: TrelloSettings) -> None:
        self.settings = settings

    def list_boards(self) -> list[dict[str, Any]]:
        boards = self._request(
            "GET",
            "/members/me/boards",
            query={"fields": "id,name,url,closed", "filter": "open"},
        )
        return self._sorted_by_name(boards)

    def list_lists(self, board_id: str) -> list[dict[str, Any]]:
        lists_ = self._request(
            "GET",
            f"/boards/{board_id}/lists",
            query={"fields": "id,name,closed", "filter": "open"},
        )
        return self._sorted_by_name(lists_)

    def list_board_cards(self, board_id: str) -> list[dict[str, Any]]:
        cards = self._request(
            "GET",
            f"/boards/{board_id}/cards",
            query={"fields": "id,name,desc,shortUrl,idList,dateLastActivity,closed"},
        )
        return self._sorted_by_name(cards)

    def list_list_cards(self, list_id: str) -> list[dict[str, Any]]:
        cards = self._request(
            "GET",
            f"/lists/{list_id}/cards",
            query={"fields": "id,name,desc,shortUrl,idList,dateLastActivity,closed"},
        )
        return self._sorted_by_name(cards)

    def create_card(self, list_id: str, title: str, description: str = "") -> dict[str, Any]:
        return self._request(
            "POST",
            "/cards",
            body={"idList": list_id, "name": title, "desc": description},
        )

    def move_card(self, card_id: str, target_list_id: str) -> dict[str, Any]:
        return self._request("PUT", f"/cards/{card_id}", body={"idList": target_list_id})

    def add_comment(self, card_id: str, text: str) -> dict[str, Any]:
        return self._request("POST", f"/cards/{card_id}/actions/comments", body={"text": text})

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        query_params = {"key": self.settings.api_key, "token": self.settings.token}
        if query:
            query_params.update({key: value for key, value in query.items() if value is not None})

        url = f"{self.settings.api_base_url}{path}?{parse.urlencode(query_params, doseq=True)}"
        data = None

        if body:
            encoded_body = {
                key: value
                for key, value in body.items()
                if value is not None and value != ""
            }
            data = parse.urlencode(encoded_body, doseq=True).encode("utf-8")

        http_request = request.Request(
            url=url,
            data=data,
            method=method.upper(),
            headers={"Accept": "application/json"},
        )

        try:
            with request.urlopen(http_request, timeout=self.settings.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise TrelloAPIError(
                f"Falha na API do Trello ({exc.code} {exc.reason}). Detalhe: {detail}"
            ) from exc
        except error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise TrelloAPIError(f"Não foi possível conectar ao Trello: {reason}") from exc

        if not payload:
            return {}

        return json.loads(payload)

    @staticmethod
    def _sorted_by_name(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(items, key=lambda item: item.get("name", "").casefold())
