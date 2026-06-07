# Desafio Agent Trello

Agente em Python para automação de tarefas no Trello, desenvolvido com foco didático para demonstrar a integração entre API, organização de código e uso de Inteligência Artificial em um caso prático.

A proposta do projeto é permitir que o usuário interaja com o Trello de duas formas: por comandos diretos no terminal ou por linguagem natural com apoio do Gemini. Dessa forma, é possível executar ações reais em um board, como listar quadros, consultar cards, criar tarefas, mover cards entre listas e adicionar comentários.

## Visão Geral

Este projeto demonstra como construir um agente capaz de unir automação tradicional com IA generativa.

O diferencial é que a IA não “inventa” respostas sobre o Trello. Sempre que precisa consultar ou alterar informações, ela utiliza ferramentas reais integradas à API do Trello. Isso torna o agente mais confiável e aproxima a solução de um cenário real de assistente operacional.

A arquitetura foi organizada em camadas simples para facilitar o entendimento, a manutenção e a evolução do projeto:

* `client`: responsável pela comunicação com a API do Trello;
* `service`: concentra as regras de negócio;
* `tools`: expõe as ações como funções reutilizáveis;
* `agent`: gerencia o modo CLI;
* `chat`: conecta o Gemini e interpreta comandos em linguagem natural.

Com essa separação, o mesmo núcleo de lógica pode ser usado tanto em comandos diretos quanto em conversas com uma LLM.

## Funcionalidades

O agente permite:

* listar boards do Trello;
* listar listas de um board;
* consultar cards;
* criar novos cards;
* mover cards entre listas;
* adicionar comentários em cards;
* usar comandos diretos via CLI;
* interagir em linguagem natural com Gemini;
* executar testes automatizados sem depender da API real em todos os cenários.

## Modos de Uso

O projeto pode ser executado de duas formas:

### Modo Chat

No modo `chat`, o Gemini interpreta o pedido do usuário e decide quando chamar as tools disponíveis.

Exemplo:

```bash
python main.py chat
```

Também é possível enviar uma mensagem diretamente:

```bash
python main.py chat "quais cards eu tenho no board Tarefas?"
```

### Modo CLI

No modo `cli`, o usuário executa comandos diretos no terminal, sem uso de LLM.

Exemplo:

```bash
python main.py cli
```

Também é possível executar comandos específicos diretamente:

```bash
python main.py boards
python main.py cli lists --board "Tarefas"
python main.py create-card --board "Tarefas" --list "A fazer" --title "Implementar login"
```

## Tecnologias Utilizadas

* Python 3.11+
* API REST do Trello
* Gemini
* SDK `google-genai`
* Variáveis de ambiente com `.env`
* Function Calling
* Testes automatizados com `unittest`

## Requisitos

Antes de executar o projeto, você precisa ter:

* Python 3.11 ou superior instalado;
* uma conta no Trello;
* `API Key` e `Token` do Trello;
* uma chave de API do Gemini para usar o modo `chat`.

## Configuração do Ambiente

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/desafio_agent_trello.git
cd desafio_agent_trello
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes informações:

```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_SECRET=your_trello_api_secret
TRELLO_TOKEN=your_trello_token

GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-2.5-flash
```

## Como a Configuração Funciona

O modo `chat` procura primeiro pela variável:

```env
GOOGLE_API_KEY
```

Caso ela não exista, o sistema tenta utilizar:

```env
GEMINI_API_KEY
```

Se nenhuma chave do Gemini for encontrada, o projeto entra automaticamente no modo `cli`.

## Como Executar

### Executar no modo chat

```bash
python main.py
python main.py chat
python main.py chat "quais cards eu tenho no board Tarefas?"
```

### Executar no modo CLI

```bash
python main.py cli
python main.py boards
python main.py cli lists --board "Tarefas"
python main.py create-card --board "Tarefas" --list "A fazer" --title "Implementar login"
```

## Exemplos de Prompts no Chat

```text
Quais boards eu tenho?
```

```text
Liste os cards do board Tarefas
```

```text
Crie um card chamado "Pagar conta de luz" na lista "A fazer" do board "Tarefas"
```

```text
Mova o card "Pagar conta de luz" para "Em andamento" no board "Tarefas"
```

```text
Adicione o comentário "feito pelo chat" no card "Pagar conta de luz" do board "Tarefas"
```

## Comandos do Modo Chat

Durante o modo interativo com IA, os seguintes comandos estão disponíveis:

```text
/help
/ajuda
/reset
/sair
```

## Comandos do Modo CLI

Comandos disponíveis no terminal:

```bash
boards
```

Lista os boards disponíveis.

```bash
lists --board "Nome do board"
```

Lista as listas de um board específico.

```bash
cards --board "Nome do board"
```

Lista os cards de um board.

```bash
cards --board "Nome do board" --list "Nome da lista"
```

Lista os cards de uma lista específica.

```bash
create-card --board "Nome do board" --list "Nome da lista" --title "Título" --desc "Descrição"
```

Cria um novo card.

```bash
move-card --board "Nome do board" --card "Nome do card" --list "Lista destino"
```

Move um card para outra lista.

```bash
comment-card --board "Nome do board" --card "Nome do card" --text "Comentário"
```

Adiciona um comentário em um card.

```bash
ajuda
sair
```

Exibe ajuda ou encerra o modo CLI.

## Estrutura Principal do Projeto

```text
desafio_agent_trello/
│
├── main.py
├── trello_agent/
│   ├── service.py
│   ├── tools.py
│   ├── chat.py
│   └── agent.py
│
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

### Descrição dos Arquivos

* `main.py`: ponto de entrada da aplicação. Decide se o projeto será executado em modo chat ou CLI.
* `trello_agent/service.py`: concentra as regras de negócio relacionadas ao Trello.
* `trello_agent/tools.py`: expõe as funções reutilizáveis usadas pelo chat e pelo CLI.
* `trello_agent/chat.py`: realiza a integração com o Gemini.
* `trello_agent/agent.py`: implementa o parser e a lógica do modo CLI.
* `tests/`: contém os testes automatizados do projeto.

## Testes

Para executar os testes automatizados, use:

```bash
python -m unittest discover -s tests
```

Os testes ajudam a validar o comportamento do agente sem depender da API real do Trello em todos os cenários.

## Observações Importantes

* As credenciais devem ser armazenadas no arquivo `.env`.
* O arquivo `.env` não deve ser enviado para o GitHub.
* Recomenda-se criar um arquivo `.env.example` com os nomes das variáveis, mas sem os valores reais.
* O Gemini utiliza o SDK oficial `google-genai`.
* O projeto usa `FunctionDeclaration.from_callable` e um loop manual de function calling.
* O modo CLI pode ser usado mesmo sem chave do Gemini configurada.

## Resultado

Como resultado, este projeto demonstra na prática como construir um agente em Python que combina automação, integração com API e IA generativa.

Além de servir como estudo, a solução também apresenta uma base inicial para cenários mais avançados de assistentes operacionais, nos quais uma IA pode interpretar solicitações em linguagem natural e executar ações reais em sistemas externos de forma controlada e confiável.
