class TrelloAgentError(Exception):
    """Base exception for the Trello agent."""


class ConfigurationError(TrelloAgentError):
    """Raised when the local configuration is incomplete."""


class CommandError(TrelloAgentError):
    """Raised when the command entered by the user is invalid."""


class NotFoundError(CommandError):
    """Raised when an entity cannot be found."""


class AmbiguousMatchError(CommandError):
    """Raised when a query matches multiple entities."""


class TrelloAPIError(TrelloAgentError):
    """Raised when the Trello API returns an error."""
