# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Resolução do desafio de Prompt Engineering do MBA: fazer pull do prompt de baixa qualidade `leonanluppi/bug_to_user_story_v1` do LangSmith Prompt Hub, refatorá-lo com técnicas avançadas de Prompt Engineering, publicar a versão otimizada (`bug_to_user_story_v2`) e iterar até que todas as métricas de avaliação (Helpfulness, Correctness, F1-Score, Clarity e Precision) atinjam a nota mínima.

---

## Técnicas Aplicadas (Fase 2)

O prompt original (v1) era genérico: um system prompt de duas frases ("Você é um assistente que ajuda a transformar relatos de bugs...") sem formato definido, sem exemplos, sem regras e com a variável `{bug_report}` duplicada no system e no user prompt. O v2 (`prompts/bug_to_user_story_v2.yml`) foi reescrito do zero com 4 técnicas:

### 1. Few-shot Learning (obrigatória)

**Por quê:** o dataset de referência tem um formato muito específico ("Como um..., eu quero..., para que..." + Critérios de Aceitação em Dado/Quando/Então, com seções extras para bugs técnicos). Descrever esse formato em palavras não basta — exemplos concretos de entrada/saída ancoram o modelo no estilo, tom e granularidade esperados, elevando diretamente o F1-Score e a Precision.

**Como apliquei:** a seção `## Exemplos` do system prompt traz 3 pares completos de entrada/saída, cobrindo os três perfis de bug do dataset:
- **Exemplo 1** — bug simples (link de recuperação de senha): story concisa + 5 critérios;
- **Exemplo 2** — bug médio com detalhes técnicos (HTTP 413 no upload): story + critérios + seção "Contexto Técnico:";
- **Exemplo 3** — bug de segurança: story com ator "o sistema" + "Critérios Adicionais para Diretores:" + "Contexto de Segurança:" com categoria OWASP.

### 2. Role Prompting

**Por quê:** a persona correta muda o vocabulário e o foco da resposta. Um "assistente" genérico descreve o defeito; um Product Manager escreve o comportamento desejado com valor de negócio e critérios verificáveis — exatamente o que as referências fazem.

**Como apliquei:** primeira linha do system prompt:

> "Você é um Product Manager sênior, especialista em metodologias ágeis e em transformar relatos de bugs em User Stories claras, precisas e acionáveis para times de desenvolvimento."

### 3. Chain of Thought (CoT)

**Por quê:** converter bug em user story exige raciocínio em etapas: identificar o ator, inverter o defeito em comportamento esperado, extrair o valor de negócio e derivar critérios verificáveis. Sem esse roteiro, o modelo tende a parafrasear o bug. O CoT também trata edge cases no ponto certo (ex: bug de backend sem usuário final → ator "o sistema").

**Como apliquei:** seção `## Processo de Raciocínio (pense passo a passo, internamente)` com 5 etapas (ATOR → COMPORTAMENTO ESPERADO → VALOR → CRITÉRIOS → DETALHES TÉCNICOS), com a instrução de raciocinar internamente sem expor a análise — mantendo a resposta limpa (o que protege Clarity e Precision).

### 4. Skeleton of Thought

**Por quê:** as métricas F1 e Precision comparam a resposta com referências cuja **profundidade escala com a complexidade do bug** (simples → story curta; médio → seções técnicas; complexo → documento estruturado). Um esqueleto fixo de resposta + regras de proporcionalidade evita tanto respostas rasas (recall baixo) quanto verbosidade inventada (precision baixa).

**Como apliquei:** seções `## Formato Obrigatório da Resposta` (esqueleto da story + critérios) e `## Proporcionalidade`, que definem quais seções usar em cada nível de complexidade ("Contexto Técnico:", "Critérios Técnicos:", "Contexto de Segurança:", "Exemplo de Cálculo:", e o formato `=== SEÇÕES ===` para bugs complexos).

### Tratamento de edge cases e regras explícitas

A seção `## Regras de Comportamento` cobre os casos-limite exigidos pelo desafio: relato vago (story genérica sem inventar detalhes), múltiplos bugs (agrupar critérios por problema), bugs de segurança (severidade + OWASP), proibição de alucinação ("use SOMENTE informações presentes no relato") e proibição de texto fora do formato.

### System vs User Prompt

Todo o comportamento (persona, regras, formato, exemplos) vive no **system prompt**; o **user prompt** contém apenas a tarefa e o `{bug_report}` delimitado — corrigindo o v1, que duplicava a variável nos dois papéis.

---

## Resultados Finais

### Tabela comparativa: v1 (original) vs v2 (otimizado)

| Métrica | v1 (`leonanluppi/bug_to_user_story_v1`) | v2 (`bug_to_user_story_v2`) | Status v2 |
|---|---|---|---|
| Helpfulness | _pendente*_ | 0.92 | ✅ |
| Correctness | _pendente*_ | 0.92 | ✅ |
| F1-Score | _pendente*_ | 0.91 | ✅ |
| Clarity | _pendente*_ | 0.92 | ✅ |
| Precision | _pendente*_ | 0.93 | ✅ |
| **Média** | _pendente*_ | **0.9197** | ✅ APROVADO |

> \* A primeira medição do v1 foi descartada por inconsistência de judge: com a quota diária do `gemini-2.5-flash` esgotada, o julgamento caiu em um modelo mais leniente, inflando as notas do v1 — comparação inválida com o v2 (julgado pelo `gemini-2.5-flash`). A medição do v1 será refeita com o mesmo perfil de judges (`USE_GEMINI_ROTATION=1 python src/evaluate_v1.py`, com quota renovada).

