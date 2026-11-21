import json
import tempfile
import unittest
from pathlib import Path

from lumeta import AuditLogMiddleware, LumetaAgent, PIIMaskingMiddleware


class TestLumetaAgentV2(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = LumetaAgent(mode="local")

    def test_suporte_tecnico_critico_e_sentimento_frustrado(self) -> None:
        resp = self.agent.receive(
            "Absurdo! Sistema fora do ar desde 09:30, erro no login. Meu telefone é (21) 99888-7766."
        )
        self.assertEqual(resp.agent_name, "Lumeta")
        self.assertEqual(resp.agent_version, "2.0.0")
        self.assertEqual(resp.interpretation.intent, "suporte_tecnico")
        self.assertEqual(resp.interpretation.priority, "critica")
        self.assertEqual(resp.interpretation.sentiment, "frustrado")
        self.assertIn("09:30", resp.interpretation.entities.get("horarios", []))
        self.assertIn("(21) 99888-7766", resp.interpretation.entities.get("telefones", []))

    def test_multiplas_intencoes_e_entidades_ricas(self) -> None:
        resp = self.agent.receive(
            "Quero orçamento do plano enterprise e também preciso da fatura #98765 de R$ 199,90. CPF 123.456.789-00 https://status.exemplo.com"
        )
        self.assertIn(resp.interpretation.intent, {"comercial", "financeiro"})
        self.assertTrue(len(resp.interpretation.secondary_intents) >= 1)
        self.assertIn("123.456.789-00", resp.interpretation.entities.get("cpfs", []))
        self.assertIn("https://status.exemplo.com", resp.interpretation.entities.get("urls", []))

    def test_memoria_de_sessao_combina_clarificacao(self) -> None:
        sessao = "whatsapp:cliente_99"
        r1 = self.agent.receive("Quero agendar uma reunião com a equipe.", session_id=sessao)
        self.assertEqual(r1.interpretation.intent, "agendamento")
        self.assertTrue(r1.interpretation.needs_clarification)

        r2 = self.agent.receive("Pode ser dia 28/11 às 15:00.", session_id=sessao)
        self.assertEqual(r2.interpretation.intent, "agendamento")
        self.assertFalse(r2.interpretation.needs_clarification)
        self.assertIn("28/11", r2.interpretation.entities.get("datas", []))

    def test_middlewares_pii_e_audit_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.jsonl"
            agent = LumetaAgent(
                mode="local",
                middlewares=[PIIMaskingMiddleware(), AuditLogMiddleware(str(log_file))],
            )
            resp = agent.receive("Quero cancelar assinatura, meu CPF é 123.456.789-00.")
            self.assertEqual(resp.interpretation.intent, "cancelamento")
            self.assertNotIn("123.456.789-00", resp.interpretation.summary)
            self.assertIn("[CPF_OCULTO]", resp.interpretation.summary)
            self.assertTrue(log_file.exists())
            saved = json.loads(log_file.read_text(encoding="utf-8").strip())
            self.assertEqual(saved["interpretation"]["intent"], "cancelamento")

    def test_batch_processing(self) -> None:
        items = [
            {"text": "Erro no login", "sender_id": "u1"},
            {"text": "Quero um orçamento para o plano pro", "sender_id": "u2"},
        ]
        results = self.agent.receive_batch(items)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].interpretation.intent, "suporte_tecnico")
        self.assertEqual(results[1].interpretation.intent, "comercial")

    def test_solicitacao_vazia_gera_erro(self) -> None:
        with self.assertRaises(ValueError):
            self.agent.receive("   ")


if __name__ == "__main__":
    unittest.main()
