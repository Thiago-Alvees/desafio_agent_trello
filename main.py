from __future__ import annotations

import sys

from trello_agent import (
    TrelloAgent,
    TrelloChatSession,
    TrelloClient,
    TrelloService,
    TrelloSettings,
    TrelloToolRegistry,
    load_chat_settings,
)
from trello_agent.exceptions import TrelloAgentError


def run_command(agent: TrelloAgent, raw_command: str | list[str]) -> int:
    try:
        output = agent.handle(raw_command)
    except TrelloAgentError as exc:
        print(f"Erro: {exc}")
        return 1

    if output:
        print(output)

    return 0


def interactive_cli_loop(agent: TrelloAgent) -> int:
    print('Agente Trello pronto. Digite "ajuda" para ver os comandos ou "sair" para encerrar.')

    while True:
        try:
            raw_command = input("trello> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw_command:
            continue

        if agent.should_exit(raw_command):
            return 0

        run_command(agent, raw_command)


def run_chat_turn(session: TrelloChatSession, user_message: str) -> int:
    try:
        output = session.ask(user_message)
    except TrelloAgentError as exc:
        print(f"Erro: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        return 1
    except Exception as exc:
        print(f"Erro: {exc}")
        return 1

    print(output)
    return 0


def interactive_chat_loop(session: TrelloChatSession) -> int:
    print('Chat Trello pronto. Use "/reset" para limpar o contexto e "/sair" para encerrar.')

    while True:
        try:
            user_message = input("chat> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not user_message:
            continue

        normalized = user_message.casefold()
        if normalized in {"/sair", "sair", "/exit", "exit", "quit"}:
            return 0
        if normalized in {"/reset", "reset"}:
            session.reset()
            print("Contexto limpo.")
            continue
        if normalized in {"/ajuda", "/help", "ajuda", "help"}:
            print('Converse em linguagem natural. Ex.: "crie um card na lista A fazer do board Tarefas".')
            continue

        run_chat_turn(session, user_message)


def build_cli_agent() -> TrelloAgent:
    # O modo CLI nao depende de LLM. Ele conversa direto com o service.
    settings = TrelloSettings.from_env()
    service = TrelloService(TrelloClient(settings))
    return TrelloAgent(service)


def build_chat_session() -> TrelloChatSession:
    # O modo chat usa o mesmo service e as mesmas tools.
    # A unica diferenca e qual backend de LLM sera usado para decidir quando
    # chamar essas tools.
    trello_settings = TrelloSettings.from_env()
    chat_settings = load_chat_settings(required=True)
    service = TrelloService(TrelloClient(trello_settings))
    tools = TrelloToolRegistry(service)
    return TrelloChatSession(chat_settings, tools)


def main(argv: list[str] | None = None) -> int:
    try:
        argv = argv or sys.argv[1:]
        mode = argv[0] if argv and argv[0] in {"chat", "cli"} else None
        rest = argv[1:] if mode else argv

        if mode == "cli":
            agent = build_cli_agent()
            if rest:
                command_input: str | list[str] = rest[0] if len(rest) == 1 else rest
                return run_command(agent, command_input)
            return interactive_cli_loop(agent)

        if mode == "chat":
            session = build_chat_session()
            if rest:
                return run_chat_turn(session, " ".join(rest))
            return interactive_chat_loop(session)

        if argv:
            agent = build_cli_agent()
            command_input: str | list[str] = argv[0] if len(argv) == 1 else argv
            return run_command(agent, command_input)

        chat_settings = load_chat_settings(required=False)
        if chat_settings is None:
            print(
                "Nenhuma chave de LLM encontrada. Entrando no modo CLI. "
                "Configure GOOGLE_API_KEY ou GEMINI_API_KEY para usar o chat."
            )
            return interactive_cli_loop(build_cli_agent())

        session = build_chat_session()
        return interactive_chat_loop(session)
    except TrelloAgentError as exc:
        print(f"Erro: {exc}")
        return 1
    except RuntimeError as exc:
        print(f"Erro: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
