# Documentação Final — RemindMe

Documento consolidado de requisitos, modelagem e arquitetura do RemindMe, na situação de 2026-11-07. Ele reúne em uma leitura só o que a baseline diz e aponta, para cada assunto, o documento que é a fonte. Em caso de diferença, vale o documento de origem.

- **Disciplina:** Modelagem de Software — Mackenzie, 2026-2.
- **Equipe:** João Pedro Silva Guerra, Bernardo Sanches e Renan Ribeiro Gandolpho ([combinados](combinados.md)).
- **Método:** Spec-Driven Development, descrito no [`SPECS.md`](../SPECS.md).
- **Execução:** local, na máquina de quem apresenta, sem hospedagem externa (OPEN-12).

## 1. Problema e visão

Micro e pequenas empresas vendem a prazo e não têm back-office. Orçamento aprovado não vira cobrança, título vencido não é cobrado, prazo fiscal se perde e ninguém sabe quem fez o quê. A causa é falta de rotina com regra, e não falta de sistema contábil.

O RemindMe é um sistema web de gestão do ciclo de recebíveis e das obrigações dessas empresas. Ele garante que cada cobrança e cada obrigação avance no prazo, com registro de quem fez o quê e quando.

| Parte | Conteúdo | Fonte |
|---|---|---|
| Núcleo | Orçamento → título → régua de cobrança → renegociação → baixa | [Visão, seção 4](visao.md) |
| Apoio | Calendário de obrigações; contas a pagar (OPEN-56); apuração do resultado | [Visão, seção 4](visao.md) |
| IA | Classifica lançamentos e extrai intenção de mensagens. A IA extrai e classifica; o sistema decide | [Visão, seção 5](visao.md); [ADR-003](adr/ADR-003-ia-extrai-e-classifica-o-sistema-decide.md) |
| Fora do MVP | Nota fiscal, folha, recomendação de investimento, WhatsApp real | [Visão, seção 6](visao.md) |
| Mercado | Soluções existentes e a lacuna ocupada | [Benchmark](benchmark.md) |

### Perfis e personas

O sistema tem três perfis de negócio e o Administrador. O cliente da empresa não é usuário: ele recebe orçamentos e cobranças e responde pelo canal de notificação (OPEN-57).

| Perfil | Persona | O que faz |
|---|---|---|
| Dono | Carla Menezes | Decide exceções, aprova descontos fora de alçada, estorna pagamentos e cancela títulos e contas a pagar |
| Operador Financeiro | Diego Ramos | Elabora orçamentos, registra pagamentos, trata cobranças, obrigações e contas a pagar |
| Contador | Helena Prado | Consulta e exporta, somente leitura (RB-03) |
| Administrador | — | Mantém usuários, permissões e configurações (OPEN-10); tem todas as permissões, fixas na matriz (OPEN-53) |
| *Cliente (não é perfil)* | Sérgio Tavares | Recebe orçamentos e cobranças e responde pelo canal de notificação |

Detalhes em [personas](personas.md).

## 2. Requisitos

Fonte: [`requisitos.md`](requisitos.md). RF e RNF em EARS; RB em forma declarativa.

| Tipo | Identificadores | Retirados | Ativos | Grupos |
|---|---|---|---|---|
| RF | RF-01 a RF-96 | RF-60, RF-63, RF-69 | 93 | Acesso; orçamentos; descontos e alçadas; títulos e pagamentos; cobrança; renegociação; obrigações; lançamentos e IA; apuração; auditoria; importação e exportação; contas a pagar |
| RNF | RNF-01 a RNF-26 | RNF-10 | 25 | Segurança e privacidade; confiabilidade; desempenho; usabilidade; manutenibilidade e evolução |
| RB | RB-01 a RB-33 | RB-26 (RB-25 não foi usado) | 31 | Estados, valores, alçadas, auditoria, IA, régua, obrigações e contas a pagar |

Os requisitos que mais pesam na arquitetura viraram drivers (seção 4). Os valores de RNF-07, RNF-08 e RNF-24 foram confirmados em 2026-10-23 (OPEN-09).

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
| Pagáveis | `Fornecedor`, `ContaPagar` | RB-31, RB-32, RB-33 |
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
| Conta a pagar | Aberta, Vencida, Paga, Cancelada |

### Casos de uso

Fonte: [`casos-de-uso/`](casos-de-uso/README.md). São 16 casos de uso, UC-01 a UC-16. O fluxo principal é UC-04 → UC-08 → UC-06: o orçamento vira título, o título é cobrado e o pagamento o baixa. Há diagramas de sequência para o [UC-04](uml/seq-UC-04.png) e o [UC-06](uml/seq-UC-06.png).

## 4. Arquitetura

Fonte: [`arquitetura.md`](arquitetura.md).

Monólito web em camadas, com o domínio isolado de framework, banco e serviços externos. Canal de notificação e serviço de IA ficam atrás de interfaces, com implementação simulada como padrão.

| Camada | Responsabilidade | Pacote |
|---|---|---|
| Apresentação | Telas web sobre WSGI da biblioteca padrão (ADR-006) | `src/remindme/apresentacao/web` |
| Entradas automáticas | Agendador de vencimentos, tarefa periódica no próprio processo (OPEN-13, OPEN-48); recepção de mensagens na Spec 009 | `src/remindme/entradas` |
| Aplicação | Um serviço por caso de uso: permissão, transação, auditoria | `src/remindme/aplicacao` |
| Domínio | Classes, estados e regras de negócio | `src/remindme/dominio` |
| Infraestrutura | Persistência em SQLite (ADR-007), relógio e dublês em memória para os testes | `src/remindme/infraestrutura` |

