# Lumeta Agent v2.0

**Lumeta** é um agente modular em Python projetado para **receber, interpretar, enriquecer com contexto e rotear solicitações** em linguagem natural.

## Novidades da v2.0

- **Motor Multi-Provider com Fallback Automático**:
  - `local`: interpretador heurístico offline (zero dependências).
  - `ollama`: integração direta com modelos locais no Ollama via HTTP nativo.
  - `llm`: integração com APIs compatíveis com OpenAI.
- **Memória de Sessão**: mantém contexto por `session_id`, permitindo responder perguntas de clarificação em múltiplos turnos.
- **Análise Mais Rica**: extrai intenção principal, intenções secundárias, prioridade, sentimento, entidades (e-mails, telefones, CPF/CNPJ, URLs, datas, horários, valores e protocolos), confiança e métricas de latência.
- **Middlewares Extensíveis**: normalização de texto, proteção/mascaramento opcional de PII e auditoria em JSONL.
- **API REST Nativa + Batch**: suba um endpoint HTTP com `python -m lumeta.cli --serve` ou processe lotes JSON com `--batch`.

## Estrutura do Projeto

```text
lumeta-agent/
├── config/
│   └── agent_config.yaml      # Configurações de intenções, prioridades e roteamento
├── prompts/
│   └── system_prompt.md       # Prompt de sistema v2.0 para LLMs
├── src/lumeta/
│   ├── __init__.py
│   ├── schemas.py             # Modelos estruturados (Request, Interpretation, Response)
│   ├── memory.py              # Gerenciador de sessões e contexto multi-turno
│   ├── middleware.py          # Hooks pré/pós-processamento e auditoria JSONL
│   ├── interpreter.py         # Motor híbrido (local, Ollama e OpenAI)
│   ├── router.py              # Roteador extensível de intenções
│   ├── agent.py               # Orquestrador principal (LumetaAgent)
│   ├── api.py                 # Servidor REST HTTP nativo (zero dependências)
│   └── cli.py                 # CLI interativa, batch e servidor
├── examples/
│   └── sample_requests.json   # Exemplos de solicitações para teste em lote
├── tests/
│   └── test_lumeta.py         # Suíte de testes automatizados
├── CHANGELOG.md
├── pyproject.toml
├── .env.example
├── .gitignore
└── requirements.txt
```

## Como Executar

### 1. CLI Interativa (modo local)
```bash
PYTHONPATH=src python -m lumeta.cli
```

### 2. Processamento em Lote (Batch)
```bash
PYTHONPATH=src python -m lumeta.cli --batch examples/sample_requests.json
```

### 3. Subir a API REST
```bash
PYTHONPATH=src python -m lumeta.cli --serve --port 8080
```
Teste com `curl`:
```bash
curl -X POST http://127.0.0.1:8080/v1/interpret \
  -H "Content-Type: application/json" \
  -d '{"text": "Urgente! Erro no login e cobrança duplicada no pedido #45892", "sender_id": "cliente_01"}'
```

### 4. Usar com Ollama (LLM Local)
```bash
PYTHONPATH=src python -m lumeta.cli --mode ollama
```

### 5. Rodar Testes
```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```
