import time
from typing import Any, Dict, List, Optional, Sequence

from .interpreter import RequestInterpreter
from .memory import SessionMemory
from .middleware import BaseMiddleware
from .router import RequestRouter
from .schemas import AgentResponse, IncomingRequest


class LumetaAgent:
    """Agente Lumeta v2.0: recebe, interpreta com contexto, aplica middlewares e roteia."""

    NAME = "Lumeta"
    VERSION = "2.0.0"

    def __init__(
        self,
        mode: Optional[str] = None,
        interpreter: Optional[RequestInterpreter] = None,
        router: Optional[RequestRouter] = None,
        memory: Optional[SessionMemory] = None,
        middlewares: Optional[Sequence[BaseMiddleware]] = None,
    ) -> None:
        self.interpreter = interpreter or RequestInterpreter(mode=mode)
        self.router = router or RequestRouter()
        self.memory = memory or SessionMemory()
        self.middlewares: List[BaseMiddleware] = list(middlewares or [])

    def add_middleware(self, middleware: BaseMiddleware) -> None:
        self.middlewares.append(middleware)

    def receive(
        self,
        text: str,
        sender_id: str = "anonimo",
        channel: str = "cli",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        if not text or not text.strip():
            raise ValueError("A solicitação não pode estar vazia.")

        started_at = time.perf_counter()
        request = IncomingRequest(
            text=text.strip(),
            sender_id=sender_id,
            channel=channel,
            session_id=session_id,
            metadata=metadata or {},
        )

        for mw in self.middlewares:
            request = mw.before_interpret(request)

        # Se o turno anterior da mesma sessão pediu clarificação, combina contexto
        context_text: Optional[str] = None
        last_turn = self.memory.get_last_turn(request.session_id)
        if last_turn and last_turn.get("needs_clarification"):
            context_text = last_turn.get("text")

        interpretation = self.interpreter.interpret(request, context_text=context_text)
        routed_to, reply_message = self.router.route(request, interpretation)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

        response = AgentResponse(
            agent_name=self.NAME,
            agent_version=self.VERSION,
            request_id=request.request_id,
            session_id=request.session_id,
            interpretation=interpretation,
            routed_to=routed_to,
            reply_message=reply_message,
            latency_ms=latency_ms,
            raw_text=request.text,
        )

        for mw in self.middlewares:
            response = mw.after_route(request, response)

        self.memory.add_turn(
            request.session_id,
            {
                "request_id": request.request_id,
                "text": request.text if not context_text else f"{context_text} | {request.text}",
                "intent": interpretation.intent,
                "needs_clarification": interpretation.needs_clarification,
                "timestamp": request.timestamp,
            },
        )
        return response

    def receive_batch(self, items: Sequence[Dict[str, Any]]) -> List[AgentResponse]:
        responses: List[AgentResponse] = []
        for item in items:
            responses.append(
                self.receive(
                    text=item["text"],
                    sender_id=item.get("sender_id", "anonimo"),
                    channel=item.get("channel", "batch"),
                    session_id=item.get("session_id"),
                    metadata=item.get("metadata"),
                )
            )
        return responses
