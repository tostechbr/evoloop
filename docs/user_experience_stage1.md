# Experiência do Desenvolvedor (DX) - EvoLoop (Estágio 1)

Este documento descreve a jornada do usuário ao utilizar o framework EvoLoop em sua primeira versão. O foco é oferecer uma integração invisível na execução e poderosa na análise.

## 1. A Instalação (Zero Atrito)
O desenvolvedor está em seu projeto atual. Não é necessário mudar de banco de dados, subir containers Docker pesados, nem realizar cadastros complexos em plataformas SaaS.

*   **Ação:** O desenvolvedor abre o terminal e roda um comando padrão de instalação Python.
*   **Resultado:** A biblioteca é baixada. Ela é leve e nenhuma configuração extra é exigida neste momento.

## 2. A Integração (O "Adesivo" Universal)
O desenvolvedor possui uma função principal em seu código que atua como o "cérebro" do agente (a função que recebe a mensagem do usuário e devolve a resposta).

*   **O Problema:** O desenvolvedor não quer reescrever essa função ou poluí-la com `logs` e `prints`.
*   **A Solução EvoLoop:** Importação de um **"decorador"** (`@monitor`).
*   **A Experiência:** O desenvolvedor "cola" esse decorador acima da função do agente.
    *   *Compatibilidade:* Funciona com LangChain, AutoGen, CrewAI, ou scripts simples.
    *   *Configuração:* Define-se apenas o destino, ex: `save_to="local_db"`.

**Sensação:** "Simples e direto. Já está monitorando."

## 3. O Tempo de Execução (A Caixa Preta Silenciosa)
O agente é colocado em execução. O desenvolvedor ou seus clientes interagem com ele.

*   **O que muda:** Nada. O agente não sofre impacto de performance. O usuário final não percebe alterações.
*   **Bastidores:** Cada interação (pergunta, resposta e dados de contexto, como consultas de API) é interceptada silenciosamente e salva em um arquivo local (SQLite), funcionando como uma "Caixa Preta".
*   **Segurança:** Os dados permanecem locais na máquina do desenvolvedor, sem envio para a nuvem nesta etapa.

## 4. A Definição das Regras (O Contrato do Juiz)
Para avaliar a performance, o EvoLoop precisa de critérios claros.

*   **Ação:** O desenvolvedor cria um pequeno arquivo de configuração.
*   **A Experiência:** Escrita de regras de negócio em linguagem natural (Português ou Inglês).
    *   *Exemplo 1:* "O agente nunca deve ser rude."
    *   *Exemplo 2:* "Se o cliente deve mais de R$ 1.000, o agente não pode dar isenção de juros."
    *   *Exemplo 3:* "A resposta deve ter no máximo 2 parágrafos."

## 5. A Análise (O Relatório do Dia Seguinte)
Ao final de um período de testes ou operação.

*   **Ação:** O desenvolvedor executa um comando do EvoLoop no terminal, ex: `evoloop avaliar`.
*   **O Processo:** O framework processa as conversas salvas na "Caixa Preta", aplica as "Regras" definidas e utiliza um LLM (o Juiz) para avaliar as interações.
*   **O Resultado Visual:**
    *   Barra de progresso no terminal.
    *   Resumo colorido: **"15 interações. 12 Aprovadas. 3 Reprovadas."**
    *   Detalhamento das falhas: *"Na conversa #4, o agente ofereceu isenção de juros, mas a dívida era de R$ 1.500 (Violação da Regra 2)."*

## 6. A Evolução (O Futuro)
O fechamento do ciclo de feedback.

*   **Ação:** O EvoLoop identifica padrões de erro (ex: falhas recorrentes na "Regra 2").
*   **Sugestão:** O framework propõe melhorias no System Prompt para corrigir o comportamento, ex: *"Seu System Prompt atual está confuso sobre juros. Sugiro alterar a linha X para: 'ATENÇÃO: Dívidas > 1k não têm isenção'."*
