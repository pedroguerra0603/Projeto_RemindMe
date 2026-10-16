# Matriz Spec → Teste → Resultado — RemindMe

Issue #66. Liga cada critério de aceite, fluxo, exceção, invariante e requisito das specs aprovadas aos testes que os verificam, com o resultado da última execução.

- **Specs aprovadas:** somente a [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md). As demais (001 a 005, 007 a 016) estão "A escrever" no [mapa](../../.specify/specs/mapa-de-specs.md) e não têm critérios a testar.
- **Execução:** `python3 -m unittest discover -s tests -t .`, em 2026-10-09, Python 3.13.16. Resultado de cada linha: **Passou**, salvo indicação.
- **Convenção de nomes:** `CA-06` vira `test_CA_06_...`; `RB-23` vira `test_RB_23_...`.

Pastas abreviadas: `aceite` = `tests/aplicacao/test_spec_006_aceite.py`; `confiab.` = `tests/aplicacao/test_confiabilidade.py`; `usab.` = `tests/aplicacao/test_usabilidade.py`; `regras` = `tests/dominio/test_titulo.py`; `unidades` = `tests/dominio/test_unidades.py`; `invariantes` = `tests/dominio/test_invariantes.py`; `exceções` = `tests/aplicacao/test_excecoes.py`; `integração` = `tests/integracao/test_integracao.py`; `camadas` = `tests/arquitetura/test_camadas.py`.

## 1. Critérios de aceitação da Spec 006

