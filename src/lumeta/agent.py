from typing import Any, Dict, Optional

from .interpreter import RequestInterpreter
from .router import RequestRouter
from .schemas import AgentResponse, IncomingRequest


class LumetaAgent:
    """Agente Lumeta: recebe, interpreta e roteia solicitações."""

    NAME = "Lumeta"

    def __init__(
        self,
        mode: Optional[str] = None,
        interpreter: Optional[RequestInterpreter] = None,
        router: Optional[RequestRouter] = None,
    ) -> None:
        self.interpreter = interpreter or RequestInterpreter(mode=mode)
        self.router = router or RequestRouter()

    def receive(
        self,
        text: str,
        sender_id: str = "anonimo",
        channel: str = "cli",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        if not text or not text.strip():
            raise ValueError("A solicitação não pode estar vazia.")

        request = IncomingRequest(
            text=text.strip(),
            sender_id=sender_id,
            channel=channel,
            metadata=metadata or {},
        )
        interpretation = self.interpreter.interpret(request)
        routed_to, reply_message = self.router.route(request, interpretation)

        return AgentResponse(
            agent_name=self.NAME,
            request_id=request.request_id,
            interpretation=interpretation,
            routed_to=routed_to,
            reply_message=reply_message,
            raw_text=request.text,
        )