> Avaliação executada com `LLM_PROVIDER=google` (`gemini-2.5-flash` para geração e avaliação), sobre os 10 primeiros exemplos do dataset `datasets/bug_to_user_story.jsonl` (LLM-as-Judge, prompts de julgamento em `src/metrics.py`).

### Evidências no LangSmith

- **Prompt otimizado no Hub:** `maxsuelgomes11/bug_to_user_story_v2`
- **Dataset de avaliação:** `prompt-optimization-challenge-resolved-eval` (15 exemplos)
- **Tracing:** com `LANGSMITH_TRACING=true`, todas as execuções da avaliação ficam rastreadas no projeto do LangSmith (geração + chamadas do judge por exemplo)
- **Link público do dashboard:** _[cole aqui o link público do seu dashboard]_
- **Screenshots:** _[cole aqui os screenshots das avaliações com notas ≥ 0.8]_

---

## Como Executar

### Pré-requisitos

- Python 3.9+
- Conta no [LangSmith](https://smith.langchain.com) (API Key)
- API Key da [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini, gratuito) **ou** da [OpenAI](https://platform.openai.com/api-keys)

### 1. Instalação

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuração

```bash
cp .env.example .env
```

Preencha no `.env`:

- `LANGSMITH_API_KEY` — sua chave do LangSmith
- `USERNAME_LANGSMITH_HUB` — seu handle do Hub (crie publicando qualquer prompt em https://smith.langchain.com/prompts)
- `GOOGLE_API_KEY` (com `LLM_PROVIDER=google`) ou `OPENAI_API_KEY` (com `LLM_PROVIDER=openai`)

### 3. Pull do prompt original (v1)

```bash
python src/pull_prompts.py
```

Baixa `leonanluppi/bug_to_user_story_v1` do Hub e salva em `prompts/bug_to_user_story_v1.yml`.

### 4. Push do prompt otimizado (v2)

```bash
python src/push_prompts.py
```

Valida `prompts/bug_to_user_story_v2.yml` e publica no Hub como `{seu_username}/bug_to_user_story_v2` (público; se sua conta ainda não tiver handle do Hub, o push é feito privado e o script indica como criar o handle).

### 5. Avaliação

```bash
python src/evaluate.py
```

Cria/reutiliza o dataset de avaliação no LangSmith, roda o prompt v2 nos exemplos e calcula as 5 métricas. Para gerar a linha "v1" da tabela comparativa:

```bash
python src/evaluate_v1.py
```

> **Nota (Gemini free tier):** cada avaliação faz ~40 chamadas ao modelo (10 gerações + 30 julgamentos). Dependendo do projeto Google, a quota gratuita pode ser de apenas **20 requisições/dia por modelo** — insuficiente para uma avaliação completa. Para esse caso existe o runner alternativo:
>
> ```bash
> python src/evaluate_rotating.py
> ```
>
> Ele executa o mesmo fluxo de `src/evaluate.py` (sem alterá-lo), distribuindo as chamadas entre vários modelos Gemini (`gemini-flash-latest`, `gemini-flash-lite-latest`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`) com throttling por modelo e troca automática quando a quota diária de um modelo esgota.

### 6. Testes de validação

```bash
pytest tests/test_prompts.py -v
```

---

## Processo de Iteração

Foram 4 iterações até a aprovação. Em cada uma, o `reasoning` retornado pelos judges (visível também no tracing do LangSmith) apontou o padrão de erro a corrigir:

| Iteração | Mudança no prompt | Resultado | Aprendizado |
|---|---|---|---|
| 1 | Reescrita completa: Few-shot + Role + CoT + Skeleton | F1 0.73 | As referências incluem critérios complementares (feedback visual, contadores, paridade entre navegadores) que a resposta não trazia |
| 2 | Critérios complementares obrigatórios | F1 0.85+ nos bugs simples; queda no bug de dashboard | Judges penalizam números literais do relato usados como regra nos critérios ("deve mostrar 42") |
| 3 | Números do relato só em seções de contexto; regra de negócio genérica nos critérios | Média 0.8836 — reprovado por pouco | O recall caía nos bugs complexos: as referências contêm **enriquecimento de PM além do relato** ("Critérios de Prevenção", "Critérios de Acessibilidade", critérios técnicos granulares) que a regra anti-alucinação estava bloqueando |
| 4 | Cobertura exaustiva linha a linha; boas práticas de mercado permitidas (prevenção, acessibilidade); ator "o sistema" para bugs server-side; granularidade técnica nos complexos | **Média 0.9197 — APROVADO** ✅ | Especificar o comportamento ideal (como um PM faria), não apenas o conserto do defeito |

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt original (pull do Hub)
│   └── bug_to_user_story_v2.yml  # Prompt otimizado (este trabalho)
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 bugs com referências (não alterar)
├── src/
│   ├── pull_prompts.py           # Pull do Hub (implementado)
│   ├── push_prompts.py           # Push ao Hub com validação (implementado)
│   ├── evaluate.py               # Avaliação automática (pronto, não alterado)
│   ├── evaluate_v1.py            # Avaliação do v1 p/ tabela comparativa (extra)
│   ├── metrics.py                # Métricas LLM-as-Judge (pronto, não alterado)
│   └── utils.py                  # Helpers (pronto, não alterado)
└── tests/
    └── test_prompts.py           # 6 testes de validação (implementados)
```
