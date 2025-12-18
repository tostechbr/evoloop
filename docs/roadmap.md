# Roadmap

## Phase 1: The Foundation (MVP)
- [ ] **Project Structure**: Setup `pyproject.toml`, `src/`, and basic CI/CD.
- [ ] **Basic Judge**: Implement a simple `LLMJudge` that uses OpenAI/Anthropic to score outputs based on natural language criteria.
- [ ] **Feedback Object**: Define a standard Pydantic model for `EvaluationResult`.

## Phase 2: Optimization Loop
- [ ] **PromptOptimizer**: Create a class that takes a prompt + feedback and generates a better prompt.
- [ ] **Optimization Strategies**: Implement "Critique & Refine" strategy.

## Phase 3: Memory & Few-Shotting
- [ ] **SkillStore**: Implement a local JSON/Vector store for saving examples.
- [ ] **Retrieval**: Add logic to fetch relevant examples based on query similarity.

## Phase 4: Advanced Features
- [ ] **Dashboard**: A simple CLI or Streamlit view to see the evolution of scores over time.
- [ ] **Integrations**: Helper wrappers for LangChain/LangGraph (optional, but helpful).
