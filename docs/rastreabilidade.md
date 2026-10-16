# Rastreabilidade — RemindMe

Issue #40. Este documento liga os requisitos aos drivers arquiteturais, às decisões técnicas, à implementação e aos testes. Ele mostra, para cada requisito, de onde ele vem e onde está a evidência de que foi atendido.

- **Data:** 2026-10-16.
- **Base:** `main` em `4b4ef09`, depois do PR #85. A suíte tem 132 testes, todos passando.
- **Fontes:** [requisitos](requisitos.md), [arquitetura](arquitetura.md), [ADRs](adr/README.md), [mapa de specs](../.specify/specs/mapa-de-specs.md), [Spec 006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), [`src/`](../src/README.md), [`tests/`](../tests/README.md).
- **Complementa:** a [matriz de critérios de aceite](qualidade/matriz-criterios-de-aceite.md). A matriz parte de cada critério da Spec 006 e chega ao teste. Este documento parte do requisito e passa pelo driver e pela decisão.

## 1. Cadeia

```
Requisito (RF, RNF, RB) → Driver (DA) → Decisão (DT, ADR) → Spec → Código → Teste
```

O identificador é o elo da cadeia. Ele aparece no requisito, na spec, na docstring do código e no nome do teste. Por exemplo, a regra `RB-23` vira o teste `test_RB_23_recusa_pagamento_maior_que_o_saldo`. Os caminhos de código são relativos a `src/remindme/`.

## 2. Drivers → decisões → implementação → testes

