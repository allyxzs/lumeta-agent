import json
import re
from pathlib import Path
from typing import Protocol

from .schemas import AgentResponse, IncomingRequest


class RequestMiddleware(Protocol):
    def before_interpret(self, request: IncomingRequest) -> IncomingRequest: ...
    def after_route(self, request: IncomingRequest, response: AgentResponse) -> AgentResponse: ...


class BaseMiddleware:
    """Classe base para criação de middlewares customizados na Lumeta."""

    def before_interpret(self, request: IncomingRequest) -> IncomingRequest:
        return request

    def after_route(self, request: IncomingRequest, response: AgentResponse) -> AgentResponse:
        return response


class PIIMaskingMiddleware(BaseMiddleware):
    """Mascara CPF e CNPJ no texto salvo em logs/metadados sem perder a detecção."""

    CPF_PATTERN = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
    CNPJ_PATTERN = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")

    def after_route(self, request: IncomingRequest, response: AgentResponse) -> AgentResponse:
        if response.raw_text:
            masked = self.CPF_PATTERN.sub("[CPF_OCULTO]", response.raw_text)
            masked = self.CNPJ_PATTERN.sub("[CNPJ_OCULTO]", masked)
            response.raw_text = masked
        response.interpretation.summary = self.CPF_PATTERN.sub(
            "[CPF_OCULTO]", response.interpretation.summary
        )
        response.interpretation.summary = self.CNPJ_PATTERN.sub(
            "[CNPJ_OCULTO]", response.interpretation.summary
        )
        return response


class AuditLogMiddleware(BaseMiddleware):
    """Registra cada solicitação interpretada em arquivo JSONL para auditoria."""

    def __init__(self, log_path: str = "logs/audit.jsonl") -> None:
        self.log_path = Path(log_path)

    def after_route(self, request: IncomingRequest, response: AgentResponse) -> AgentResponse:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": request.timestamp,
            "channel": request.channel,
            "sender_id": request.sender_id,
            **response.to_dict(),
        }
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return response