### Drivers, decisões e ADRs

| Driver | Resumo | Decisão |
|---|---|---|
| DA-01 | Transições de estado são invariantes de domínio | DT-01, [ADR-001](adr/ADR-001-monolito-em-camadas-com-dominio-isolado.md) |
| DA-02 | Toda mudança de estado é auditada, e a auditoria é imutável | DT-04, [ADR-004](adr/ADR-004-auditoria-somente-inclusao.md) |
| DA-03 | Operações financeiras são atômicas | DT-05 |
| DA-04 | Acesso negado por padrão; o cliente não acessa o sistema | DT-06 |
| DA-05 | Processamento por tempo não degrada o uso interativo | DT-07 |
| DA-06 | A IA é falível e nunca decide | DT-03, [ADR-003](adr/ADR-003-ia-extrai-e-classifica-o-sistema-decide.md) |
| DA-07 | A suíte roda sem credencial externa | DT-02, [ADR-002](adr/ADR-002-canal-de-notificacao-substituivel.md) |
| DA-08 | A régua não repete etapa para o mesmo título | DT-08 |
| DA-09 | Cada regra em um único ponto, com teste nomeado | DT-01 |
| DA-10 | Configuração alterada não reescreve o passado | DT-09 |

Os sete ADRs estão aceitos: ADR-005 a ADR-007 em 2026-10-23 e ADR-001 a ADR-004 em 2026-11-07. Segurança do produto e do uso de agentes: [`seguranca.md`](seguranca.md).

## 5. Do mapa de specs ao código

Fonte: [mapa de specs](../.specify/specs/mapa-de-specs.md), aprovado em 2026-11-07. São 19 specs, de 001 a 019, ordenadas pelas dependências do domínio.

| Situação | Specs |
|---|---|
| Verificadas | [001](../.specify/specs/001-fundacao-camadas-e-auditoria.md) fundação e auditoria; [002](../.specify/specs/002-autenticacao-e-autorizacao.md) autenticação e autorização; [003](../.specify/specs/003-cadastro-de-clientes.md) clientes; [004](../.specify/specs/004-orcamento-itens-valores-e-alcada.md) orçamento e alçada; [006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) título, pagamento, baixa e estorno; [013](../.specify/specs/013-consulta-de-auditoria.md) consulta de auditoria; [017](../.specify/specs/017-interface-web.md) interface web; [018](../.specify/specs/018-contas-a-pagar-e-fornecedores.md) contas a pagar e fornecedores; [019](../.specify/specs/019-troca-da-propria-senha.md) troca da própria senha |
| A escrever | 005 conversão em título; 007 e 008 régua de cobrança; 009 renegociação; 010 obrigações; 011 lançamentos e IA; 012 apuração; 014 configuração de regras; 015 CSV; 016 painel por perfil |

Tecnologia adotada (OPEN-01): Python 3.11 ou mais recente, somente a biblioteca padrão, com interface web sobre WSGI (ADR-006), banco SQLite (ADR-007) e testes com `unittest`. A suíte tem 478 testes, todos passando, com 9 pulados: 4 de navegador, que dependem do Playwright, opcional (OPEN-29), e 5 marcadores de testes ainda não escritos. Para ver a aplicação: `python3 iniciar.py demonstracao`. Como executar: [`execucao.md`](execucao.md). Estratégia de testes: [`testes.md`](testes.md). Avaliação de qualidade: [`qualidade/`](qualidade/README.md).

## 6. Decisões em aberto

Fonte: [`.specify/open.md`](../.specify/open.md). São 60 questões registradas.

| Situação | Questões |
|---|---|
| Decididas | 58. As decididas "por delegação" ao agente, em 2026-10-23, tiveram autorização prévia de João Pedro Silva Guerra. As OPEN-49 a OPEN-52 foram decididas em 2026-11-07 por Renan Gandolpho |
| Abertas | OPEN-59 (o Administrador redefine a senha de outro usuário?) e OPEN-60 (troca obrigatória da senha provisória no primeiro acesso?), ambas deixadas fora da Spec 019 |

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
| Desconto acima da alçada | RF-16, RB-15 | UC-04, UC-05 | `Orcamento` | DA-01 | 004, CA-05 | `test_CA_05_RF_16_desconto_acima_da_alcada_fica_pendente_de_alcada` |
| Conta a pagar quitada | RF-91, RB-31 | UC-15 | `ContaPagar` | DA-01 | 018 | `test_RB_31_pagamento_parcial_mantem_aberta_e_o_que_zera_o_saldo_a_torna_paga` |
| Troca da própria senha | RF-95, RF-96 | UC-16 | `Usuario` | DA-04 | 019, CA-01, CA-02 | `test_CA_01_troca_aceita_e_so_a_nova_entra`, `test_CA_02_senha_atual_errada_nao_muda_nada` |

A matriz de critérios de aceite da Spec 006 está em [`qualidade/matriz-criterios-de-aceite.md`](qualidade/matriz-criterios-de-aceite.md). A cadeia requisito → driver → decisão → código → teste, com a cobertura de cada tipo de requisito, está em [`rastreabilidade.md`](rastreabilidade.md).
