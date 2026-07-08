"""
Runner alternativo de avaliação para o free tier do Gemini.

A quota gratuita observada é de ~20 requisições/dia POR MODELO — insuficiente
para uma avaliação completa (40 chamadas). Este wrapper executa o MESMO fluxo
de src/evaluate.py (sem alterá-lo), mas intercepta as chamadas de LLM e as
distribui entre vários modelos Gemini, com throttling por modelo e tratamento
de erros 429:
- quota por MINUTO: aguarda o retry_delay informado pela API e tenta de novo;
- quota por DIA: marca o modelo como esgotado e alterna para o próximo.

Uso:
    python src/evaluate_rotating.py

Modelos podem ser configurados via env GEMINI_ROTATION_MODELS (lista separada
por vírgula).
"""

import os
import re
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

# Pools separados e POR PRIORIDADE (usa o primeiro modelo com quota; só troca
# quando a quota diária dele esgota): geração e julgamento precisam de modelos
# fortes — os "lite" resumem demais (derruba recall/F1) e julgam com ruído.
# Em uma avaliação completa (10 gerações + 30 julgamentos), a distribuição
# fica dentro da quota diária de 20 requisições por modelo:
# gen: flash-latest (10) | eval: 2.5-flash (20) + 2.5-flash-lite (10).
DEFAULT_GEN_MODELS = "gemini-flash-latest,gemini-flash-lite-latest"
DEFAULT_EVAL_MODELS = (
    "gemini-2.5-flash,gemini-2.5-flash-lite,"
    "gemini-flash-lite-latest,gemini-flash-latest"
)
GEN_MODELS = [m.strip() for m in os.getenv("GEMINI_GEN_MODELS", DEFAULT_GEN_MODELS).split(",") if m.strip()]
EVAL_MODELS = [m.strip() for m in os.getenv("GEMINI_EVAL_MODELS", DEFAULT_EVAL_MODELS).split(",") if m.strip()]
MIN_INTERVAL_PER_MODEL = 6.5  # ~9 req/min por modelo (limite free: 10/min)


class GeminiRotator:
    """Distribui chamadas entre modelos Gemini respeitando as quotas."""

    def __init__(self, models):
        api_key = os.environ["GOOGLE_API_KEY"]
        self._models = models
        self._llms = {
            model: ChatGoogleGenerativeAI(
                model=model, temperature=0, google_api_key=api_key, max_retries=1
            )
            for model in models
        }
        self._exhausted = set()
        self._last_call = {model: 0.0 for model in models}

    def _next_model(self) -> str:
        # Prioridade: sempre o primeiro modelo da lista que ainda tem quota
        alive = [m for m in self._models if m not in self._exhausted]
        if not alive:
            raise RuntimeError(
                "Quota diária esgotada em todos os modelos Gemini configurados. "
                "Tente novamente após o reset (meia-noite, horário do Pacífico)."
            )
        return alive[0]

    def invoke(self, messages):
        for _ in range(12):
            model = self._next_model()
            wait = MIN_INTERVAL_PER_MODEL - (time.monotonic() - self._last_call[model])
            if wait > 0:
                time.sleep(wait)
            try:
                result = self._llms[model].invoke(messages)
                self._last_call[model] = time.monotonic()
                return result
            except Exception as e:
                self._last_call[model] = time.monotonic()
                message = str(e)
                is_quota = (
                    "429" in message
                    or "ResourceExhausted" in message
                    or "RESOURCE_EXHAUSTED" in message
                )
                if not is_quota:
                    raise
                if "PerDay" in message:
                    print(f"      ⚠️  {model}: quota diária esgotada, alternando de modelo")
                    self._exhausted.add(model)
                    continue
                delay = 10.0
                match = re.search(r"retry in (\d+(?:\.\d+)?)", message) or re.search(
                    r"seconds: (\d+)", message
                )
                if match:
                    delay = float(match.group(1)) + 1
                print(f"      ⏳ {model}: limite por minuto, aguardando {delay:.0f}s")
                time.sleep(min(delay, 65))
        raise RuntimeError("Chamada ao Gemini falhou após várias tentativas de rotação")


_rotators = {}


def _get_rotating_llm(pool: str, models):
    if pool not in _rotators:
        _rotators[pool] = GeminiRotator(models)
    rotator = _rotators[pool]
    return RunnableLambda(lambda value: rotator.invoke(value))


# O patch precisa acontecer ANTES de importar evaluate/metrics, pois ambos
# fazem `from utils import get_llm/get_eval_llm` no topo do módulo.
# As assinaturas espelham utils.get_llm/get_eval_llm; a rotação ignora os args.
import utils  # noqa: E402

utils.get_llm = lambda model=None, temperature=0.0: _get_rotating_llm("gen", GEN_MODELS)
utils.get_eval_llm = lambda temperature=0.0: _get_rotating_llm("eval", EVAL_MODELS)

import evaluate  # noqa: E402


if __name__ == "__main__":
    sys.exit(evaluate.main())
