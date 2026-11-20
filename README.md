# Lumeta Agent

**Lumeta** é um agente modular projetado para **receber, interpretar, classificar e estruturar solicitações** em linguagem natural, preparando-as para roteamento ou execução por outros sistemas.

## Funcionalidades

- **Recepção padronizada**: recebe texto livre, metadados do solicitante e canal de origem.
- **Interpretação estruturada**: identifica intenção (`intent`), prioridade (`priority`), entidades-chave (`entities`), resumo objetivo e confiança (`confidence`).
- **Modo Híbrido**:
  - **Modo LLM** (via API compatível com OpenAI/Gemini configurada em `.env`).
  - **Modo Local / Fallback**: interpretador heurístico pronto para uso offline, testes e desenvolvimento sem chave de API.
- **Roteamento extensível**: mapeia intenções interpretadas para manipuladores (handlers) específicos.
- **CLI interativa** para testar solicitações direto no terminal.

## Estrutura do Projeto

```text
lumeta-agent/
├── config/
│   └── agent_config.yaml      # Configurações gerais, intenções e prioridades
├── prompts/
│   └── system_prompt.md       # Prompt de sistema do agente Lumeta
├── src/lumeta/
│   ├── __init__.py
│   ├── schemas.py             # Modelos de entrada e saída estruturada
│   ├── interpreter.py         # Motor de interpretação (LLM + fallback local)
│   ├── router.py              # Roteador de intenções para handlers
│   ├── agent.py               # Orquestrador principal (LumetaAgent)
│   └── cli.py                 # Interface de linha de comando
├── examples/
│   └── sample_requests.json   # Exemplos de solicitações para teste
├── tests/
│   └── test_lumeta.py         # Testes automatizados (unittest)
├── .env.example
└── requirements.txt
```

## Como Executar

1. (Opcional) Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # .venv\Scripts\activate   # Windows
   ```

2. (Opcional) Instale as dependências se for usar integração com LLM:
   ```bash
   pip install -r requirements.txt
   ```
   > O modo local funciona apenas com a biblioteca padrão do Python 3.9+.

3. Configure variáveis de ambiente (opcional, para modo LLM):
   ```bash
   cp .env.example .env
   ```

4. Execute a CLI interativa:
   ```bash
   PYTHONPATH=src python -m lumeta.cli
   ```

5. Execute os testes automatizados:
   ```bash
   PYTHONPATH=src python -m unittest discover -s tests -v
   ```
