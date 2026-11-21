import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Type

from .agent import LumetaAgent


def create_handler(agent: LumetaAgent) -> Type[BaseHTTPRequestHandler]:
    class LumetaHTTPHandler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> Dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            return json.loads(raw)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "agent": agent.NAME,
                        "version": agent.VERSION,
                        "mode": agent.interpreter.mode,
                    },
                )
                return

            if self.path.startswith("/v1/sessions/"):
                session_id = self.path.split("/v1/sessions/", 1)[1]
                history = agent.memory.get_history(session_id)
                self._send_json(200, {"session_id": session_id, "history": history})
                return

            self._send_json(404, {"error": "Endpoint não encontrado."})

        def do_POST(self) -> None:
            try:
                data = self._read_json()
            except json.JSONDecodeError:
                self._send_json(400, {"error": "JSON inválido."})
                return

            if self.path == "/v1/interpret":
                text = data.get("text", "")
                if not isinstance(text, str) or not text.strip():
                    self._send_json(400, {"error": "Campo 'text' é obrigatório."})
                    return
                resp = agent.receive(
                    text=text,
                    sender_id=data.get("sender_id", "api_user"),
                    channel=data.get("channel", "api"),
                    session_id=data.get("session_id"),
                    metadata=data.get("metadata"),
                )
                self._send_json(200, resp.to_dict())
                return

            if self.path == "/v1/batch":
                items = data.get("requests", [])
                if not isinstance(items, list) or not items:
                    self._send_json(400, {"error": "Campo 'requests' deve ser uma lista não vazia."})
                    return
                results = [r.to_dict() for r in agent.receive_batch(items)]
                self._send_json(200, {"count": len(results), "results": results})
                return

            self._send_json(404, {"error": "Endpoint não encontrado."})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return LumetaHTTPHandler


def serve(agent: LumetaAgent, host: str = "127.0.0.1", port: int = 8080) -> None:
    server = HTTPServer((host, port), create_handler(agent))
    print(f"Lumeta API v{agent.VERSION} rodando em http://{host}:{port}")
    print("Endpoints: GET /health | POST /v1/interpret | POST /v1/batch | GET /v1/sessions/<id>")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor Lumeta encerrado.")
    finally:
        server.server_close()
