from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional


class SessionMemory:
    """Gerencia histórico de curto prazo por sessão para suportar múltiplos turnos."""

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self._sessions: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_turns)
        )

    def add_turn(self, session_id: str, entry: Dict[str, Any]) -> None:
        self._sessions[session_id].append(entry)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        return list(self._sessions.get(session_id, []))

    def get_last_turn(self, session_id: str) -> Optional[Dict[str, Any]]:
        history = self._sessions.get(session_id)
        if not history:
            return None
        return history[-1]

    def clear(self, session_id: Optional[str] = None) -> None:
        if session_id is None:
            self._sessions.clear()
        else:
            self._sessions.pop(session_id, None)
