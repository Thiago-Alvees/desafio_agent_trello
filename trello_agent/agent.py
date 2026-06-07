from __future__ import annotations

import argparse
import re
import shlex
import textwrap
import unicodedata
from typing import Callable

from trello_agent.exceptions import CommandError
from trello_agent.service import TrelloService


class _CommandParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CommandError(message)


class TrelloAgent:
    def __init__(self, service: TrelloService) -> None:
        # Este agente representa o modo CLI "deterministico":
        # o usuario escreve um comando e nos o transformamos em uma chamada
        # objetiva ao service, sem usar LLM.
        self.service = service
        self.parser = self._build_parser()
        # Estes regexes permitem aceitar frases em portugues alem dos comandos
        # formais. Ex.: "criar card ..." vira os mesmos argumentos de
        # "create-card --board ...".
        self.natural_patterns: list[tuple[re.Pattern[str], Callable[[re.Match[str]], list[str]]]] = [
            (
                re.compile(r"^(?:listar\s+)?(?:boards|quadros)$", re.IGNORECASE),
                lambda match: ["boards"],
            ),
            (
                re.compile(
                    r'^(?:listar\s+)?listas?\s+(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"$',
                    re.IGNORECASE,
                ),
                lambda match: ["lists", "--board", match.group("board")],
            ),
            (
                re.compile(
                    r'^(?:listar\s+)?cards?\s+(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"$',
                    re.IGNORECASE,
                ),
                lambda match: ["cards", "--board", match.group("board")],
            ),
            (
                re.compile(
                    r'^(?:listar\s+)?cards?\s+(?:do|da)\s+lista\s+"(?P<list>[^"]+)"\s+'
                    r'(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"$',
                    re.IGNORECASE,
                ),
                lambda match: [
                    "cards",
                    "--board",
                    match.group("board"),
                    "--list",
                    match.group("list"),
                ],
            ),
            (
                re.compile(
                    r'^criar\s+card\s+"(?P<title>[^"]+)"\s+na\s+lista\s+"(?P<list>[^"]+)"\s+'
                    r'(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"'
                    r'(?:\s+com\s+descricao\s+"(?P<desc>[^"]+)")?$',
                    re.IGNORECASE,
                ),
                self._translate_create_card,
            ),
            (
                re.compile(
                    r'^mover\s+card\s+"(?P<card>[^"]+)"\s+para\s+(?:a\s+)?lista\s+"(?P<list>[^"]+)"\s+'
                    r'(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"$',
                    re.IGNORECASE,
                ),
                lambda match: [
                    "move-card",
                    "--board",
                    match.group("board"),
                    "--card",
                    match.group("card"),
                    "--list",
                    match.group("list"),
                ],
            ),
            (
                re.compile(
                    r'^comentar\s+(?:no|em)\s+card\s+"(?P<card>[^"]+)"\s+'
                    r'(?:do|da|no|na)\s+(?:board|quadro)\s+"(?P<board>[^"]+)"\s+com\s+"(?P<text>[^"]+)"$',
                    re.IGNORECASE,
                ),
                lambda match: [
                    "comment-card",
                    "--board",
                    match.group("board"),
                    "--card",
                    match.group("card"),
                    "--text",
                    match.group("text"),
                ],
            ),
        ]

    def handle(self, raw_command: str | list[str]) -> str:
        parsed = self._parse(raw_command)

        if parsed.command == "help":
            return self.help_text()
        if parsed.command == "boards":
            return self._handle_boards()
        if parsed.command == "lists":
            return self._handle_lists(parsed.board)
        if parsed.command == "cards":
            return self._handle_cards(parsed.board, parsed.list_name)
        if parsed.command == "create-card":
            return self._handle_create_card(parsed.board, parsed.list_name, parsed.title, parsed.desc)
        if parsed.command == "move-card":
            return self._handle_move_card(parsed.board, parsed.card, parsed.list_name)
        if parsed.command == "comment-card":
            return self._handle_comment_card(parsed.board, parsed.card, parsed.text)
        if parsed.command == "exit":
            return ""

        raise CommandError(f"Comando não suportado: {parsed.command}")

    def should_exit(self, raw_command: str | list[str]) -> bool:
        normalized = self._normalize(" ".join(raw_command) if isinstance(raw_command, list) else raw_command)
        return normalized in {"sair", "exit", "quit"}

    def help_text(self) -> str:
        return textwrap.dedent(
            """
            Comandos disponíveis:
            - boards
            - lists --board "Nome do board"
            - cards --board "Nome do board" [--list "Nome da lista"]
            - create-card --board "Nome do board" --list "Nome da lista" --title "Título" [--desc "Descrição"]
            - move-card --board "Nome do board" --card "Nome do card" --list "Lista destino"
            - comment-card --board "Nome do board" --card "Nome do card" --text "Comentário"
            - ajuda
            - sair

            Também aceito frases como:
            - listar boards
            - listar listas do board "Projeto"
            - criar card "Corrigir login" na lista "A Fazer" do board "Projeto"
            """
        ).strip()

    def _parse(self, raw_command: str | list[str]) -> argparse.Namespace:
        if isinstance(raw_command, list):
            if not raw_command:
                raise CommandError("Digite um comando.")
            return self.parser.parse_args(raw_command)

        stripped = raw_command.strip()
        if not stripped:
            raise CommandError("Digite um comando.")

        translated = self._translate_natural_language(stripped)
        try:
            argv = translated if translated is not None else shlex.split(stripped)
        except ValueError as exc:
            raise CommandError(f"Não foi possível interpretar o comando: {exc}") from exc

        return self.parser.parse_args(argv)

    def _translate_natural_language(self, raw_command: str) -> list[str] | None:
        for pattern, translator in self.natural_patterns:
            match = pattern.match(raw_command)
            if match:
                return translator(match)
        return None

    def _translate_create_card(self, match: re.Match[str]) -> list[str]:
        args = [
            "create-card",
            "--board",
            match.group("board"),
            "--list",
            match.group("list"),
            "--title",
            match.group("title"),
        ]
        description = match.group("desc")
        if description:
            args.extend(["--desc", description])
        return args

    def _build_parser(self) -> _CommandParser:
        parser = _CommandParser(add_help=False)
        subparsers = parser.add_subparsers(dest="command", required=True)

        subparsers.add_parser("boards", add_help=False)
        subparsers.add_parser("ajuda", add_help=False).set_defaults(command="help")
        subparsers.add_parser("help", add_help=False).set_defaults(command="help")
        subparsers.add_parser("sair", add_help=False).set_defaults(command="exit")
        subparsers.add_parser("exit", add_help=False).set_defaults(command="exit")
        subparsers.add_parser("quit", add_help=False).set_defaults(command="exit")

        lists_parser = subparsers.add_parser("lists", add_help=False)
        lists_parser.add_argument("--board", required=True)

        cards_parser = subparsers.add_parser("cards", add_help=False)
        cards_parser.add_argument("--board", required=True)
        cards_parser.add_argument("--list", dest="list_name")

        create_parser = subparsers.add_parser("create-card", add_help=False)
        create_parser.add_argument("--board", required=True)
        create_parser.add_argument("--list", dest="list_name", required=True)
        create_parser.add_argument("--title", required=True)
        create_parser.add_argument("--desc", default="")

        move_parser = subparsers.add_parser("move-card", add_help=False)
        move_parser.add_argument("--board", required=True)
        move_parser.add_argument("--card", required=True)
        move_parser.add_argument("--list", dest="list_name", required=True)

        comment_parser = subparsers.add_parser("comment-card", add_help=False)
        comment_parser.add_argument("--board", required=True)
        comment_parser.add_argument("--card", required=True)
        comment_parser.add_argument("--text", required=True)

        return parser

    def _handle_boards(self) -> str:
        boards = self.service.list_boards()
        if not boards:
            return "Nenhum board aberto encontrado."

        lines = ["Boards encontrados:"]
        lines.extend(f'- {board["name"]} ({board["id"]})' for board in boards)
        return "\n".join(lines)

    def _handle_lists(self, board_name: str) -> str:
        result = self.service.list_lists(board_name)
        board = result["board"]
        lists_ = result["lists"]

        if not lists_:
            return f'O board "{board["name"]}" não possui listas abertas.'

        lines = [f'Listas do board "{board["name"]}":']
        lines.extend(f'- {list_["name"]} ({list_["id"]})' for list_ in lists_)
        return "\n".join(lines)

    def _handle_cards(self, board_name: str, list_name: str | None) -> str:
        result = self.service.list_cards(board_name, list_name)
        board = result["board"]

        if list_name:
            list_ = result["list"]
            cards = result["cards"]
            if not cards:
                return f'A lista "{list_["name"]}" não possui cards.'

            lines = [f'Cards da lista "{list_["name"]}" no board "{board["name"]}":']
            lines.extend(self._format_card_line(card) for card in cards)
            return "\n".join(lines)

        cards = result["cards"]
        if not cards:
            return f'O board "{board["name"]}" não possui cards.'

        lines = [f'Cards do board "{board["name"]}":']
        lines.extend(self._format_card_line(card) for card in cards)
        return "\n".join(lines)

    def _handle_create_card(
        self, board_name: str, list_name: str, title: str, description: str
    ) -> str:
        result = self.service.create_card(board_name, list_name, title=title, description=description)
        board = result["board"]
        list_ = result["list"]
        card = result["card"]

        return (
            f'Card "{card["name"]}" criado na lista "{list_["name"]}" do board "{board["name"]}".\n'
            f'URL: {card.get("shortUrl", "indisponível")}'
        )

    def _handle_move_card(self, board_name: str, card_name: str, target_list_name: str) -> str:
        result = self.service.move_card(board_name, card_name, target_list_name)
        card = result["card"]
        target_list = result["target_list"]

        return f'Card "{card["name"]}" movido para a lista "{target_list["name"]}".'

    def _handle_comment_card(self, board_name: str, card_name: str, text: str) -> str:
        result = self.service.comment_card(board_name, card_name, text)
        card = result["card"]

        return f'Comentário adicionado ao card "{card["name"]}".'

    @staticmethod
    def _format_card_line(card: dict[str, object]) -> str:
        return f'- {card["name"]} ({card["id"]})'

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold().strip())
        return "".join(char for char in decomposed if not unicodedata.combining(char))