| Critério | Requisito | Teste de aceite | Testes complementares | Resultado |
|---|---|---|---|---|
| CA-01 | RF-20, RF-21 | `test_CA_01_cadastro_manual_cria_titulo_aberto` | `test_RF_21_armazena_todos_os_dados_do_titulo` (unidades) | Passou |
| CA-02 | RF-20, E7 | `test_CA_02_recusa_cadastro_com_valor_zero`; `test_CA_02_E7_recusa_cadastro_com_cliente_inexistente_ou_sem_vencimento` | `test_E7_recusa_valor_negativo` (unidades) | Passou |
| CA-03 | RF-25, RF-26, RB-22 | `test_CA_03_pagamento_integral_baixa_o_titulo` | `test_RB_23_aceita_pagamento_igual_ao_saldo` (regras) | Passou |
| CA-04 | RF-27 | `test_CA_04_pagamento_parcial_mantem_aberto` | `test_RF_27_pagamento_parcial_devolve_o_saldo_restante` (usab.) | Passou |
| CA-05 | RF-26, INV-3 | `test_CA_05_pagamento_do_saldo_restante_baixa_o_titulo` | `test_RB_22_baixa_quando_soma_dos_pagamentos_iguala_o_valor` (regras) | Passou |
| CA-06 | RF-68, RB-23 | `test_CA_06_recusa_pagamento_maior_que_o_saldo` | `test_RB_23_recusa_pagamento_maior_que_o_saldo` (regras); `test_RNF_14_recusa_por_saldo_informa_o_saldo_disponivel` (usab.) | Passou |
| CA-07 | RF-68, RB-23 | `test_CA_07_recusa_pagamento_zero_ou_negativo` | `test_RB_23_recusa_pagamento_zero`, `test_RB_23_recusa_pagamento_negativo` (regras) | Passou |
| CA-08 | RB-21, E2 | `test_CA_08_recusa_pagamento_em_titulo_baixado_informando_o_estado` | `test_RB_21_recusa_pagamento_em_titulo_baixado` (regras) | Passou |
| CA-09 | RB-21, E2 | `test_CA_09_recusa_pagamento_em_titulo_cancelado` | `test_RB_21_recusa_pagamento_em_titulo_cancelado` (regras) | Passou |
| CA-10 | RF-24 | `test_CA_10_titulo_com_vencimento_ontem_passa_a_vencido` | `test_RF_24_marcar_vencido_informa_se_mudou` (unidades) | Passou |
| CA-11 | RF-24 | `test_CA_11_titulo_com_vencimento_hoje_continua_aberto` | — | Passou |
| CA-12 | RF-26, RB-21 | `test_CA_12_pagamento_integral_de_titulo_vencido_baixa` | `test_UC_06_ciclo_completo_grava_estado_e_trilha_de_auditoria` (integração) | Passou |
| CA-13 | RF-30, RB-02 | `test_CA_13_estorno_com_vencimento_futuro_volta_a_aberto` | `test_A4_estorno_com_vencimento_igual_a_data_de_referencia_volta_a_aberto` (unidades) | Passou |
| CA-14 | RF-30, RB-21 | `test_CA_14_estorno_com_vencimento_passado_vai_a_vencido` | `test_UC_06_ciclo_completo_...` (integração) | Passou |
| CA-15 | RB-02, E3 | `test_CA_15_operador_financeiro_nao_estorna` | `test_RB_02_somente_o_dono_estorna` (regras); `test_RB_02_nenhum_outro_perfil_estorna` (invariantes), pelo serviço | Passou |
| CA-16 | RF-31, E4 | `test_CA_16_recusa_estorno_sem_motivo` | — | Passou |
| CA-17 | E5, INV-1 | `test_CA_17_recusa_segundo_estorno_do_mesmo_pagamento` | `test_E5_estorno_de_pagamento_inexistente_e_recusado` (unidades) | Passou |
| CA-18 | RF-31, RB-21, OPEN-16 | `test_CA_18_dono_cancela_titulo_aberto_com_motivo`; `test_CA_18_OPEN_16_operador_financeiro_nao_cancela`; `test_CA_18_E4_recusa_cancelamento_sem_motivo` | `test_OPEN_16_somente_o_dono_cancela` (regras); `test_OPEN_16_nenhum_outro_perfil_cancela` (invariantes) | Passou |
| CA-19 | RB-21, E6 | `test_CA_19_recusa_cancelamento_de_titulo_baixado` | `test_E6_recusa_de_cancelamento_de_baixado_orienta_o_estorno` (unidades) | Passou |
| CA-20 | RF-23 | `test_CA_20_titulo_proximo_do_vencimento_e_sinalizado_e_continua_aberto` | `test_RF_23_limites_da_antecedencia`, `test_RF_23_so_titulo_aberto_e_sinalizado` (regras) | Passou |
| CA-21 | RF-22 | `test_CA_21_filtra_por_cliente_e_estado`; `test_CA_21_filtra_por_periodo_de_vencimento` | — | Passou |
| CA-22 | RB-01, INV-7 | `test_CA_22_pagamento_gera_registro_de_auditoria`; `test_CA_22_RB_01_mudancas_de_estado_sao_auditadas` | `test_UC_06_ciclo_completo_...` (integração), trilha completa | Passou |
| CA-23 | RNF-09, INV-7 | `test_CA_23_falha_na_auditoria_desfaz_o_pagamento` | `test_RNF_09_*` (confiab.), 5 operações × 2 tipos de falha | Passou |
| CA-24 | INV-1, INV-2 | `test_CA_24_saldo_e_valor_menos_pagamentos_nao_estornados` | `test_INV_1_a_INV_6_valem_depois_de_cada_operacao` (invariantes) | Passou |

**Cobertura:** 24 de 24 critérios com teste; 24 passaram.

## 2. Fluxos e exceções da Spec 006

