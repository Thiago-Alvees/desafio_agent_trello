from __future__ import annotations

import unittest

from trello_agent.agent import TrelloAgent
from trello_agent.service import TrelloService

from tests.fakes import FakeTrelloClient


class TrelloAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeTrelloClient()
        self.agent = TrelloAgent(TrelloService(self.client))

    def test_lists_command_uses_partial_board_name(self) -> None:
        output = self.agent.handle('lists --board "projeto"')

        self.assertIn('Listas do board "Projeto Principal"', output)
        self.assertIn("A Fazer", output)

    def test_create_card_natural_language_command(self) -> None:
        output = self.agent.handle(
            'criar card "Nova tarefa" na lista "A Fazer" do board "Projeto Principal" '
            'com descricao "Detalhes do card"'
        )

        self.assertIn('Card "Nova tarefa" criado', output)
        self.assertEqual(self.client.created_cards[0]["idList"], "list-1")
        self.assertEqual(self.client.created_cards[0]["desc"], "Detalhes do card")

    def test_move_card_command(self) -> None:
        output = self.agent.handle(
            'move-card --board "Projeto Principal" --card "Corrigir login" --list "Em Andamento"'
        )

        self.assertIn('movido para a lista "Em Andamento"', output)
        self.assertEqual(self.client.moved_cards[0]["id"], "card-1")
        self.assertEqual(self.client.moved_cards[0]["idList"], "list-2")

    def test_comment_card_command(self) -> None:
        output = self.agent.handle(
            'comment-card --board "Projeto Principal" --card "Corrigir login" --text "Iniciado"'
        )

        self.assertIn("Comentario adicionado", output.replace("á", "a"))
        self.assertEqual(self.client.comments[0]["text"], "Iniciado")

    def test_handle_list_arguments(self) -> None:
        output = self.agent.handle(["lists", "--board", "Projeto Principal"])

        self.assertIn('Listas do board "Projeto Principal"', output)


if __name__ == "__main__":
    unittest.main()
