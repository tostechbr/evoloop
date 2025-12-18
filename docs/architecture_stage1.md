# Arquitetura do Framework EvoLoop (Estágio 1)

Este documento descreve a arquitetura técnica do EvoLoop, baseada nos conceitos do artigo "LLM Evals: Everything You Need to Know" de Hamel Husain.

---

## Visão Geral

O framework é dividido em **4 módulos** que representam o ciclo completo de avaliação:

```
┌─────────────────────────────────────────────────────────────────┐
│                         EVOLOOP                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. TRACKER          2. STORAGE          3. JUDGE              │
│   (Captura)           (Armazenamento)     (Avaliação)           │
│                                                                 │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐           │
│   │@monitor │ ──────► │ SQLite  │ ──────► │ Binary  │           │
│   │Decorator│         │ Local   │         │ Judge   │           │
│   └─────────┘         └─────────┘         └─────────┘           │
│                                                  │              │
│                                                  ▼              │
│                                           4. REPORTER           │
│                                           (Visualização)        │
│                                                                 │
│                                           ┌─────────┐           │
│                                           │ Console │           │
│                                           │ Report  │           │
│                                           └─────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Módulos

### Módulo 1: TRACKER (Captura de Traces)

**Conceito Base:** *"Um trace é o registro completo de todas as ações, mensagens, chamadas de ferramentas e recuperação de dados desde a consulta inicial do usuário até a resposta final."*

**Responsabilidades:**
- Interceptar a execução do agente sem alterar seu comportamento.
- Capturar: Input do usuário, Output do agente, Contexto (dados de APIs), Timestamp, Metadados.

**Interface:** Decorador `@monitor` aplicado na função principal do agente.

---

### Módulo 2: STORAGE (Armazenamento Local)

**Conceito Base:** Os dados precisam estar persistidos e acessíveis para análise posterior.

**Responsabilidades:**
- Persistir os traces capturados em formato consultável.
- Permitir consultas simples (ex: "todos os traces de hoje").

**Implementação:** SQLite local (arquivo único, zero configuração).

---

### Módulo 3: JUDGE (Avaliação Binária)

**Conceito Base:** *"Avaliações binárias forçam um pensamento mais claro. Escalas Likert (1-5) introduzem desafios significativos."*

**Responsabilidades:**
- Receber um Trace e um Critério de Avaliação.
- Retornar veredito estruturado: `{ passed: bool, reason: str, error_category: str }`.

**Filosofia:**
- O juiz SEMPRE explica o raciocínio (Chain of Thought).
- Critério definido em linguagem natural.
- Classificação de erro obrigatória para falhas.

**Tipos:**
1. **LLM Judge:** Usa modelo de linguagem para avaliação subjetiva.
2. **Code Judge:** Usa código Python para verificações objetivas.

---

### Módulo 4: REPORTER (Visualização e Análise)

**Conceito Base:** *"Error analysis é A ATIVIDADE MAIS IMPORTANTE em evals."*

**Responsabilidades:**
- Ler resultados das avaliações.
- Agrupar falhas por `error_category`.
- Exibir relatório claro no terminal.

---

## Estrutura de Pastas

```
evoloop/
├── src/
│   └── evoloop/
│       ├── __init__.py         # Exporta: monitor, Judge, run_eval
│       ├── tracker.py          # Módulo 1: Decorador @monitor
│       ├── storage.py          # Módulo 2: Classe SQLiteStorage
│       ├── judge.py            # Módulo 3: Classes BinaryJudge, CodeJudge
│       ├── reporter.py         # Módulo 4: Geração de relatórios
│       └── types.py            # Dataclasses: Trace, EvalResult, Criteria
├── tests/
│   ├── test_tracker.py
│   ├── test_storage.py
│   ├── test_judge.py
│   └── test_reporter.py
├── examples/
│   ├── simple_qa_agent.py      # Exemplo: agente de perguntas e respostas
│   └── run_evaluation.py       # Exemplo: script de avaliação batch
├── pyproject.toml
└── README.md
```

---

## Fluxo de Dados

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   AGENTE     │     │   STORAGE    │     │    JUDGE     │     │   REPORTER   │
│  do Usuário  │     │   (SQLite)   │     │   (Binary)   │     │  (Console)   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  1. @monitor       │                    │                    │
       │  intercepta        │                    │                    │
       │  input/output      │                    │                    │
       ├───────────────────►│                    │                    │
       │                    │  2. Trace salvo    │                    │
       │                    │  no banco local    │                    │
       │                    │                    │                    │
       │                    │  3. Script batch   │                    │
       │                    │  lê os traces      │                    │
       │                    ├───────────────────►│                    │
       │                    │                    │  4. Aplica         │
       │                    │                    │  critérios         │
       │                    │                    │  do usuário        │
       │                    │                    │                    │
       │                    │                    │  5. Gera           │
       │                    │                    │  EvalResults       │
       │                    │                    ├───────────────────►│
       │                    │                    │                    │  6. Agrupa
       │                    │                    │                    │  por categoria
       │                    │                    │                    │
       │                    │                    │                    │  7. Exibe
       │                    │                    │                    │  relatório
       │                    │                    │                    │
```

---

## Roadmap de Implementação

### Fase 1: Fundação (MVP)
- [ ] **1.1** Criar estrutura do projeto (`pyproject.toml`, pastas, `__init__.py`)
- [ ] **1.2** Implementar `types.py` (Dataclasses: `Trace`, `EvalResult`, `Criteria`)
- [ ] **1.3** Implementar `storage.py` (SQLiteStorage: save, load, query)
- [ ] **1.4** Implementar `tracker.py` (Decorador `@monitor`)
- [ ] **1.5** Criar exemplo `simple_qa_agent.py` para validar captura

### Fase 2: O Juiz
- [ ] **2.1** Implementar `judge.py` com `BinaryJudge` (usando LLM)
- [ ] **2.2** Adicionar suporte a `CodeJudge` (assertions em Python)
- [ ] **2.3** Criar testes unitários para os juízes

### Fase 3: Relatórios
- [ ] **3.1** Implementar `reporter.py` (agregação por `error_category`)
- [ ] **3.2** Criar saída formatada no terminal (usando `rich` ou similar)
- [ ] **3.3** Criar exemplo `run_evaluation.py` para demonstrar fluxo completo

### Fase 4: CLI e Distribuição
- [ ] **4.1** Criar CLI com comandos: `evoloop init`, `evoloop eval`, `evoloop report`
- [ ] **4.2** Finalizar `pyproject.toml` para publicação no PyPI
- [ ] **4.3** Escrever documentação no `README.md`

### Fase 5: Extensões (Futuro)
- [ ] **5.1** Adaptadores de Storage (PostgreSQL, S3)
- [ ] **5.2** Dashboard web para visualização
- [ ] **5.3** Integração com LangSmith, Langfuse, etc.
- [ ] **5.4** Auto-sugestão de melhorias no prompt (Self-Evolving)

---

## Dependências Externas (Mínimas)

| Pacote      | Uso                                      |
|-------------|------------------------------------------|
| `pydantic`  | Validação de dados (Trace, EvalResult)   |
| `litellm`   | Abstração para chamadas de LLM (Judge)   |
| `rich`      | Formatação de relatórios no terminal     |

---

## Critérios de Sucesso do MVP

1. **Instalação simples:** `pip install evoloop`
2. **Integração em 1 linha:** Adicionar `@monitor` na função do agente.
3. **Avaliação batch funcional:** Rodar `evoloop eval` e ver relatório de erros.
4. **Relatório útil:** Taxonomia de erros clara com contagem e exemplos.
