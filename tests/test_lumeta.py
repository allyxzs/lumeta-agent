import unittest
from lumeta import LumetaAgent


class TestLumetaAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = LumetaAgent(mode="local")

    def test_suporte_tecnico_critico(self) -> None:
        resp = self.agent.receive("Urgente! Sistema fora do ar, erro no login às 09:30.")
        self.assertEqual(resp.agent_name, "Lumeta")
        self.assertEqual(resp.interpretation.intent, "suporte_tecnico")
        self.assertEqual(resp.interpretation.priority, "critica")
        self.assertIn("09:30", resp.interpretation.entities.get("horarios", []))

    def test_financeiro_com_entidades(self) -> None:
        resp = self.agent.receive(
            "Preciso do reembolso da fatura do pedido #98765 no valor de R$ 199,90. Meu e-mail é teste@exemplo.com"
        )
        self.assertEqual(resp.interpretation.intent, "financeiro")
        self.assertFalse(resp.interpretation.needs_clarification)
        self.assertIn("98765", resp.interpretation.entities.get("protocolos_ou_pedidos", []))
        self.assertIn("R$ 199,90", resp.interpretation.entities.get("valores", []))
        self.assertIn("teste@exemplo.com", resp.interpretation.entities.get("emails", []))

    def test_agendamento_sem_data_pede_clarificacao(self) -> None:
        resp = self.agent.receive("Quero agendar uma reunião com a equipe.")
        self.assertEqual(resp.interpretation.intent, "agendamento")
        self.assertTrue(resp.interpretation.needs_clarification)
        self.assertTrue(len(resp.interpretation.missing_info) > 0)

    def test_solicitacao_vazia_gera_erro(self) -> None:
        with self.assertRaises(ValueError):
            self.agent.receive("   ")


if __name__ == "__main__":
    unittest.main()
