from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class IncomingRequest:
    """Representa uma solicitação bruta recebida pela Lumeta."""

    text: str
    sender_id: str = "anonimo"
    channel: str = "cli"
    session_id: Optional[str] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id:
            self.session_id = f"{self.channel}:{self.sender_id}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterpretationResult:
    """Resultado estruturado da interpretação feita pela Lumeta v2.0."""

    intent: str
    priority: str
    confidence: float
    summary: str
    sentiment: str = "neutro"
    secondary_intents: List[str] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    missing_info: List[str] = field(default_factory=list)
    suggested_action: str = ""
    engine_used: str = "local"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResponse:
    """Resposta completa do agente Lumeta após interpretar e rotear."""

    agent_name: str
    agent_version: str
    request_id: str
    session_id: str
    interpretation: InterpretationResult
    routed_to: str
    reply_message: str
    latency_ms: float = 0.0
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "interpretation": self.interpretation.to_dict(),
            "routed_to": self.routed_to,
            "reply_message": self.reply_message,
            "latency_ms": self.latency_ms,
        }
