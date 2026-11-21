import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schemas import IncomingRequest, InterpretationResult


INTENT_KEYWORDS: Dict[str, List[str]] = {
    "suporte_tecnico": [
        "erro", "bug", "falha", "não funciona", "nao funciona", "travando",
        "sistema fora", "fora do ar", "login", "senha", "acesso", "suporte",
        "quebrou", "instabilidade", "lento", "lentidão", "lentidao", "tela branca",
    ],
    "financeiro": [
        "fatura", "boleto", "cobrança", "cobranca", "pagamento", "reembolso",
        "nota fiscal", "nf", "estorno", "pix", "cartão", "cartao", "mensalidade",
        "duplicada", "desconto",
    ],
    "comercial": [
        "orçamento", "orcamento", "preço", "preco", "plano", "contratar",
        "proposta", "comprar", "assinatura", "demonstração", "demonstracao",
        "upgrade", "cotação", "cotacao", "enterprise",
    ],
    "agendamento": [
        "agendar", "marcar", "remarcar", "cancelar reunião", "reunião",
        "reuniao", "horário", "horario", "consulta", "agenda", "visita", "call",
    ],
    "cancelamento": [
        "cancelar conta", "encerrar conta", "cancelar assinatura",
        "cancelamento", "desistir", "excluir minha conta", "parar de usar",
    ],
    "informacao_geral": [
        "horário de funcionamento", "endereço", "endereco", "dúvida", "duvida",
        "como funciona", "informação", "informacao", "status", "política", "politica",
    ],
}

URGENCY_KEYWORDS = {
    "critica": [
        "urgente", "crítico", "critico", "emergência", "emergencia",
        "sistema fora", "fora do ar", "parado", "imediato", "perda de dados",
    ],
    "alta": [
        "hoje", "agora", "rápido", "rapido", "bloqueado", "não consigo acessar",
        "nao consigo acessar", "cobrança indevida", "cobranca indevida", "duplicada",
    ],
    "baixa": ["quando puder", "sem pressa", "apenas uma dúvida", "curiosidade"],
}

SENTIMENT_KEYWORDS = {
    "frustrado": [
        "absurdo", "péssimo", "pessimo", "cansado", "ninguém resolve",
        "ninguem resolve", "inaceitável", "inaceitavel", "revoltado", "ridículo",
        "ridiculo", "pela terceira vez", "de novo", "!!!",
    ],
    "negativo": [
        "erro", "problema", "falha", "ruim", "demora", "indevida",
        "não consigo", "nao consigo", "quebrou", "cancelar", "reclamação",
    ],
    "positivo": [
        "obrigado", "obrigada", "excelente", "ótimo", "otimo", "parabéns",
        "parabens", "adorei", "gostei", "perfeito", "maravilha",
    ],
}

SUGGESTED_ACTIONS = {
    "suporte_tecnico": "Abrir chamado na fila de Suporte Técnico e coletar evidências do erro.",
    "financeiro": "Encaminhar solicitação ao setor Financeiro com dados da cobrança/documento.",
    "comercial": "Direcionar lead para o time Comercial preparar proposta.",
    "agendamento": "Consultar disponibilidade na agenda e confirmar data/horário.",
    "cancelamento": "Acionar fluxo de Retenção/Cancelamento e validar titularidade.",
    "informacao_geral": "Responder com base na central de conhecimento.",
    "desconhecido": "Solicitar mais detalhes ao usuário para classificar corretamente.",
}


