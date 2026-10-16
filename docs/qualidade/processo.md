# Processo SDD e Normas de Qualidade de Processo — RemindMe

Issue #84. A qualidade do **produto** (ISO/IEC 9126 / 25010) é norma de referência e não se certifica; as características do produto estão nas avaliações de #48, #52, #58, #61, #62 e #63. A qualidade do **processo** pode ser certificada: ISO 9001 (sistema de gestão da qualidade), ISO/IEC 12207 (ciclo de vida de software) e CMMI (níveis de maturidade de 1 a 5). Este documento mostra como o processo Spec-Driven Development (SDD) do projeto se relaciona a essas práticas.

- **Data:** 2026-10-16.
- **Natureza:** autoavaliação para fins de estudo. O projeto não pretende nem tem certificação, e nada aqui é um parecer de conformidade nem uma avaliação formal (no CMMI, o equivalente seria um appraisal conduzido por avaliador credenciado).
- **Fontes no projeto:** [`CLAUDE.md`](../../CLAUDE.md) (fluxo de trabalho obrigatório), [`combinados.md`](../combinados.md), [`testes.md`](../testes.md), [`.specify/`](../../.specify/README.md).
- **Relacionadas:** #60 (critérios de qualidade), #72 (relatório de qualidade). O resumo está na seção 8 do [relatório](relatorio-de-qualidade.md).

## 1. Etapas do fluxo SDD e processos da ISO/IEC 12207

Nomes dos processos conforme a ISO/IEC/IEEE 12207:2017 (alinhada à ISO/IEC/IEEE 15288). Os nomes de processos da edição de 2008 estão entre parênteses, quando diferem.

| Etapa do fluxo SDD (CLAUDE.md) | Processos da ISO/IEC 12207 | Como o projeto faz | Evidência |
|---|---|---|---|
| 1. **Mapa de specs**: decompor o trabalho e parar | Planejamento do projeto (*Project Planning*); definição de arquitetura (*Architecture Definition*) | O mapa decompõe o produto em specs numeradas, com dependências e ordem | [`mapa-de-specs.md`](../../.specify/specs/mapa-de-specs.md), [`arquitetura.md`](../arquitetura.md), ADRs |
| 2. **Revisão humana** do mapa | Avaliação e controle do projeto (*Project Assessment and Control*); revisão (*Review*, 2008) | A equipe revisa a decomposição antes de qualquer spec | Regra 3 do fluxo: "Uma spec por vez"; PR do mapa |
| 3. **Spec**, pelo modelo | Definição dos requisitos do software (*System/Software Requirements Definition*; em 2008, *Software Requirements Analysis*); definição do projeto (*Design Definition*) | Cada spec traz critérios de aceite Dado, Quando, Então, rastreados a RF, RB e UC | [`modelo-de-spec.md`](../../.specify/specs/modelo-de-spec.md), [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), [`requisitos.md`](../requisitos.md) |
| 4. **Aprovação humana** da spec | Gestão de decisão (*Decision Management*); validação (*Validation*), no que diz respeito à intenção do cliente | Aprovação registrada na própria spec; sem spec Aprovada, não há código (regra 1) | Situação "Aprovada" na Spec 006 |
| 5. **Implementação** em novo contexto | Implementação (*Implementation*; em 2008, *Software Construction*); integração (*Integration*) | Código mínimo para os critérios de aceite, em camadas, com domínio isolado | `src/remindme/`, ADR-001, [plano da Spec 006](../../.specify/plans/006-plano.md) |
| 6. **Verificação** e registro na seção 8 da spec | Verificação (*Verification*); garantia da qualidade (*Quality Assurance*); teste de qualificação (2008) | Teste por critério, com o identificador no nome; matriz spec → teste → resultado | [`matriz-criterios-de-aceite.md`](matriz-criterios-de-aceite.md), `tests/` |

Processos que atravessam todas as etapas:

