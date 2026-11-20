import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .schemas import IncomingRequest, InterpretationResult


INTENT_KEYWORDS: Dict[str, List[str]] = {
    "suporte_tecnico": [
        "erro", "bug", "falha", "não funciona", "nao funciona", "travando",
        "sistema fora", "fora do ar", "login", "senha", "acesso", "suporte",
        "quebrou", "instabilidade",
    ],
    "financeiro": [
        "fatura", "boleto", "cobrança", "cobranca", "pagamento", "reembolso",
        "nota fiscal", "nf", "estorno", "pix", "cartão", "cartao", "mensalidade",
    ],
    "comercial": [
        "orçamento", "orcamento", "preço", "preco", "plano", "contratar",
        "proposta", "comprar", "assinatura", "demonstração", "demonstracao", "upgrade",
    ],
    "agendamento": [
        "agendar", "marcar", "remarcar", "cancelar reunião", "reunião",
        "reuniao", "horário", "horario", "consulta", "agenda", "visita",
    ],
    "informacao_geral": [
        "horário de funcionamento", "endereço", "endereco", "dúvida", "duvida",
        "como funciona", "informação", "informacao", "status", "política", "politica",
    ],
}

URGENCY_KEYWORDS = {
    "critica": ["urgente", "crítico", "critico", "emergência", "emergencia", "sistema fora", "parado", "imediato"],
    "alta": ["hoje", "agora", "rápido", "rapido", "bloqueado", "não consigo acessar", "nao consigo acessar", "cobrança indevida"],
    "baixa": ["quando puder", "sem pressa", "apenas uma dúvida", "curiosidade"],
}

SUGGESTED_ACTIONS = {
    "suporte_tecnico": "Abrir chamado na fila de Suporte Técnico e coletar evidências do erro.",
    "financeiro": "Encaminhar solicitação ao setor Financeiro com dados da cobrança/documento.",
    "comercial": "Direcionar lead para o time Comercial preparar proposta.",
    "agendamento": "Consultar disponibilidade na agenda e confirmar data/horário.",
    "informacao_geral": "Responder com base na central de conhecimento.",
    "desconhecido": "Solicitar mais detalhes ao usuário para classificar corretamente.",
}


class RequestInterpreter:
    """Interpreta solicitações usando LLM (opcional) ou motor heurístico local."""

    def __init__(self, mode: str | None = None, system_prompt_path: str | None = None):
        self.mode = (mode or os.getenv("LUMETA_MODE", "local")).lower()
        self.system_prompt = self._load_system_prompt(system_prompt_path)

    @staticmethod
    def _load_system_prompt(path: str | None) -> str:
        if path and Path(path).exists():
            return Path(path).read_text(encoding="utf-8")
        default_path = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt.md"
        if default_path.exists():
            return default_path.read_text(encoding="utf-8")
        return "Você é Lumeta, um agente especialista em interpretar solicitações e responder em JSON."

    def interpret(self, request: IncomingRequest) -> InterpretationResult:
        if self.mode == "llm":
            return self._interpret_with_llm(request)
        return self._interpret_locally(request)

    def _interpret_with_llm(self, request: IncomingRequest) -> InterpretationResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return self._interpret_locally(request)

        try:
            from openai import OpenAI
        except ImportError:
            return self._interpret_locally(request)

        base_url = os.getenv("LUMETA_BASE_URL") or None
        model = os.getenv("LUMETA_MODEL", "gpt-4o-mini")
        client = OpenAI(api_key=api_key, base_url=base_url)

        completion = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": request.text},
            ],
        )

        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)
        return InterpretationResult(
            intent=data.get("intent", "desconhecido"),
            priority=data.get("priority", "media"),
            confidence=float(data.get("confidence", 0.75)),
            summary=data.get("summary", request.text[:140]),
            entities=data.get("entities", {}),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_info=list(data.get("missing_info", [])),
            suggested_action=data.get("suggested_action", ""),
        )

    def _interpret_locally(self, request: IncomingRequest) -> InterpretationResult:
        text = request.text.strip()
        lower = text.lower()

        intent, confidence = self._detect_intent(lower)
        priority = self._detect_priority(lower, intent)
        entities = self._extract_entities(text)
        missing_info = self._detect_missing_info(intent, entities, lower)
        needs_clarification = len(missing_info) > 0 or intent == "desconhecido"

        summary = text if len(text) <= 140 else text[:137].rstrip() + "..."
        suggested_action = SUGGESTED_ACTIONS.get(intent, SUGGESTED_ACTIONS["desconhecido"])

        return InterpretationResult(
            intent=intent,
            priority=priority,
            confidence=confidence,
            summary=summary,
            entities=entities,
            needs_clarification=needs_clarification,
            missing_info=missing_info,
            suggested_action=suggested_action,
        )

    @staticmethod
    def _detect_intent(lower_text: str) -> Tuple[str, float]:
        scores: Dict[str, int] = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower_text)
            if score > 0:
                scores[intent] = score

        if not scores:
            return "desconhecido", 0.35

        best_intent = max(scores, key=scores.get)
        hits = scores[best_intent]
        confidence = min(0.60 + hits * 0.12, 0.95)
        return best_intent, round(confidence, 2)

    @staticmethod
    def _detect_priority(lower_text: str, intent: str) -> str:
        for level in ("critica", "alta", "baixa"):
            if any(kw in lower_text for kw in URGENCY_KEYWORDS[level]):
                return level
        if intent == "suporte_tecnico":
            return "alta"
        return "media"

    @staticmethod
    def _extract_entities(text: str) -> Dict[str, Any]:
        entities: Dict[str, Any] = {}

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if emails:
            entities["emails"] = emails

        dates = re.findall(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", text)
        if dates:
            entities["datas"] = dates

        times = re.findall(r"\b\d{1,2}[:h]\d{2}\b", text.lower())
        if times:
            entities["horarios"] = times

        amounts = re.findall(r"R\$\s?\d+(?:[.,]\d{3})*(?:[.,]\d{2})?", text)
        if amounts:
            entities["valores"] = amounts

        protocols = re.findall(r"(?:#|protocolo\s*|pedido\s*)(\d{3,12})", text, flags=re.IGNORECASE)
        if protocols:
            entities["protocolos_ou_pedidos"] = protocols

        return entities

    @staticmethod
    def _detect_missing_info(intent: str, entities: Dict[str, Any], lower_text: str) -> List[str]:
        missing: List[str] = []
        if intent == "desconhecido":
            missing.append("Poderia detalhar melhor o que você precisa?")
        elif intent == "agendamento" and "datas" not in entities and not any(
            w in lower_text for w in ("amanhã", "amanha", "hoje", "segunda", "terça", "terca", "quarta", "quinta", "sexta")
        ):
            missing.append("Qual data e horário de preferência para o agendamento?")
        elif intent == "financeiro" and "protocolos_ou_pedidos" not in entities and "emails" not in entities:
            missing.append("Informe o número do pedido, fatura ou e-mail cadastrado.")
        return missing
