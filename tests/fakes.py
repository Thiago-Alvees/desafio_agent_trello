from __future__ import annotations


class FakeTrelloClient:
    def __init__(self) -> None:
        self.created_cards: list[dict[str, str]] = []
        self.moved_cards: list[dict[str, str]] = []
        self.comments: list[dict[str, str]] = []

    def list_boards(self) -> list[dict[str, str]]:
        return [
            {"id": "board-1", "name": "Projeto Principal"},
            {"id": "board-2", "name": "Operacoes"},
        ]

    def list_lists(self, board_id: str) -> list[dict[str, str]]:
        data = {
            "board-1": [
                {"id": "list-1", "name": "A Fazer"},
                {"id": "list-2", "name": "Em Andamento"},
            ],
            "board-2": [{"id": "list-3", "name": "Backlog"}],
        }
        return data[board_id]

    def list_board_cards(self, board_id: str) -> list[dict[str, str]]:
        data = {
            "board-1": [
                {"id": "card-1", "name": "Corrigir login"},
                {"id": "card-2", "name": "Publicar release"},
            ],
            "board-2": [{"id": "card-3", "name": "Revisar SLA"}],
        }
        return data[board_id]

    def list_list_cards(self, list_id: str) -> list[dict[str, str]]:
        data = {
            "list-1": [{"id": "card-1", "name": "Corrigir login"}],
            "list-2": [{"id": "card-2", "name": "Publicar release"}],
            "list-3": [{"id": "card-3", "name": "Revisar SLA"}],
        }
        return data[list_id]

    def create_card(self, list_id: str, title: str, description: str = "") -> dict[str, str]:
        payload = {
            "id": "new-card",
            "idList": list_id,
            "name": title,
            "desc": description,
            "shortUrl": "https://trello.test/card/new-card",
        }
        self.created_cards.append(payload)
        return payload

    def move_card(self, card_id: str, target_list_id: str) -> dict[str, str]:
        payload = {"id": card_id, "idList": target_list_id}
        self.moved_cards.append(payload)
        return payload

    def add_comment(self, card_id: str, text: str) -> dict[str, str]:
        payload = {"id": card_id, "text": text}
        self.comments.append(payload)
        return payload
