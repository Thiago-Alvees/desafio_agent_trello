from __future__ import annotations

import unicodedata
from typing import Any

from trello_agent.client import TrelloClient
from trello_agent.exceptions import AmbiguousMatchError, CommandError, NotFoundError


class TrelloService:
    def __init__(self, client: TrelloClient) -> None:
        # O service fica entre o cliente HTTP e as tools.
        # Ele resolve nomes amigaveis, aplica validacoes e devolve dados
        # prontos para o restante da aplicacao usar.
        self.client = client

    def list_boards(self) -> list[dict[str, Any]]:
        return self.client.list_boards()

    def list_lists(self, board_query: str) -> dict[str, Any]:
        board = self.resolve_board(board_query)
        lists_ = self.client.list_lists(board["id"])
        return {"board": board, "lists": lists_}

    def list_cards(self, board_query: str, list_query: str | None = None) -> dict[str, Any]:
        board = self.resolve_board(board_query)

        if list_query:
            list_ = self.resolve_list(board["id"], list_query)
            cards = self.client.list_list_cards(list_["id"])
            return {"board": board, "list": list_, "cards": cards}

        cards = self.client.list_board_cards(board["id"])
        return {"board": board, "cards": cards}

    def create_card(self, board_query: str, list_query: str, title: str, description: str = "") -> dict[str, Any]:
        board = self.resolve_board(board_query)
        list_ = self.resolve_list(board["id"], list_query)
        card = self.client.create_card(list_["id"], title=title, description=description)
        return {"board": board, "list": list_, "card": card}

    def move_card(self, board_query: str, card_query: str, target_list_query: str) -> dict[str, Any]:
        board = self.resolve_board(board_query)
        card = self.resolve_card(board["id"], card_query)
        target_list = self.resolve_list(board["id"], target_list_query)
        updated_card = self.client.move_card(card["id"], target_list["id"])
        return {"board": board, "card": card, "target_list": target_list, "updated_card": updated_card}

    def comment_card(self, board_query: str, card_query: str, text: str) -> dict[str, Any]:
        board = self.resolve_board(board_query)
        card = self.resolve_card(board["id"], card_query)
        comment = self.client.add_comment(card["id"], text)
        return {"board": board, "card": card, "comment": comment}

    def resolve_board(self, board_query: str) -> dict[str, Any]:
        return self._match_item(self.client.list_boards(), board_query, "board")

    def resolve_list(self, board_id: str, list_query: str) -> dict[str, Any]:
        return self._match_item(self.client.list_lists(board_id), list_query, "lista")

    def resolve_card(self, board_id: str, card_query: str) -> dict[str, Any]:
        return self._match_item(self.client.list_board_cards(board_id), card_query, "card")

    def _match_item(
        self, items: list[dict[str, Any]], query: str, entity_name: str
    ) -> dict[str, Any]:
        # Esta funcao implementa a busca "inteligente" por nome:
        # 1. tenta id ou nome exato
        # 2. depois prefixo
        # 3. por fim qualquer trecho do nome
        # Isso deixa o chat e o CLI mais tolerantes para quem esta digitando.
        if not items:
            raise NotFoundError(f"Nenhum {entity_name} disponivel para busca.")

        normalized_query = self._normalize(query)
        if not normalized_query:
            raise CommandError(f"Informe o nome do {entity_name}.")

        exact_matches = [
            item
            for item in items
            if normalized_query
            in {
                self._normalize(item.get("id", "")),
                self._normalize(item.get("name", "")),
            }
        ]
        if len(exact_matches) == 1:
            return exact_matches[0]
        if len(exact_matches) > 1:
            raise AmbiguousMatchError(self._ambiguous_message(entity_name, query, exact_matches))

        startswith_matches = [
            item for item in items if self._normalize(item.get("name", "")).startswith(normalized_query)
        ]
        if len(startswith_matches) == 1:
            return startswith_matches[0]
        if len(startswith_matches) > 1:
            raise AmbiguousMatchError(self._ambiguous_message(entity_name, query, startswith_matches))

        contains_matches = [
            item for item in items if normalized_query in self._normalize(item.get("name", ""))
        ]
        if len(contains_matches) == 1:
            return contains_matches[0]
        if len(contains_matches) > 1:
            raise AmbiguousMatchError(self._ambiguous_message(entity_name, query, contains_matches))

        available = ", ".join(item.get("name", "<sem nome>") for item in items[:5])
        suffix = f" Disponiveis: {available}" if available else ""
        raise NotFoundError(f'Nenhum {entity_name} encontrado para "{query}".{suffix}')

    def _ambiguous_message(
        self, entity_name: str, query: str, matches: list[dict[str, Any]]
    ) -> str:
        names = ", ".join(item.get("name", "<sem nome>") for item in matches[:5])
        return f'A busca por {entity_name} "{query}" retornou multiplos resultados: {names}'

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold().strip())
        return "".join(char for char in decomposed if not unicodedata.combining(char))
