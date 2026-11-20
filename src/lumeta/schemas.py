from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class IncomingRequest:
    """Representa uma solicitação bruta recebida pela Lumeta."""

    text: str
    sender_id: str = "anonimo"
    channel: str = "cli"
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterpretationResult:
    """Resultado estruturado da interpretação feita pela Lumeta."""

    intent: str
    priority: str
    confidence: float
    summary: str
    entities: Dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    missing_info: List[str] = field(default_factory=list)
    suggested_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    """Resposta completa do agente Lumeta após interpretar e rotear."""

    agent_name: str
    request_id: str
    interpretation: InterpretationResult
    routed_to: str
    reply_message: str
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "request_id": self.request_id,
            "interpretation": self.interpretation.to_dict(),
            "routed_to": self.routed_to,
            "reply_message": self.reply_message,
        }
