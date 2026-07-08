"""
Script auxiliar para avaliar o prompt ORIGINAL (v1) do Hub.

Reutiliza toda a lógica de src/evaluate.py, apenas apontando para o prompt
leonanluppi/bug_to_user_story_v1 — usado para gerar a tabela comparativa
v1 vs v2 do README. Não altera o fluxo oficial de avaliação.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Opcional: rotação de modelos Gemini p/ contornar quota free de 20 req/dia
# (precisa ser importado ANTES de evaluate)
if os.getenv("USE_GEMINI_ROTATION", "").lower() in ("1", "true", "yes"):
    import evaluate_rotating  # noqa: F401

from langsmith import Client

from evaluate import (
    create_evaluation_dataset,
    evaluate_prompt,
    display_results,
)
from utils import check_env_vars, print_section_header

load_dotenv()


def main():
    print_section_header("📊 Avaliação do prompt ORIGINAL (v1)")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    client = Client()
    project_name = os.getenv("LANGCHAIN_PROJECT", "prompt-optimization-challenge-resolved")
    dataset_name = f"{project_name}-eval"

    create_evaluation_dataset(client, dataset_name, "datasets/bug_to_user_story.jsonl")

    scores = evaluate_prompt("leonanluppi/bug_to_user_story_v1", dataset_name, client)
    display_results("leonanluppi/bug_to_user_story_v1", scores)
    return 0


if __name__ == "__main__":
    sys.exit(main())
