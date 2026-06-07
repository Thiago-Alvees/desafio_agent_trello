# desafio_agent_trello

Agente em Python para interagir com o Trello de duas formas:

- modo `chat`, em que o Gemini decide quando chamar tools
- modo `cli`, em que voce executa comandos diretos sem LLM

## Requisitos

- Python 3.11 ou superior
- Conta no Trello com `API Key` e `Token`
- Chave do Gemini para usar o modo `chat`

## Configuracao

1. Instale as dependencias:

```bash
pip install -r requirements.txt
```

Ou crie um arquivo `requirements.txt`:

```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_SECRET=your_trello_api_secret
TRELLO_TOKEN=your_trello_token

GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-2.5-flash
```

## Como a configuracao funciona

- O modo `chat` procura `GOOGLE_API_KEY` e, se ela nao existir, tenta `GEMINI_API_KEY`.
- Se nenhuma chave existir, `python main.py` entra no modo `cli`.

## Como executar

Modo chat:

```bash
python main.py
python main.py chat
python main.py chat "quais cards eu tenho no board Tarefas?"
```

Modo CLI:

```bash
python main.py cli
python main.py boards
python main.py cli lists --board "Tarefas"
python main.py create-card --board "Tarefas" --list "A fazer" --title "Implementar login"
```

## Exemplos de prompts no chat

- `Quais boards eu tenho?`
- `Liste os cards do board Tarefas`
- `Crie um card chamado "Pagar conta de luz" na lista "A fazer" do board "Tarefas"`
- `Mova o card "Pagar conta de luz" para "Em andamento" no board "Tarefas"`
- `Adicione o comentario "feito pelo chat" no card "Pagar conta de luz" do board "Tarefas"`

## Comandos do modo chat

- `/help` ou `/ajuda`
- `/reset`
- `/sair`

## Comandos do modo CLI

- `boards`
- `lists --board "Nome do board"`
- `cards --board "Nome do board" [--list "Nome da lista"]`
- `create-card --board "Nome do board" --list "Nome da lista" --title "Titulo" [--desc "Descricao"]`
- `move-card --board "Nome do board" --card "Nome do card" --list "Lista destino"`
- `comment-card --board "Nome do board" --card "Nome do card" --text "Comentario"`
- `ajuda`
- `sair`

## Estrutura principal

- [main.py](/c:/Users/thiag/Desktop/portfólio/Projetos/desafio_agent_trello/main.py): decide se entra em chat ou CLI
- [trello_agent/service.py](/c:/Users/thiag/Desktop/portfólio/Projetos/desafio_agent_trello/trello_agent/service.py): regras de negocio do Trello
- [trello_agent/tools.py](/c:/Users/thiag/Desktop/portfólio/Projetos/desafio_agent_trello/trello_agent/tools.py): tools compartilhadas entre CLI e chat
- [trello_agent/chat.py](/c:/Users/thiag/Desktop/portfólio/Projetos/desafio_agent_trello/trello_agent/chat.py): integracao com Gemini
- [trello_agent/agent.py](/c:/Users/thiag/Desktop/portfólio/Projetos/desafio_agent_trello/trello_agent/agent.py): parser do modo CLI

## Testes

```bash
python -m unittest discover -s tests
```

## Observacoes

- O Gemini usa o SDK oficial `google-genai` com `FunctionDeclaration.from_callable` e um loop manual de function calling.
- As credenciais do `.env` devem ficar fora do versionamento.
