from typing import Callable, Dict
from .schemas import IncomingRequest, InterpretationResult


HandlerFunc = Callable[[IncomingRequest, InterpretationResult], str]


class RequestRouter:
    """Roteia solicitações interpretadas pela Lumeta para o destino adequado."""

    def __init__(self) -> None:
        self._handlers: Dict[str, HandlerFunc] = {
            "suporte_tecnico": self._handle_support,
            "financeiro": self._handle_finance,
            "comercial": self._handle_sales,
            "agendamento": self._handle_scheduling,
            "informacao_geral": self._handle_general,
            "desconhecido": self._handle_unknown,
        }

    def register_handler(self, intent: str, handler: HandlerFunc) -> None:
        self._handlers[intent] = handler

    def route(self, request: IncomingRequest, result: InterpretationResult) -> tuple[str, str]:
        target = result.intent if result.intent in self._handlers else "desconhecido"
        handler = self._handlers[target]
        message = handler(request, result)
        return target, message

    @staticmethod
    def _handle_support(_: IncomingRequest, result: InterpretationResult) -> str:
        return (
            f"[Lumeta -> Suporte Técnico | Prioridade: {result.priority.upper()}] "
            f"Solicitação interpretada e pronta para abertura de chamado. Resumo: {result.summary}"
        )

    @staticmethod
    def _handle_finance(_: IncomingRequest, result: InterpretationResult) -> str:
        extra = f" Pendências: {' '.join(result.missing_info)}" if result.missing_info else ""
        return (
            f"[Lumeta -> Financeiro | Prioridade: {result.priority.upper()}] "
            f"Demanda financeira identificada.{extra}"
        )

    @staticmethod
    def _handle_sales(_: IncomingRequest, result: InterpretationResult) -> str:
        return (
            f"[Lumeta -> Comercial | Prioridade: {result.priority.upper()}] "
            f"Interesse comercial identificado. Ação sugerida: {result.suggested_action}"
        )

    @staticmethod
    def _handle_scheduling(_: IncomingRequest, result: InterpretationResult) -> str:
        extra = f" {result.missing_info[0]}" if result.missing_info else ""
        return (
            f"[Lumeta -> Agendamento | Prioridade: {result.priority.upper()}] "
            f"Pedido de agendamento reconhecido.{extra}"
        )

    @staticmethod
    def _handle_general(_: IncomingRequest, result: InterpretationResult) -> str:
        return (
            f"[Lumeta -> Atendimento Geral] "
            f"Dúvida registrada com confiança de {int(result.confidence * 100)}%."
        )

    @staticmethod
    def _handle_unknown(_: IncomingRequest, result: InterpretationResult) -> str:
        return (
            "[Lumeta -> Triagem] Não consegui identificar com certeza a intenção da solicitação. "
            "Poderia informar mais detalhes?"
        )
