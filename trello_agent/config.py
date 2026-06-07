from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from trello_agent.exceptions import ConfigurationError


@dataclass(frozen=True)
class TrelloSettings:
    # Esta classe concentra apenas as credenciais do Trello.
    # Separar a configuracao em objetos pequenos deixa o restante do codigo
    # mais simples de testar e de entender.
    api_key: str
    token: str
    api_secret: str | None = None
    api_base_url: str = "https://api.trello.com/1"
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "TrelloSettings":
        load_dotenv()

        api_key = os.getenv("TRELLO_API_KEY", "").strip()
        token = os.getenv("TRELLO_TOKEN", "").strip()
        api_secret = os.getenv("TRELLO_API_SECRET", "").strip() or None

        if not api_key:
            raise ConfigurationError("Defina TRELLO_API_KEY no arquivo .env.")

        if not token:
            raise ConfigurationError("Defina TRELLO_TOKEN no arquivo .env.")

        return cls(api_key=api_key, token=token, api_secret=api_secret)


@dataclass(frozen=True)
class GoogleSettings:
    api_key: str
    model: str = "gemini-2.5-flash"

    @classmethod
    def from_env(cls, required: bool = False) -> "GoogleSettings | None":
        load_dotenv()

        # Aceitamos os dois nomes porque a documentacao do Gemini costuma usar
        # GEMINI_API_KEY, mas muita gente salva a mesma chave como GOOGLE_API_KEY.
        api_key = os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
        model = os.getenv("GOOGLE_MODEL", "").strip() or "gemini-2.5-flash"

        if not api_key:
            if required:
                raise ConfigurationError(
                    "Defina GOOGLE_API_KEY ou GEMINI_API_KEY no .env para usar o modo chat com Google."
                )
            return None

        return cls(api_key=api_key, model=model)


def load_chat_settings(required: bool = False) -> GoogleSettings | None:
    """
    Carrega a configuracao do Gemini a partir do ambiente.

    Mantivemos esta funcao separada porque o `main.py` nao precisa conhecer
    os detalhes das variaveis de ambiente; ele apenas pede "as configuracoes
    do chat".
    """
    return GoogleSettings.from_env(required=required)