Os dez drivers de [`arquitetura.md`](arquitetura.md#2-drivers-arquiteturais), com a decisão que responde a cada um e a evidência no código.

| Driver | Requisitos de origem | Decisão | Specs | Implementação | Testes | Situação |
|---|---|---|---|---|---|---|
| DA-01 — Transições de estado são invariantes de domínio | RB-21, RB-05, RB-22, RF-12, RF-24 | DT-01, ADR-001 | 006 (título); 004, 005 (orçamento); 010 (obrigação) | `dominio/titulo.py`: `EstadoTitulo` e os métodos de `Titulo` | `test_RB_21_*` (10), `test_INV_4_*` (2), CA-08, CA-09, CA-19 | Título: implementado, sem Em Renegociação (Spec 009). Orçamento e obrigação: pendentes |
| DA-02 — Toda mudança de estado é auditada, e a auditoria é imutável | RB-01, RB-30, RNF-06 | DT-04, ADR-004 | 001, 013; 006 (uso) | `dominio/auditoria.py` (`RegistroAuditoria` imutável); `aplicacao/servico_titulos.py` (`_auditar`, `_auditar_estado`); `infraestrutura/memoria.py` (`AuditoriaEmMemoria`, só inclusão) | CA-22 (2), `test_RB_01_toda_mudanca_de_estado_tem_registro_de_auditoria`, `test_RB_30_registro_de_auditoria_e_imutavel`, `test_ADR_004_registros_sao_acrescentados_em_ordem` | Parcial: título e pagamento, em memória. Persistência e consulta nas Specs 001 e 013 |
| DA-03 — Operações financeiras são atômicas | RNF-09, RB-19 | DT-05 | 006; 005, 015 | `infraestrutura/memoria.py`: `UnidadeDeTrabalhoEmMemoria`; o serviço abre uma transação por operação | CA-23, `test_RNF_09_*` (8) | Implementado em memória. O banco depende de OPEN-02 |
| DA-04 — Acesso negado por padrão; o Cliente só vê os próprios dados | RNF-02, RNF-03, RNF-25, RB-03, RB-26 | DT-06 | 002, 009; 006 (estorno e cancelamento) | `dominio/regras.py` (`exigir_permissao_de_estorno`, `exigir_permissao_de_cancelamento`), chamadas pelo serviço antes do domínio | CA-15, CA-18, `test_RB_02_*` (2), `test_OPEN_16_*` (2) | Parcial: só RB-02 e OPEN-16. RB-03, RNF-01, RNF-02 e RNF-25 dependem das Specs 002 e 009 |
| DA-05 — Processamento por tempo não degrada o uso interativo | RF-24, RF-33, RF-34, RF-44, RF-48, RNF-12, RNF-13 | DT-07 | 008, 010 | `ServicoTitulos.verificar_vencimentos`: a operação existe e pode ser chamada pelo agendador | CA-10, CA-11, `test_RF_24_*` (3); lote de vencimentos medido em [eficiência](qualidade/eficiencia.md) | Parcial: o agendador não existe (OPEN-13, Spec 008) |
| DA-06 — A IA é falível e nunca decide | RB-08, RB-14, RB-17, RB-27, RNF-24 | DT-03, ADR-003 | 009, 011 | — | — | Pendente |
| DA-07 — A suíte roda sem credencial externa | RNF-23, RB-18 | DT-02, ADR-002 | 001, 005, 008 | O código e os testes usam somente a biblioteca padrão; não há variável de credencial | `test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao`; a suíte inteira | Parcial: os simuladores de canal e de IA ainda não existem (issue #79) |
| DA-08 — A régua não repete etapa para o mesmo título | UC-08, RF-35 | DT-08 | 008 | — | — | Pendente |
| DA-09 — Cada regra em um único ponto, com teste nomeado | RNF-19 | DT-01 | Todas | RB-21, RB-22 e RB-23 só em `dominio/titulo.py`; RB-02 e OPEN-16 só em `dominio/regras.py` | `test_RNF_19_regras_do_titulo_ficam_somente_no_dominio`, `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas` | Implementado para a Spec 006 |
| DA-10 — Configuração alterada não reescreve o passado | RNF-18, RF-36 | DT-09 | 007, 014 | — | — | Pendente |

## 3. Requisitos implementados → código → testes

Requisitos da Spec 006 e os RNF verificados na rodada de qualidade de outubro (#48 a #72). O asterisco indica o conjunto de testes com aquele prefixo; entre parênteses, a quantidade.

| Requisito | Driver | Decisão | Código | Testes | Situação |
|---|---|---|---|---|---|
| RF-20 | DA-01 | DT-01 | `Titulo.cadastrar_manual`; `ServicoTitulos.cadastrar_titulo` | CA-01, CA-02 (2), `test_RB_21_titulo_nasce_aberto`, `test_RF_20_condicao_de_pagamento_e_opcional`, `test_E7_*` (5) | Implementado. "Usuário autorizado" depende da Spec 002 |
| RF-21 | — | — | Campos de `Titulo` | `test_RF_21_armazena_todos_os_dados_do_titulo`, `test_contrato_salva_e_obtem_com_todos_os_dados` | Implementado |
| RF-22 | — | — | `ServicoTitulos.consultar_titulos`, `FiltroTitulos`, `_atende` | CA-21 (2) | Implementado. "Período" filtra o vencimento (OPEN-19) |
| RF-23 | — | — | `Titulo.proximo_do_vencimento` | CA-20, `test_RF_23_*` (3) | Implementado. Nenhuma spec define de onde vem a antecedência (OPEN-21) |
| RF-24 | DA-01, DA-05 | DT-01, DT-07 | `Titulo.marcar_vencido`; `ServicoTitulos.verificar_vencimentos` | CA-10, CA-11, `test_RF_24_*` (3), `test_RNF_09_falha_no_meio_do_lote_de_vencimentos_desfaz_o_lote_inteiro` | Implementado. O disparo periódico é da Spec 008 |
| RF-25 | DA-01, DA-03 | DT-01, DT-05 | `Titulo.registrar_pagamento`; `ServicoTitulos.registrar_pagamento` | CA-03, CA-04, `test_RF_25_devolve_o_pagamento_registrado` | Implementado. "Usuário autorizado" depende da Spec 002 |
| RF-26 | DA-01 | DT-01 | `Titulo.registrar_pagamento` (RB-22) | CA-03, CA-05, CA-12 | Implementado |
| RF-27 | — | — | `Titulo.saldo` | CA-04, `test_RF_27_*` (2) | Implementado |
| RF-30 | DA-01, DA-04 | DT-01, DT-06 | `Titulo.estornar_pagamento`; `regras.exigir_permissao_de_estorno`; `ServicoTitulos.estornar_pagamento` | CA-13, CA-14, `test_A4_*` (3), `test_RF_30_estorno_guarda_o_motivo` | Implementado. Em aberto: OPEN-18 e OPEN-23 |
| RF-31 | DA-02 | DT-04 | `_exigir_motivo` em `dominio/titulo.py` | CA-16, `test_CA_18_E4_recusa_cancelamento_sem_motivo`, `test_RF_31_motivo_em_branco_equivale_a_ausente`, `test_E4_*` (3) | Implementado para estorno e cancelamento. A "alteração de valor" não tem operação (OPEN-22) |
| RF-68 | DA-01 | DT-01 | `Titulo.registrar_pagamento`, `_exigir_decimal` | CA-06, CA-07, `test_E1_*` (3) | Implementado |
| RB-01 | DA-02 | DT-04, ADR-004 | `ServicoTitulos._auditar`, `_auditar_estado` | CA-22 (2), `test_RB_01_toda_mudanca_de_estado_tem_registro_de_auditoria`, `test_UC_06_ciclo_completo_grava_estado_e_trilha_de_auditoria` | Parcial: título e pagamento |
| RB-02 | DA-04 | DT-06 | `regras.exigir_permissao_de_estorno` | CA-15, `test_RB_02_*` (2) | Implementado |
| RB-21 | DA-01 | DT-01, ADR-001 | `EstadoTitulo`, `ESTADOS_QUE_ACEITAM_PAGAMENTO`, `ESTADOS_QUE_ACEITAM_CANCELAMENTO` e os métodos de `Titulo` | CA-08, CA-09, CA-19, `test_RB_21_*` (10), `test_INV_4_*` (2) | Parcial: sem Em Renegociação (Spec 009) |
| RB-22 | DA-01 | DT-01 | `Titulo.registrar_pagamento`, `Titulo.saldo` | CA-03, CA-05, `test_RB_22_*` (3) | Implementado |
| RB-23 | DA-01 | DT-01 | `Titulo.registrar_pagamento` | CA-06, CA-07, `test_RB_23_*` (6) | Implementado |
| RB-30 | DA-02 | DT-04, ADR-004 | `RegistroAuditoria` imutável (`frozen=True`); `AuditoriaEmMemoria` sem alteração nem exclusão | `test_RB_30_registro_de_auditoria_e_imutavel`, `test_ADR_004_registros_sao_acrescentados_em_ordem` | Parcial: objeto imutável. A garantia no armazenamento é da Spec 001 |
| OPEN-16 (decisão) | DA-04 | DT-06 | `regras.exigir_permissao_de_cancelamento` | `test_CA_18_OPEN_16_operador_financeiro_nao_cancela`, `test_OPEN_16_*` (2) | Implementado |
| RNF-03 | DA-04 | DT-06 | A permissão é verificada no serviço, sem interface | CA-15, `test_RB_02_nenhum_outro_perfil_estorna` | Parcial: só estorno e cancelamento |
| RNF-09 | DA-03 | DT-05 | `UnidadeDeTrabalhoEmMemoria` | CA-23, `test_RNF_09_*` (8) | Implementado em memória |
| RNF-11 | DA-05 | — | — | `test_RNF_11_*` (3); [eficiência](qualidade/eficiencia.md) | Atende, com 2000 títulos em memória |
| RNF-14 | — | — | Motivo de `OperacaoRecusada` | `test_RNF_14_*` (2); [usabilidade](qualidade/usabilidade.md) | Parcial: ainda não há interface |
| RNF-19 | DA-09 | DT-01 | Regras somente em `dominio/` | `test_RNF_19_regras_do_titulo_ficam_somente_no_dominio` | Implementado |
| RNF-23 | DA-07 | DT-02 | Somente a biblioteca padrão | `test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao` | Parcial: simuladores pendentes |

## 4. Requisitos ainda sem implementação

Todo requisito ativo aparece em ao menos uma spec do mapa. A conferência foi feita por script sobre `requisitos.md` e a tabela do mapa: os 137 requisitos ativos aparecem. RNF-07 e RNF-08 aparecem como operacionais, na nota abaixo da tabela. Os que não estão na seção 3 seguem pela spec indicada no mapa.

| Spec | Requisitos | Situação da spec |
|---|---|---|
| 001 | RF-04, RF-05, RF-61, RF-62; RB-01, RB-30; RNF-06, RNF-21 | A escrever |
| 002 | RF-02, RF-03, RF-65, RF-66, RF-67; RB-03; RNF-01 a RNF-05 | A escrever |
| 003 | RF-01 | A escrever |
| 004 | RF-06, RF-07, RF-10, RF-13 a RF-18; RB-15, RB-24 | A escrever |
| 005 | RF-08, RF-09, RF-11, RF-12, RF-19; RB-05, RB-18 | A escrever |
| 007, 008 | RF-32 a RF-39, RF-70, RF-71; RB-10, RB-11; RNF-12, RNF-13, RNF-18, RNF-20 | A escrever |
| 009 | RF-28, RF-29, RF-69, RF-72 a RF-76; RB-17, RB-20, RB-26, RB-27, RB-28; RNF-22, RNF-24, RNF-25 | A escrever |
| 010 | RF-40 a RF-50, RF-77; RB-04, RB-07, RB-13, RB-16, RB-29; RNF-15 | A escrever |
| 011, 012 | RF-51 a RF-59, RF-78 a RF-82; RB-06, RB-08, RB-09, RB-12, RB-14; RNF-26 | A escrever |
| 013 a 016 | RF-64, RF-83 a RF-85; RB-19; RNF-16, RNF-17 | A escrever |
| Operacionais | RNF-07, RNF-08 | Na entrega, depois de OPEN-09 e OPEN-12 |

### Cobertura

| Tipo | Ativos | Implementados | Parciais | Sem implementação |
|---|---|---|---|---|
| RF | 83 | 11 (RF-20 a RF-27, RF-30, RF-31, RF-68) | — | 72 |
| RB | 29 | 3 (RB-02, RB-22, RB-23) | 3 (RB-01, RB-21, RB-30) | 23 |
| RNF | 25 | 3 (RNF-09, RNF-11, RNF-19) | 3 (RNF-03, RNF-14, RNF-23) | 19 |
| Drivers | 10 | 1 (DA-09) | 6 (DA-01 a DA-05, DA-07) | 3 (DA-06, DA-08, DA-10) |

## 5. Lacunas encontradas

| Lacuna | Tratamento |
|---|---|
| RF-23 fala em "número de dias configurado", mas nenhum RF, caso de uso ou spec configura essa antecedência. O código a recebe como parâmetro, e a docstring cita a Spec 014, que não a inclui | OPEN-21 |
| RF-31 exige motivo para "alteração de valor", mas nenhuma operação altera o valor do título, e a Spec 006 diz que ele não muda (INV-5) | OPEN-22 |
| A linha da Spec 006 no mapa não listava RB-01, que a spec cobre | Corrigido no mapa (#57) |
| 20 dos 132 testes não levam identificador no nome, contra o princípio 2 de [`testes.md`](testes.md). São testes de infraestrutura, de integração e de contrato do repositório | Registrado em [divergências](qualidade/divergencias.md), DV-14 |

As divergências entre código, spec e baseline estão em [`qualidade/divergencias.md`](qualidade/divergencias.md).

## 6. Como manter

1. Requisito novo ou alterado: atualizar a linha da spec no mapa e, se ele pesar na estrutura, a tabela de drivers da arquitetura.
2. Spec aprovada e implementada: mover seus requisitos da seção 4 para a seção 3, com código e testes.
3. Teste novo de regra: nomear pelo identificador (`test_RB_nn_...`, `test_CA_nn_...`), para que o elo apareça numa busca por texto.
