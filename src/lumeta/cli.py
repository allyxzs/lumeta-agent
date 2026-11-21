import argparse
import json
from pathlib import Path

from .agent import LumetaAgent
from .api import serve
from .middleware import AuditLogMiddleware, PIIMaskingMiddleware


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lumeta Agent v2.0 — CLI e Servidor")
    parser.add_argument("--mode", choices=["local", "ollama", "llm"], default=None, help="Motor de interpretação")
    parser.add_argument("--session", default="cli:default", help="ID da sessão para manter contexto")
    parser.add_argument("--batch", type=str, default=None, help="Caminho para arquivo JSON com solicitações em lote")
    parser.add_argument("--serve", action="store_true", help="Inicia o servidor REST HTTP")
    parser.add_argument("--host", default="127.0.0.1", help="Host do servidor HTTP")
    parser.add_argument("--port", type=int, default=8080, help="Porta do servidor HTTP")
    parser.add_argument("--audit-log", type=str, default=None, help="Ativa auditoria JSONL no caminho indicado")
    parser.add_argument("--mask-pii", action="store_true", help="Mascara CPF/CNPJ nos resumos e logs")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    middlewares = []
    if args.mask_pii:
        middlewares.append(PIIMaskingMiddleware())
    if args.audit_log:
        middlewares.append(AuditLogMiddleware(args.audit_log))

    agent = LumetaAgent(mode=args.mode, middlewares=middlewares)

    if args.serve:
        serve(agent, host=args.host, port=args.port)
        return

    if args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        responses = agent.receive_batch(items)
        print(json.dumps([r.to_dict() for r in responses], ensure_ascii=False, indent=2))
        return

    print(f"=== Lumeta Agent v{agent.VERSION} (modo: {agent.interpreter.mode} | digite 'sair' para encerrar) ===")
    while True:
        try:
            user_input = input("\nSolicitação > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando Lumeta.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Até logo!")
            break

        response = agent.receive(user_input, channel="cli", session_id=args.session)
        print("\n" + response.reply_message)
        print("\nInterpretação estruturada:")
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
