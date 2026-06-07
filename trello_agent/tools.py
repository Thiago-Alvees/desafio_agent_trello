from __future__ import annotations

from typing import Any, Callable

from trello_agent.exceptions import TrelloAgentError
from trello_agent.service import TrelloService


class TrelloToolRegistry:
    def __init__(self, service: TrelloService) -> None:
        # O registry concentra todas as "ferramentas" do projeto em um lugar.
        # Isso evita duplicar a mesma regra de negocio em cada provedor de LLM.
        self.service = service

    def definitions(self) -> list[dict[str, Any]]:
        # Estas definicoes seguem um formato JSON simples de nome, descricao
        # e parametros. Mantemos isso separado porque ele continua util como
        # documentacao das tools do projeto.
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_boards",
                    "description": "Lista os boards abertos do usuario no Trello.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_lists",
                    "description": "Lista as listas abertas de um board do Trello.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "board_name": {
                                "type": "string",
                                "description": "Nome ou id do board no Trello.",
                            }
                        },
                        "required": ["board_name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_cards",
                    "description": "Lista os cards de um board ou de uma lista especifica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "board_name": {
                                "type": "string",
                                "description": "Nome ou id do board no Trello.",
                            },
                            "list_name": {
                                "type": "string",
                                "description": "Nome ou id da lista no board.",
                            },
                        },
                        "required": ["board_name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_card",
                    "description": "Cria um novo card em uma lista do Trello.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "board_name": {
                                "type": "string",
                                "description": "Nome ou id do board no Trello.",
                            },
                            "list_name": {
                                "type": "string",
                                "description": "Nome ou id da lista onde o card sera criado.",
                            },
                            "title": {
                                "type": "string",
                                "description": "Titulo do card.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Descricao opcional do card.",
                            },
                        },
                        "required": ["board_name", "list_name", "title"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "move_card",
                    "description": "Move um card existente para outra lista do mesmo board.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "board_name": {
                                "type": "string",
                                "description": "Nome ou id do board onde o card esta.",
                            },
                            "card_name": {
                                "type": "string",
                                "description": "Nome ou id do card.",
                            },
                            "target_list_name": {
                                "type": "string",
                                "description": "Nome ou id da lista de destino.",
                            },
                        },
                        "required": ["board_name", "card_name", "target_list_name"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "comment_card",
                    "description": "Adiciona um comentario em um card do Trello.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "board_name": {
                                "type": "string",
                                "description": "Nome ou id do board onde o card esta.",
                            },
                            "card_name": {
                                "type": "string",
                                "description": "Nome ou id do card.",
                            },
                            "text": {
                                "type": "string",
                                "description": "Texto do comentario.",
                            },
                        },
                        "required": ["board_name", "card_name", "text"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def google_functions(self) -> list[Callable[..., dict[str, Any]]]:
        """
        O SDK oficial do Gemini consegue transformar funcoes Python em tools.

        Entao, para o Google, em vez de enviar JSON manualmente, basta expor
        funcoes normais com type hints e docstrings.
        """
        return [
            self.list_boards,
            self.list_lists,
            self.list_cards,
            self.create_card,
            self.move_card,
            self.comment_card,
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if name == "list_boards":
                return {"ok": True, "boards": self.service.list_boards()}
            if name == "list_lists":
                return {"ok": True, **self.service.list_lists(arguments["board_name"])}
            if name == "list_cards":
                return {
                    "ok": True,
                    **self.service.list_cards(
                        arguments["board_name"],
                        arguments.get("list_name"),
                    ),
                }
            if name == "create_card":
                return {
                    "ok": True,
                    **self.service.create_card(
                        arguments["board_name"],
                        arguments["list_name"],
                        arguments["title"],
                        arguments.get("description", ""),
                    ),
                }
            if name == "move_card":
                return {
                    "ok": True,
                    **self.service.move_card(
                        arguments["board_name"],
                        arguments["card_name"],
                        arguments["target_list_name"],
                    ),
                }
            if name == "comment_card":
                return {
                    "ok": True,
                    **self.service.comment_card(
                        arguments["board_name"],
                        arguments["card_name"],
                        arguments["text"],
                    ),
                }
        except TrelloAgentError as exc:
            return {"ok": False, "error": str(exc)}

        return {"ok": False, "error": f"Tool desconhecida: {name}"}

    def list_boards(self) -> dict[str, Any]:
        """Lista os boards abertos do usuario no Trello."""
        return self.execute("list_boards", {})

    def list_lists(self, board_name: str) -> dict[str, Any]:
        """
        Lista as listas abertas de um board.

        Args:
            board_name: Nome ou id do board no Trello.
        """
        return self.execute("list_lists", {"board_name": board_name})

    def list_cards(self, board_name: str, list_name: str | None = None) -> dict[str, Any]:
        """
        Lista os cards de um board ou de uma lista especifica.

        Args:
            board_name: Nome ou id do board no Trello.
            list_name: Nome ou id da lista. Se vazio, busca no board inteiro.
        """
        return self.execute(
            "list_cards",
            {"board_name": board_name, "list_name": list_name},
        )

    def create_card(self, board_name: str, list_name: str, title: str, description: str = "") -> dict[str, Any]:
        """
        Cria um card no Trello.

        Args:
            board_name: Nome ou id do board.
            list_name: Nome ou id da lista onde o card sera criado.
            title: Titulo do card.
            description: Descricao opcional do card.
        """
        return self.execute(
            "create_card",
            {
                "board_name": board_name,
                "list_name": list_name,
                "title": title,
                "description": description,
            },
        )

    def move_card(self, board_name: str, card_name: str, target_list_name: str) -> dict[str, Any]:
        """
        Move um card para outra lista do mesmo board.

        Args:
            board_name: Nome ou id do board.
            card_name: Nome ou id do card.
            target_list_name: Nome ou id da lista de destino.
        """
        return self.execute(
            "move_card",
            {
                "board_name": board_name,
                "card_name": card_name,
                "target_list_name": target_list_name,
            },
        )

    def comment_card(self, board_name: str, card_name: str, text: str) -> dict[str, Any]:
        """
        Adiciona um comentario em um card.

        Args:
            board_name: Nome ou id do board.
            card_name: Nome ou id do card.
            text: Conteudo do comentario.
        """
        return self.execute(
            "comment_card",
            {"board_name": board_name, "card_name": card_name, "text": text},
        )