| Processo da ISO/IEC 12207 | Prática no projeto | Evidência |
|---|---|---|
| Gestão de configuração (*Configuration Management*) | Git; branch por issue; PR pequeno com `Closes #N`; identificadores nunca reaproveitados (regra 7); spec e código no mesmo PR (regra 5) | [`combinados.md`](../combinados.md), [`CLAUDE.md`](../../CLAUDE.md) |
| Gestão da informação / documentação (*Information Management*; em 2008, *Documentation Management*) | Baseline em `docs/` como fonte de verdade; glossário obrigatório; diagramas com fonte Mermaid | [`docs/README.md`](../README.md), [`glossario.md`](../glossario.md) |
| Gestão de riscos (*Risk Management*) | Decisão ausente vira `OPEN-nn` em vez de ser preenchida (regra 2); 26 questões registradas | [`.specify/open.md`](../../.specify/open.md) |
| Gestão de decisão (*Decision Management*) | ADRs para decisões caras de reverter | [`adr/`](../adr/README.md) |
| Garantia da qualidade (*Quality Assurance*) | Revisão por colega no PR; checklist de revisão de código; rodada de qualidade | [`revisao-de-codigo.md`](revisao-de-codigo.md), [`relatorio-de-qualidade.md`](relatorio-de-qualidade.md) |
| Resolução de problemas (*Problem Resolution*, 2008) | Registro de defeitos com evidência, correção e nova execução | [`defeitos.md`](defeitos.md) |
| Medição (*Measurement*) | Métricas de código, testes e desempenho | Seção 4 do [relatório](relatorio-de-qualidade.md) |

**Lacunas em relação à 12207:** não há processos de **transição**, **operação** e **manutenção** em produção, porque o produto não é implantado (OPEN-12); a **validação** com usuários reais não existe (só personas, [`personas.md`](../personas.md)); e não há **gestão de acordos** (aquisição e fornecimento), porque não há fornecedor.

## 2. Práticas da ISO 9001 presentes no projeto

Cláusulas conforme a ISO 9001:2015. A ISO 9001 certifica uma **organização**, e este é um projeto acadêmico de três pessoas: a tabela mostra práticas semelhantes às exigidas, e não conformidade.