class RequestInterpreter:
    """Interpreta solicitações usando modo local, Ollama (HTTP nativo) ou OpenAI."""

    def __init__(self, mode: Optional[str] = None, system_prompt_path: Optional[str] = None):
        self.mode = (mode or os.getenv("LUMETA_MODE", "local")).lower()
        self.system_prompt = self._load_system_prompt(system_prompt_path)

    @staticmethod
    def _load_system_prompt(path: Optional[str]) -> str:
        if path and Path(path).exists():
            return Path(path).read_text(encoding="utf-8")
        default_path = Path(__file__).resolve().parents[2] / "prompts" / "system_prompt.md"
        if default_path.exists():
            return default_path.read_text(encoding="utf-8")
        return "Você é Lumeta, um agente especialista em interpretar solicitações e responder em JSON."

    def interpret(
        self,
        request: IncomingRequest,
        context_text: Optional[str] = None,
    ) -> InterpretationResult:
        effective_text = request.text if not context_text else f"{context_text}\nComplemento: {request.text}"

        if self.mode == "ollama":
            result = self._interpret_with_ollama(effective_text)
            if result is not None:
                return result
        elif self.mode == "llm":
            result = self._interpret_with_llm(effective_text)
            if result is not None:
                return result

        return self._interpret_locally(effective_text)

    def _interpret_with_ollama(self, text: str) -> Optional[InterpretationResult]:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "llama3.1")
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text},
            ],
        }
        req = urllib.request.Request(
            url=f"{host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body.get("message", {}).get("content", "{}")
            return self._parse_json_result(content, text, engine_used=f"ollama:{model}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

    def _interpret_with_llm(self, text: str) -> Optional[InterpretationResult]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            from openai import OpenAI
        except ImportError:
            return None

        base_url = os.getenv("LUMETA_BASE_URL") or None
        model = os.getenv("LUMETA_MODEL", "gpt-4o-mini")
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            completion = client.chat.completions.create(
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text},
                ],
            )
            content = completion.choices[0].message.content or "{}"
            return self._parse_json_result(content, text, engine_used=f"llm:{model}")
        except Exception:
            return None

    @staticmethod
    def _parse_json_result(content: str, fallback_text: str, engine_used: str) -> InterpretationResult:
        data = json.loads(content)
        intent = data.get("intent", "desconhecido")
        return InterpretationResult(
            intent=intent,
            secondary_intents=list(data.get("secondary_intents", [])),
            priority=data.get("priority", "media"),
            sentiment=data.get("sentiment", "neutro"),
            confidence=float(data.get("confidence", 0.8)),
            summary=data.get("summary", fallback_text[:140]),
            entities=dict(data.get("entities", {})),
            needs_clarification=bool(data.get("needs_clarification", False)),
            missing_info=list(data.get("missing_info", [])),
            suggested_action=data.get("suggested_action", SUGGESTED_ACTIONS.get(intent, "")),
            engine_used=engine_used,
        )

    def _interpret_locally(self, text: str) -> InterpretationResult:
        clean_text = " ".join(text.strip().split())
        lower = clean_text.lower()

        intent, secondary_intents, confidence = self._detect_intents(lower)
        priority = self._detect_priority(lower, intent)
        sentiment = self._detect_sentiment(lower)
        entities = self._extract_entities(clean_text)
        missing_info = self._detect_missing_info(intent, entities, lower)
        needs_clarification = len(missing_info) > 0 or intent == "desconhecido"

        summary = clean_text if len(clean_text) <= 140 else clean_text[:137].rstrip() + "..."
        suggested_action = SUGGESTED_ACTIONS.get(intent, SUGGESTED_ACTIONS["desconhecido"])

        return InterpretationResult(
            intent=intent,
            secondary_intents=secondary_intents,
            priority=priority,
            sentiment=sentiment,
            confidence=confidence,
            summary=summary,
            entities=entities,
            needs_clarification=needs_clarification,
            missing_info=missing_info,
            suggested_action=suggested_action,
            engine_used="local",
        )

    @staticmethod
    def _detect_intents(lower_text: str) -> Tuple[str, List[str], float]:
        scores: Dict[str, int] = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(len(kw.split()) for kw in keywords if kw in lower_text)
            if score > 0:
                scores[intent] = score

        if not scores:
            return "desconhecido", [], 0.35

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_intent, hits = ranked[0]
        secondary = [intent for intent, _ in ranked[1:]]
        confidence = min(0.62 + hits * 0.11, 0.96)
        return best_intent, secondary, round(confidence, 2)

    @staticmethod
    def _detect_priority(lower_text: str, intent: str) -> str:
        for level in ("critica", "alta", "baixa"):
            if any(kw in lower_text for kw in URGENCY_KEYWORDS[level]):
                return level
        if intent in {"suporte_tecnico", "cancelamento"}:
            return "alta"
        return "media"

    @staticmethod
    def _detect_sentiment(lower_text: str) -> str:
        for sentiment in ("frustrado", "positivo", "negativo"):
            if any(kw in lower_text for kw in SENTIMENT_KEYWORDS[sentiment]):
                return sentiment
        return "neutro"

    @staticmethod
    def _extract_entities(text: str) -> Dict[str, Any]:
        entities: Dict[str, Any] = {}

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if emails:
            entities["emails"] = emails

        phones = re.findall(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}-\d{4}\b", text)
        if phones:
            entities["telefones"] = [p.strip() for p in phones]

        cpfs = re.findall(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", text)
        if cpfs:
            entities["cpfs"] = cpfs

        cnpjs = re.findall(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", text)
        if cnpjs:
            entities["cnpjs"] = cnpjs

        urls = re.findall(r"https?://[^\s]+", text)
        if urls:
            entities["urls"] = urls

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
            w in lower_text
            for w in ("amanhã", "amanha", "hoje", "segunda", "terça", "terca", "quarta", "quinta", "sexta")
        ):
            missing.append("Qual data e horário de preferência para o agendamento?")
        elif intent == "financeiro" and not any(
            k in entities for k in ("protocolos_ou_pedidos", "emails", "cpfs", "cnpjs")
        ):
            missing.append("Informe o número do pedido, fatura, CPF/CNPJ ou e-mail cadastrado.")
        elif intent == "cancelamento" and not any(k in entities for k in ("emails", "cpfs", "cnpjs")):
            missing.append("Informe o e-mail ou CPF/CNPJ da conta para validar o cancelamento.")
        return missing
