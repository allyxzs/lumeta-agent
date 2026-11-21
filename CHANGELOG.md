# Changelog — Lumeta Agent

## [2.0.0] - 2026-11-21
### Adicionado
- **Suporte Multi-Provider**: motor híbrido com suporte a `local` (heurístico), `ollama` (LLM local via HTTP nativo sem dependências externas) e `llm` (OpenAI ou API compatível), com fallback automático em caso de falha.
- **Memória de Sessão (`memory.py`)**: histórico por `session_id` que permite complementar solicitações anteriores quando a Lumeta pede clarificação.
- **Análise de Sentimento e Intenções Secundárias**: detecção de sentimento (`positivo`, `neutro`, `negativo`, `frustrado`) e lista de `secondary_intents`.
- **Extração Expandida de Entidades**: além de e-mails, datas, horários, valores e protocolos, agora extrai telefones (formato BR), CPF/CNPJ e URLs.
- **Sistema de Middlewares (`middleware.py`)**: hooks pré e pós-processamento com suporte nativo a normalização, mascaramento opcional de dados sensíveis (PII) e log de auditoria em JSONL.
- **API HTTP Nativa (`api.py`)**: servidor REST leve sem dependências externas (`GET /health`, `POST /v1/interpret`, `POST /v1/batch`, `GET /v1/sessions/{id}`).
- **Processamento em Lote (`receive_batch`)**: interpreta múltiplas solicitações de uma vez e suporta execução via CLI (`--batch`).
- **Métricas de Execução**: tempo de resposta (`latency_ms`) e motor utilizado (`engine_used`) em cada resposta.
- **Empacotamento Moderno**: `pyproject.toml` com comando instalável `lumeta` e `.gitignore` incluído.

## [1.0.0]
- Versão inicial com interpretação local/LLM, roteador básico e CLI interativa.
