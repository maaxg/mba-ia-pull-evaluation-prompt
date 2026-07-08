"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPTS_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    prompt_object = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])

    tags = list(prompt_data.get("tags", []))
    techniques = list(prompt_data.get("techniques_applied", []))

    for is_public in (True, False):
        try:
            url = client.push_prompt(
                prompt_name,
                object=prompt_object,
                description=prompt_data.get("description", ""),
                tags=tags + techniques,
                is_public=is_public,
            )
            username = os.getenv("USERNAME_LANGSMITH_HUB", "")
            visibility = "público" if is_public else "PRIVADO"
            print(f"✓ Push realizado com sucesso ({visibility}): {username}/{prompt_name}")
            print(f"  URL: {url}")
            return True
        except Exception as e:
            # O Hub rejeita commits idênticos ao último — não é um erro real
            if "Nothing to commit" in str(e):
                print(f"✓ Prompt {prompt_name} já está atualizado no Hub (nada a commitar)")
                return True
            # Publicar exige um handle do Hub; sem ele, faz push privado
            if is_public and "Hub handle" in str(e):
                print("⚠️  Sua conta ainda não tem um handle público no LangChain Hub.")
                print("   Crie um em https://smith.langchain.com/prompts e rode este script")
                print("   novamente para tornar o prompt público. Fazendo push PRIVADO...")
                continue
            print(f"❌ Erro ao fazer push do prompt {prompt_name}: {e}")
            return False
    return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    user_prompt = prompt_data.get("user_prompt", "")
    if not user_prompt:
        errors.append("Campo obrigatório ausente ou vazio: user_prompt")
    elif "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("🚀 Push de Prompts Otimizados ao LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    prompts = load_yaml(str(PROMPTS_FILE))
    if not prompts:
        print(f"❌ Não foi possível carregar {PROMPTS_FILE}")
        return 1

    exit_code = 0
    for prompt_name, prompt_data in prompts.items():
        print(f"\n📋 Validando prompt: {prompt_name}")
        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print(f"❌ Prompt inválido:")
            for error in errors:
                print(f"   - {error}")
            exit_code = 1
            continue

        print(f"✓ Estrutura válida")
        print(f"📤 Enviando ao LangSmith Hub...")
        if not push_prompt_to_langsmith(prompt_name, prompt_data):
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
