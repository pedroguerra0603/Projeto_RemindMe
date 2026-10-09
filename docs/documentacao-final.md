# Documentação Final — RemindMe

Documento consolidado de requisitos, modelagem e arquitetura do RemindMe, na situação de 2026-10-09. Ele reúne em uma leitura só o que a baseline diz e aponta, para cada assunto, o documento que é a fonte. Em caso de diferença, vale o documento de origem.

- **Disciplina:** Modelagem de Software — Mackenzie, 2026-2.
- **Equipe:** João Pedro Silva Guerra, Bernardo Sanches e Renan Ribeiro Gandolpho ([combinados](combinados.md)).
- **Método:** Spec-Driven Development, descrito no [`CLAUDE.md`](../CLAUDE.md).

## 1. Problema e visão

Micro e pequenas empresas vendem a prazo e não têm back-office. Orçamento aprovado não vira cobrança, título vencido não é cobrado, prazo fiscal se perde e ninguém sabe quem fez o quê. A causa é falta de rotina com regra, e não falta de sistema contábil.

O RemindMe é um sistema web de gestão do ciclo de recebíveis e das obrigações dessas empresas. Ele garante que cada cobrança e cada obrigação avance no prazo, com registro de quem fez o quê e quando.

| Parte | Conteúdo | Fonte |
|---|---|---|
| Núcleo | Orçamento → título → régua de cobrança → renegociação → baixa | [Visão, seção 4](visao.md) |
| Apoio | Calendário de obrigações; apuração do resultado | [Visão, seção 4](visao.md) |
| IA | Classifica lançamentos e extrai intenção de mensagens. A IA extrai e classifica; o sistema decide | [Visão, seção 5](visao.md); [ADR-003](adr/ADR-003-ia-extrai-e-classifica-o-sistema-decide.md) |
| Fora do MVP | Nota fiscal, folha, recomendação de investimento, WhatsApp real, contas a pagar | [Visão, seção 6](visao.md) |
| Mercado | Soluções existentes e a lacuna ocupada | [Benchmark](benchmark.md) |

### Perfis e personas

| Perfil | Persona | O que faz |
|---|---|---|
| Dono | Carla Menezes | Decide exceções, aprova descontos fora de alçada, estorna pagamentos e cancela títulos |
| Operador Financeiro | Diego Ramos | Elabora orçamentos, registra pagamentos, trata cobranças e obrigações |
| Cliente | Sérgio Tavares | Decide orçamentos, consulta os próprios títulos, propõe renegociação |
| Contador | Helena Prado | Consulta e exporta, somente leitura (RB-03) |

O Administrador aparece nos casos de uso como ator. Se é perfil próprio ou papel do Dono está em aberto (OPEN-10). Detalhes em [personas](personas.md).

## 2. Requisitos

Fonte: [`requisitos.md`](requisitos.md). RF e RNF em EARS; RB em forma declarativa.

| Tipo | Identificadores | Retirados | Grupos |
|---|---|---|---|
| RF | RF-01 a RF-85 | RF-60, RF-63 | Acesso; orçamentos; descontos e alçadas; títulos e pagamentos; cobrança; renegociação; obrigações; lançamentos e IA; apuração; auditoria; importação e exportação |
| RNF | RNF-01 a RNF-26 | RNF-10 | Segurança e privacidade; confiabilidade; desempenho; usabilidade; manutenibilidade e evolução |
| RB | RB-01 a RB-30 | — (RB-25 não foi usado) | Estados, valores, alçadas, auditoria, IA, régua e obrigações |

Os requisitos que mais pesam na arquitetura viraram drivers (seção 5). Os valores marcados com **(P)** em RNF-07, RNF-08 e RNF-24 ainda aguardam confirmação (OPEN-09).

Vocabulário obrigatório: [glossário](glossario.md). Termos como "fatura", "boleto" e "duplicata" não são usados no lugar de *título*.

## 3. Modelagem

### Domínio

Fonte: [modelo de domínio](modelo-dominio.md) e [diagrama de classes](uml/dominio-v2.png).

| Módulo | Classes | Regras principais |
|---|---|---|
| Acesso | `Usuario`, `Perfil`, `AlcadaDesconto` | RB-03, RB-15 |
| Comercial | `Cliente`, `Orcamento`, `ItemOrcamento`, `AprovacaoDesconto` | RB-05, RB-15, RB-24 |
| Recebíveis | `Titulo`, `Pagamento`, `Renegociacao` | RB-02, RB-21, RB-22, RB-23, RB-28 |
| Cobrança | `ReguaCobranca`, `EtapaCobranca`, `TentativaCobranca` | RB-10, RB-11 |
| Obrigações | `Obrigacao`, `Evidencia` | RB-07, RB-13, RB-16, RB-29 |
| Resultado | `LancamentoFinanceiro`, `CategoriaFinanceira`, `SugestaoClassificacao` | RB-06, RB-08, RB-12, RB-14 |
| Auditoria | `RegistroAuditoria` | RB-01, RB-30 |

`Titulo` é a classe central: controla saldo, vencimento e estado.

### Estados

Fonte: [`uml/estados.md`](uml/estados.md). Transição fora da tabela é inválida e é recusada.

| Entidade | Estados |
|---|---|
| Título | Aberto, Vencido, Em Renegociação, Baixado, Cancelado |
| Orçamento | Rascunho, Pendente de Alçada, Enviado, Aprovado, Rejeitado, Convertido, Cancelado |
| Obrigação | Pendente, Aguardando Evidência, Atrasada, Cumprida |

### Casos de uso

