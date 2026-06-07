from __future__ import annotations

from typing import Any, Protocol

from trello_agent.config import GoogleSettings
from trello_agent.tools import TrelloToolRegistry


# Este prompt funciona como a "personalidade" do agente.
# Como o projeto agora usa apenas Gemini, a instrucao fica centralizada aqui.
SYSTEM_PROMPT = """
Voce e um assistente de Trello em portugues do Brasil.
Seu trabalho e conversar com o usuario e usar as tools disponiveis para ler ou alterar dados no Trello.

Regras:
- Use tools sempre que a resposta depender do estado atual do Trello.
- Nunca invente boards, listas, cards ou resultados de acoes.
- So confirme uma criacao, movimentacao ou comentario depois que a tool retornar sucesso.
- Se a tool retornar erro de ambiguidade ou item nao encontrado, explique isso com clareza e peca a informacao minima necessaria.
- Se o usuario pedir os cards de um board e nao citar uma lista, liste os cards do board inteiro.
- Seja objetivo, mas preserve detalhes importantes como nomes de boards, listas, cards e URLs quando disponiveis.
""".strip()


class ChatGateway(Protocol):
    """
    Interface minima usada pela sessao de chat.

    A sessao em si so espera dois comportamentos:
    - enviar uma mensagem
    - limpar o contexto
    """

    def send_message(self, user_message: str) -> str:
        """Envia uma mensagem ao modelo e devolve a resposta final em texto."""

    def reset(self) -> None:
        """Limpa o contexto conversacional mantido pelo backend."""


class GoogleChatGateway:
    """
    Implementacao do Gemini usando o SDK oficial `google-genai`.

    Embora o SDK tenha modo automatico, aqui usamos um loop manual porque ele
    nos da mais previsibilidade para depurar e para manter explicito cada passo
    do function calling.
    """

    def __init__(self, settings: GoogleSettings, tool_registry: TrelloToolRegistry) -> None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "A biblioteca google-genai nao esta instalada. Rode: pip install -r requirements.txt"
            ) from exc

        self.client = genai.Client(api_key=settings.api_key)
        self.types = types
        self.settings = settings
        self.tool_registry = tool_registry
        self.history: list[Any] = []
        self.config = self._create_config()

    def send_message(self, user_message: str) -> str:
        working_history = list(self.history)
        working_history.append(self._user_text_content(user_message))

        response = self._generate_content(working_history)

        while True:
            function_calls = list(getattr(response, "function_calls", None) or [])
            if not function_calls:
                working_history.extend(self._response_history_items(response))
                self.history = working_history
                return self._extract_text(response)

            working_history.extend(self._response_history_items(response))
            working_history.append(self._function_results_content(function_calls))
            response = self._generate_content(working_history)

    def reset(self) -> None:
        self.history.clear()

    def _create_config(self) -> Any:
        # O Gemini aceita declarations derivadas diretamente de funcoes Python.
        function_declarations = [
            self.types.FunctionDeclaration.from_callable(callable=func, client=self.client)
            for func in self.tool_registry.google_functions()
        ]

        return self.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[self.types.Tool(function_declarations=function_declarations)],
            automatic_function_calling=self.types.AutomaticFunctionCallingConfig(disable=True),
        )

    def _generate_content(self, contents: list[Any]) -> Any:
        return self.client.models.generate_content(
            model=self.settings.model,
            contents=contents,
            config=self.config,
        )

    def _function_results_content(self, function_calls: list[Any]) -> Any:
        parts = []
        for function_call in function_calls:
            result = self.tool_registry.execute(function_call.name, dict(function_call.args))
            parts.append(
                self.types.Part.from_function_response(
                    name=function_call.name,
                    response=result,
                )
            )

        return self.types.Content(role="user", parts=parts)

    def _response_history_items(self, response: Any) -> list[Any]:
        items: list[Any] = []
        candidates = getattr(response, "candidates", None) or []
        if candidates and getattr(candidates[0], "content", None) is not None:
            items.append(candidates[0].content)
        return items

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "text", "") or ""
        if text.strip():
            return text.strip()

        texts: list[str] = []
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            if content is None:
                continue

            for part in getattr(content, "parts", None) or []:
                part_text = getattr(part, "text", None)
                if part_text:
                    texts.append(part_text)

        if texts:
            return "\n".join(texts).strip()

        return "Nao houve resposta em texto."

    def _user_text_content(self, text: str) -> Any:
        return self.types.Content(role="user", parts=[self.types.Part(text=text)])


def build_chat_gateway(settings: GoogleSettings, tool_registry: TrelloToolRegistry) -> ChatGateway:
    """Fabrica simples: cria o gateway do Gemini."""
    return GoogleChatGateway(settings, tool_registry)


class TrelloChatSession:
    """
    Fachada pequena usada pelo restante do programa.

    Ela existe para que `main.py` nao precise conhecer os detalhes do Gemini.
    """

    def __init__(
        self,
        settings: GoogleSettings,
        tool_registry: TrelloToolRegistry,
        gateway: ChatGateway | None = None,
    ) -> None:
        self.settings = settings
        self.tool_registry = tool_registry
        self.gateway = gateway or build_chat_gateway(settings, tool_registry)

    def ask(self, user_message: str) -> str:
        return self.gateway.send_message(user_message)

    def reset(self) -> None:
        self.gateway.reset()