| Item | Testes | Resultado |
|---|---|---|
| Fluxo principal | CA-03, CA-22 | Passou |
| A1 — Pagamento parcial | CA-04, CA-05 | Passou |
| A2 — Cadastro manual | CA-01 | Passou |
| A3 — Vencimento | CA-10, CA-11 | Passou |
| A4 — Estorno | CA-13, CA-14, `test_A4_*` (unidades, 3 testes) | Passou |
| A5 — Cancelamento | CA-18 | Passou |
| A6 — Consulta | CA-20, CA-21, `test_A6_consulta_apresenta_o_que_o_operador_precisa_para_decidir` (usab.) | Passou |
| E1 — Valor inválido | CA-06, CA-07; `test_E1_*` (exceções), inclusive `NaN`, infinito, `float` e texto | Passou após a correção de #70 |
| E2 — Estado que não aceita pagamento | CA-08, CA-09 | Passou |
| E3 — Estorno por quem não é Dono | CA-15 | Passou |
| E4 — Motivo ausente | CA-16, CA-18, `test_RF_31_motivo_em_branco_equivale_a_ausente`; `test_E4_*` (exceções) | Passou após a correção de #70 |
| E5 — Pagamento já estornado | CA-17; `test_E5_pagamento_de_outro_titulo_nao_e_estornado` (exceções) | Passou |
| E6 — Cancelamento de título Baixado | CA-19 | Passou |
| E7 — Dados inválidos no cadastro | CA-02; `test_E7_*` (exceções) | Passou após a correção de #70 |
| E8 — Falha durante a operação | CA-23, `test_RNF_09_*` (confiab.) | Passou |
| "Toda recusa informa o motivo e não altera nenhum dado" | `test_RNF_14_cada_recusa_informa_o_campo_ou_a_condicao` (usab.); `test_recusa_nao_grava_auditoria` (integração) | Passou |

## 3. Invariantes da Spec 006

| Invariante | Testes | Resultado |
|---|---|---|
| INV-1 — saldo = valor − pagamentos não estornados | CA-24; `test_INV_1_*` (unidades); `test_INV_1_a_INV_6_*` (invariantes, 200 sequências) | Passou |
| INV-2 — 0 ≤ saldo ≤ valor | CA-24; `test_INV_1_a_INV_6_*` (invariantes) | Passou |
| INV-3 — Baixado ⇔ saldo zero | CA-24; CA-05; `test_RB_22_um_centavo_de_saldo_impede_a_baixa` (invariantes) | Passou |
| INV-4 — um estado, só por transição válida | `test_RB_21_*` (regras); `test_RB_21_cada_operacao_em_cada_estado` (invariantes, 4 estados × 5 operações); `test_INV_4_*` (invariantes) | Passou |
| INV-5 — valor não muda | `test_RB_21_valor_do_titulo_nao_muda_com_pagamentos`; `test_INV_1_a_INV_6_*` (invariantes) | Passou |
| INV-6 — pagamento não é apagado | Revisão de código; `test_INV_1_a_INV_6_*` (invariantes) | Passou |
| INV-7 — auditoria na mesma transação | CA-22, CA-23; `test_INV_7_*` (confiab.) | Passou |
| INV-8 — regras no domínio | `test_RNF_19_regras_do_titulo_ficam_somente_no_dominio`, `test_ADR_001_*` (camadas) | Passou |

## 4. Requisitos da Spec 006

| Requisito | Critérios | Resultado |
|---|---|---|
| RF-20, RF-21 | CA-01, CA-02 | Passou |
| RF-22 | CA-21 | Passou |
| RF-23 | CA-20 | Passou |
| RF-24 | CA-10, CA-11 | Passou |
| RF-25, RF-26, RF-27 | CA-03 a CA-05, CA-12 | Passou |
| RF-30 | CA-13, CA-14 | Passou |
| RF-31 | CA-16, CA-18 | Passou |
| RF-68 | CA-06, CA-07 | Passou |
| RB-01 | CA-22; `test_RB_01_toda_mudanca_de_estado_tem_registro_de_auditoria` | Passou |
| RB-02 | CA-15 | Passou |
| RB-21 | CA-08, CA-09, CA-18, CA-19 | Passou |
| RB-22 | CA-03, CA-05 | Passou |
| RB-23 | CA-06, CA-07; `test_RB_23_limite_*`, `test_RB_23_saldo_restaurado_*` | Passou |
| RNF-09 | CA-23 | Passou |
| RNF-19 | `test_RNF_19_*`, `test_ADR_001_*` | Passou |

Requisitos de outros documentos verificados nesta rodada, fora dos critérios da spec: RNF-11 ([eficiência](eficiencia.md)) e RNF-14 ([usabilidade](usabilidade.md)).
