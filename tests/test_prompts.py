"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPTS_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def prompt_data():
    """Carrega os dados do prompt v2."""
    prompts = load_prompts(str(PROMPTS_FILE))
    assert "bug_to_user_story_v2" in prompts, "Chave 'bug_to_user_story_v2' não encontrada no YAML"
    return prompts["bug_to_user_story_v2"]

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não existe"
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "você é um" in system_prompt, "Prompt não define uma persona ('Você é um...')"
        assert "product manager" in system_prompt, "Persona esperada (Product Manager) não encontrada"

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"].lower()
        has_user_story_format = (
            "como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
            and "critérios de aceitação" in system_prompt
        )
        has_markdown = "markdown" in system_prompt
        assert has_user_story_format or has_markdown, (
            "Prompt não exige formato Markdown nem o formato padrão de User Story"
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"].lower()
        assert "exemplo" in system_prompt, "Prompt não contém exemplos (Few-shot)"
        assert "relato de bug" in system_prompt, "Exemplos não mostram a entrada (relato de bug)"
        assert "resposta" in system_prompt, "Exemplos não mostram a saída (resposta esperada)"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        yaml_text = PROMPTS_FILE.read_text(encoding="utf-8")
        assert "TODO" not in yaml_text, "Existe um [TODO] esquecido no arquivo de prompts"
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list)
        assert len(techniques) >= 2, (
            f"Esperado pelo menos 2 técnicas em 'techniques_applied', encontrado {len(techniques)}"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
