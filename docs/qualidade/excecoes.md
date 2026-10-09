# Casos de Teste de Exceção — RemindMe

Issue #68. Comportamento do sistema diante de entradas inválidas, referências inexistentes, falhas e situações inesperadas. Regra de referência, da Spec 006 (seção 4): **toda recusa informa o motivo e não altera nenhum dado**.

- **Data:** 2026-10-09.
- **Testes:** [`tests/aplicacao/test_excecoes.py`](../../tests/aplicacao/test_excecoes.py). As falhas de infraestrutura estão em [confiabilidade](confiabilidade.md) e as exceções E1 a E8 da spec, na [matriz](matriz-criterios-de-aceite.md).

## 1. Casos de teste

| ID | Cenário | Entrada | Resultado esperado | Teste | Resultado |
|---|---|---|---|---|---|
| X-01 | Operação sobre título inexistente | Pagamento, estorno e cancelamento com id desconhecido | Recusa "Título não encontrado"; nenhuma auditoria | `test_titulo_inexistente_e_recusado_em_toda_operacao` | Passou |
| X-02 | Estorno de pagamento que pertence a outro título | Id de pagamento do título A no título B | Recusa "Pagamento não encontrado"; o pagamento de A continua válido | `test_E5_pagamento_de_outro_titulo_nao_e_estornado` | Passou |
| X-03 | Cadastro com cliente vazio | `""` e `None` | Recusa | `test_E7_cliente_vazio_e_recusado` | Passou |
| X-04 | Cadastro com valor que não é número decimal finito | `NaN`, `sNaN`, infinito, `float`, texto, `None` | Recusa com motivo | `test_E7_cadastro_com_valor_invalido_e_recusado` | **Falhou**: D-01, D-02, D-04 |
| X-05 | Pagamento com valor que não é número decimal finito | Idem | Recusa com motivo; título inalterado | `test_E1_pagamento_com_valor_invalido_e_recusado_sem_alterar_o_titulo` | **Falhou**: D-01, D-03, D-04 |
| X-06 | Motivo que não é texto | `123`, lista | Recusa por motivo ausente (E4) | `test_E4_motivo_que_nao_e_texto_e_recusado` | **Falhou**: D-05 |
| X-07 | Motivo só com espaços, tabulação ou quebra de linha | `" "`, `"\n\t"` | Recusa no estorno e no cancelamento | `test_E4_motivo_so_com_espacos_e_quebras_de_linha_e_recusado` | Passou |
| X-08 | Valor com mais de duas casas decimais | Pagamento de R$ 0,001 | Sem regra na baseline. Hoje é aceito | `test_E1_valor_com_mais_de_duas_casas_e_aceito_ate_decisao_de_OPEN_20` | Registrado como **OPEN-20** |
| X-09 | Valor alto | Título de R$ 123.456.789.012,34 | Saldo exato ao centavo; baixa no último centavo | `test_E1_valor_alto_nao_perde_precisao` | Passou |
| X-10 | Pagamento com data um ano no futuro | Data = hoje + 365 dias | Sem regra na baseline. Hoje é aceito | `test_OPEN_17_pagamento_com_data_futura_e_aceito_ate_a_decisao` | Aguarda **OPEN-17** |
| X-11 | Verificação de vencimento com data anterior à última | Data de referência no passado | O título Vencido não volta a Aberto | `test_RF_24_verificacao_com_data_anterior_nao_desfaz_vencimento` | Passou |

Os testes de X-04 a X-06 foram escritos antes da correção, marcados com `@unittest.expectedFailure`, para que a suíte continuasse íntegra e o defeito ficasse visível no resultado ("expected failures=3"). A correção e a retirada da marcação são da issue #70.

## 2. Defeitos encontrados

| ID | Defeito | Caso |
|---|---|---|
| D-01 | `NaN` e `sNaN` no valor do título ou do pagamento geram `decimal.InvalidOperation`, um erro interno, em vez de recusa com motivo | X-04, X-05 |
| D-02 | Valor infinito é aceito no cadastro: cria um título com saldo infinito | X-04 |
| D-03 | Pagamento em `float` é anexado ao título e só depois gera `TypeError`: o objeto do domínio fica com um pagamento inválido | X-05 |
| D-04 | Valor em texto ou `None` gera `TypeError` em vez de recusa com motivo | X-04, X-05 |
| D-05 | Motivo que não é texto gera `AttributeError` em vez de recusa | X-06 |

Registro completo, correção e evidências: [defeitos](defeitos.md) (#70).

## 3. Questões abertas por este levantamento

| Questão | Registro |
|---|---|
| Valores monetários podem ter mais de duas casas decimais? Há arredondamento? | OPEN-20 em [`.specify/open.md`](../../.specify/open.md) |
| Pagamento com data futura | OPEN-17, já registrada |