Fonte: [`casos-de-uso/`](casos-de-uso/README.md). São 14 casos de uso, UC-01 a UC-14. O fluxo principal é UC-04 → UC-08 → UC-06: o orçamento vira título, o título é cobrado e o pagamento o baixa. Há diagramas de sequência para o [UC-04](uml/seq-UC-04.png) e o [UC-06](uml/seq-UC-06.png).

## 4. Arquitetura

Fonte: [`arquitetura.md`](arquitetura.md).

Monólito web em camadas, com o domínio isolado de framework, banco e serviços externos. Canal de notificação e serviço de IA ficam atrás de interfaces, com implementação simulada como padrão.

| Camada | Responsabilidade | Pacote atual |
|---|---|---|
| Apresentação e entradas automáticas | Telas, API, agendador, recepção de mensagens | Ainda não existe (OPEN-01, OPEN-13) |
| Aplicação | Um serviço por caso de uso: permissão, transação, auditoria | `src/remindme/aplicacao` |
| Domínio | Classes, estados e regras de negócio | `src/remindme/dominio` |
| Infraestrutura | Persistência, canal, IA, relógio | `src/remindme/infraestrutura` (em memória) |

### Drivers, decisões e ADRs

| Driver | Resumo | Decisão |
|---|---|---|
| DA-01 | Transições de estado são invariantes de domínio | DT-01, [ADR-001](adr/ADR-001-monolito-em-camadas-com-dominio-isolado.md) |
| DA-02 | Toda mudança de estado é auditada, e a auditoria é imutável | DT-04, [ADR-004](adr/ADR-004-auditoria-somente-inclusao.md) |
| DA-03 | Operações financeiras são atômicas | DT-05 |
| DA-04 | Acesso negado por padrão; Cliente só vê os próprios dados | DT-06 |
| DA-05 | Processamento por tempo não degrada o uso interativo | DT-07 |
| DA-06 | A IA é falível e nunca decide | DT-03, [ADR-003](adr/ADR-003-ia-extrai-e-classifica-o-sistema-decide.md) |
| DA-07 | A suíte roda sem credencial externa | DT-02, [ADR-002](adr/ADR-002-canal-de-notificacao-substituivel.md) |
| DA-08 | A régua não repete etapa para o mesmo título | DT-08 |
| DA-09 | Cada regra em um único ponto, com teste nomeado | DT-01 |
| DA-10 | Configuração alterada não reescreve o passado | DT-09 |

Os quatro ADRs estão com situação Proposto. Segurança do produto e do uso de agentes: [`seguranca.md`](seguranca.md).

## 5. Do mapa de specs ao código

Fonte: [mapa de specs](../.specify/specs/mapa-de-specs.md). São 16 specs, de 001 a 016, ordenadas pelas dependências do domínio.

| Spec | Situação | Evidência |
|---|---|---|
| [006 — Título: cadastro manual, pagamento, baixa e estorno](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) | Verificada | Plano em [`006-plano.md`](../.specify/plans/006-plano.md); testes em [`tests/`](../tests/README.md) |
| 001 a 005, 007 a 016 | A escrever | — |

Tecnologia adotada (OPEN-01): Python 3.11 ou mais recente, somente a biblioteca padrão, testes com `unittest`. Como executar: [`execucao.md`](execucao.md). Estratégia de testes: [`testes.md`](testes.md). Avaliação de qualidade: [`qualidade/`](qualidade/README.md).

## 6. Decisões em aberto

Fonte: [`.specify/open.md`](../.specify/open.md).

| Situação | Questões |
|---|---|
| Decididas | OPEN-01 (linguagem), OPEN-11 (juros fora do MVP), OPEN-16 (só o Dono cancela título) |
| Abertas, bloqueiam specs futuras | OPEN-02 (banco), OPEN-03 (sessão), OPEN-04 e OPEN-05 (IA), OPEN-06 e OPEN-14 (renegociação), OPEN-07 (despesas), OPEN-08 (acesso do Cliente), OPEN-10 (Administrador), OPEN-13 (agendador), OPEN-15 (parcelas) |
| Abertas, não bloqueiam | OPEN-09 (metas operacionais), OPEN-12 (hospedagem), OPEN-17 a OPEN-19 (Spec 006), OPEN-20 (precisão monetária) |

## 7. Rastreabilidade

A ligação entre os artefatos é feita pelo identificador, que aparece no requisito, na spec, no nome do teste e no PR.

```
Visão → RF/RNF/RB → UC → Modelo de domínio → DA → DT/ADR → Spec → Teste → PR
```

| Exemplo | Requisito | Caso de uso | Classe | Driver | Spec | Teste |
|---|---|---|---|---|---|---|
| Pagamento maior que o saldo | RF-68, RB-23 | UC-06 | `Titulo` | DA-01 | 006, CA-06 | `test_CA_06_recusa_pagamento_maior_que_o_saldo`, `test_RB_23_recusa_pagamento_maior_que_o_saldo` |
| Baixa | RF-26, RB-22 | UC-06 | `Titulo` | DA-01 | 006, CA-03 | `test_CA_03_pagamento_integral_baixa_o_titulo` |
| Estorno só pelo Dono | RF-30, RB-02 | UC-06 | `Pagamento` | DA-04 | 006, CA-15 | `test_CA_15_operador_financeiro_nao_estorna`, `test_RB_02_somente_o_dono_estorna` |
| Atomicidade | RNF-09 | UC-06 | — | DA-03 | 006, CA-23 | `test_CA_23_falha_na_auditoria_desfaz_o_pagamento` |

A matriz completa de critérios de aceite está em [`qualidade/matriz-criterios-de-aceite.md`](qualidade/matriz-criterios-de-aceite.md).