| Prática (cláusula) | Presente? | Evidência |
|---|---|---|
| **Rastreabilidade** (8.5.2, identificação e rastreabilidade) | Sim | Identificadores `RF`, `RNF`, `RB`, `UC`, `DA`, `DT`, `ADR`, `OPEN`; cadeia cláusula → issue → PR → commits → teste ([`testes.md`](../testes.md), "Rastreabilidade"); cada teste leva o identificador no nome; [matriz de critérios](matriz-criterios-de-aceite.md) |
| **Revisão** (8.3.4, controles do projeto e desenvolvimento) | Sim | Aprovação humana da spec antes do código; PR revisado por um colega ("ninguém aprova o próprio PR", [`combinados.md`](../combinados.md)); [checklist de revisão de código](revisao-de-codigo.md) |
| **Verificação** (8.3.4) | Sim | Suíte com critério binário por spec; [definição de pronto](../testes.md) |
| **Informação documentada** (7.5) | Sim | Baseline versionada em `docs/`; mudança em requisito atualiza os dependentes no mesmo PR |
| **Controle de mudanças** (8.3.6) | Sim | Regra 4: não alterar a baseline para acomodar o código; propor e aguardar aprovação |
| **Ação corretiva e não conformidade** (10.2) | Sim | [`defeitos.md`](defeitos.md): D-01 a D-05 encontrados, corrigidos e re-testados; D-06 aberto com registro da causa |
| **Melhoria contínua** (10.3) | Parcial | A rodada de qualidade de outubro de 2026 (#48 a #84) e o registro de pendências; falta um ciclo periódico de retrospectiva |
| **Planejamento com base em riscos** (6.1) | Parcial | `OPEN-nn` registra o que não foi decidido, mas sem avaliação de probabilidade e impacto |
| **Monitoramento e medição** (9.1) | Parcial | Métricas medidas uma vez, no [relatório](relatorio-de-qualidade.md); sem série histórica |
| **Auditoria interna** (9.2) | Não | Nenhuma auditoria do próprio processo; a revisão é do produto |
| **Análise crítica pela direção** (9.3) | Não aplicável | Não há direção; o equivalente seria a reunião semanal da equipe, ainda "a confirmar" em `combinados.md` |
| **Validação com o cliente** (8.3.4 e 8.2) | Não | Sem cliente real; só personas |

## 3. Nível de maturidade do CMMI

CMMI organiza a maturidade em cinco níveis: 1 Inicial, 2 Gerenciado, 3 Definido, 4 Gerenciado quantitativamente, 5 Em otimização.

**O processo atual se aproxima do nível 2 (Gerenciado), com alguns elementos do nível 3.** Não está plenamente no nível 2.

| Área de processo do nível 2 | Situação | Justificativa |
|---|---|---|
| Gestão de requisitos | Atendida em boa medida | Requisitos com identificador estável, rastreados a UC, RB e testes; matriz de critérios |
| Planejamento do projeto | Atendida em boa medida | Mapa de specs; issues com critérios de aceite e responsável; Kanban |
| Monitoramento e controle do projeto | Parcial | Kanban com colunas definidas, mas reunião semanal ainda "a confirmar"; sem comparação de plano e realizado |
| Gestão de configuração | Atendida | Git, branches, PR, identificadores imutáveis |
| Garantia da qualidade do processo e do produto | Parcial | Revisão por colega e checklist; mas nada audita o cumprimento do próprio fluxo |
| Medição e análise | Parcial | Métricas existem, em uma única medição |
| Gestão de acordos com fornecedores | Não aplicável | Não há fornecedor |

Por que não é o nível 3: o processo é definido (o `CLAUDE.md` é um processo padrão, com modelo de spec e regras), mas para o projeto, e não como padrão de uma organização com adaptação (*tailoring*) e treinamento. Isso é suficiente para dizer que há **elementos** do nível 3, como o processo padrão escrito, as ADRs (análise de decisão) e as verificações por critério de aceite.

**O que faltaria para o nível seguinte** (completar o 2 e chegar ao 3):

1. Fechar o nível 2: reunião semanal confirmada em `combinados.md` e uso real do Kanban; comparar o previsto com o realizado; guardar as métricas a cada rodada para ter série histórica; **verificar o cumprimento do fluxo** (por exemplo, a integração contínua exigindo a suíte aprovada, [`execucao.md`](../execucao.md), OPEN-28, #82).
2. Gestão de riscos com probabilidade e impacto, em vez de só `OPEN-nn`.
3. Validação com usuário real (o ciclo de verificação existe; o de validação, não).
4. Processo padrão com adaptação documentada (o que muda quando se trabalha com agente de codificação e quando não).
5. Papéis e treinamento: `combinados.md` ainda é "rascunho para aprovação".

Os níveis 4 e 5 (gestão quantitativa e otimização) não se aplicam ao tamanho e à duração do projeto.

## 4. Particularidade: trabalho com agente de codificação

O SDD usa um agente de codificação como executor. Para o processo, isso muda duas coisas: o **fluxo** (spec aprovada, depois código) é a principal medida de controle, porque o agente não preenche lacunas (regra 2) e as **ações do agente** têm limites explícitos ([`CLAUDE.md`](../../CLAUDE.md), "Ações do agente"; [`seguranca.md`](../seguranca.md)); e o **PR declara o uso de agente**, com revisão humana (template de PR, [`combinados.md`](../combinados.md)). Isso corresponde, na ISO 9001, ao controle de processos fornecidos externamente (8.4) e à responsabilidade de quem aprova (8.3.4).
