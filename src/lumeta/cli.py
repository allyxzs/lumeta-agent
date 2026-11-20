import json
from .agent import LumetaAgent


def main() -> None:
    agent = LumetaAgent()
    print("=== Lumeta Agent (digite 'sair' para encerrar) ===")
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

        response = agent.receive(user_input, channel="cli")
        print("\n" + response.reply_message)
        print("\nInterpretação estruturada:")
        print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
