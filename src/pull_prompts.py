"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt do LangSmith Hub e salva localmente.
    
    Returns:
        0 se sucesso, 1 se erro
    """
    print_section_header("🔄 Pull de Prompts do LangSmith Hub")
    
    # Verificar variáveis de ambiente obrigatórias
    required_vars = ['LANGSMITH_API_KEY']
    if not check_env_vars(required_vars):
        return 1
    
    # Pull do prompt público do leonanluppi
    hub_path = "leonanluppi/bug_to_user_story_v1"
    prompt_name = 'bug_to_user_story_v1'
    
    print(f"📥 Fazendo pull do prompt: {hub_path}")
    
    try:
        # Pull do prompt usando langchain hub
        prompt = hub.pull(hub_path)
        
        print(f"✓ Prompt baixado com sucesso!")
        print(f"  Tipo: {type(prompt).__name__}")
        
        # Serializar o prompt em um formato legível, extraindo o template
        # de cada mensagem (a serialização nativa .dict() perde os textos)
        prompt_dict = {
            'description': 'Prompt para converter relatos de bugs em User Stories',
            'system_prompt': '',
            'user_prompt': '{bug_report}',
            'version': 'v1',
            'tags': ['bug-analysis', 'user-story', 'product-management'],
            'metadata': getattr(prompt, 'metadata', None),
            'input_variables': getattr(prompt, 'input_variables', []),
        }

        if hasattr(prompt, 'messages'):
            for msg in prompt.messages:
                if hasattr(msg, 'prompt') and hasattr(msg.prompt, 'template'):
                    if 'system' in str(type(msg)).lower():
                        prompt_dict['system_prompt'] = msg.prompt.template
                    else:
                        prompt_dict['user_prompt'] = msg.prompt.template
        elif hasattr(prompt, 'template'):
            prompt_dict['system_prompt'] = prompt.template
        
        # Preparar estrutura para salvar
        data_to_save = {
            prompt_name: prompt_dict
        }
        
        # Caminho para salvar
        output_path = Path('prompts') / f'{prompt_name}.yml'
        
        # Salvar YAML
        print(f"💾 Salvando prompt em: {output_path}")
        if save_yaml(data_to_save, str(output_path)):
            print(f"✓ Prompt salvo com sucesso em {output_path}")
            return 0
        else:
            print(f"❌ Erro ao salvar prompt")
            return 1
            
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        print(f"   Verifique se o prompt {hub_path} existe no LangSmith Hub")
        return 1


def main():
    """Função principal"""
    return pull_prompts_from_langsmith()


if __name__ == "__main__":
    sys.exit(main())
