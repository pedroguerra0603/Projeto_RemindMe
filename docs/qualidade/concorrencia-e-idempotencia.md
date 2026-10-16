# Concorrência e Idempotência — RemindMe

Issue #76. Lições dos casos Americanas (2023), em que cliques repetidos em "Finalizar compra" duplicaram o pedido, e ViaQuatro (2022), em que um pagamento liberou vários bilhetes. No RemindMe, o risco equivalente é registrar duas vezes o mesmo pagamento, baixar o título duas vezes ou repetir uma etapa da régua.

- **Data:** 2026-10-16.
- **Objeto:** Spec 006.
- **Requisitos e regras:** RF-25, RF-26, RF-30, RNF-09, RB-22, RB-23; DA-08, DA-09.
- **Testes:** [`tests/aplicacao/test_idempotencia.py`](../../tests/aplicacao/test_idempotencia.py) (13 testes: 11 passam, 2 pulados).

## 1. Casos de teste

As repetições são **em sequência, no mesmo processo**. A concorrência real, com duas transações ao mesmo tempo, depende do banco (seção 3).

| Critério da issue | Teste | Resultado |
|---|---|---|
| Dois pagamentos de R$ 60,00 sobre R$ 100,00 em sequência: o segundo é recusado (RB-23); nada muda no segundo pedido | `test_RB_23_segundo_pagamento_que_estoura_o_saldo_e_recusado` | Passou |
| Dois pagamentos que somam exatamente o saldo: baixa uma única vez, com um único registro de mudança de estado | `test_RB_23_dois_pagamentos_que_somam_exatamente_...` | Passou |
| Duplo clique no pagamento integral: o segundo é recusado porque o título já está Baixado (RB-21) | `test_RB_21_repetir_o_pagamento_integral_...` | Passou |
| 20 pedidos de R$ 30,00 sobre R$ 100,00: 3 aceitos, 17 recusados, saldo nunca negativo | `test_RB_23_muitas_repeticoes_...` | Passou |
| O mesmo estorno pedido duas vezes: o saldo volta a R$ 100,00 uma única vez; o segundo é recusado sem alterar nada | `test_RF_30_o_mesmo_estorno_pedido_duas_vezes_...` | Passou |
| Estorno repetido não gera segundo registro de auditoria | `test_RF_30_o_estorno_repetido_nao_gera_...` | Passou |
| Estornar, pagar de novo e tentar estornar o pagamento antigo: recusado | `test_RF_30_estornar_e_pagar_de_novo_...` | Passou |
| `verificar_vencimentos` duas vezes: muda e audita uma única vez | `test_RF_24_verificar_vencimentos_duas_vezes_...` | Passou |
| Falha na auditoria no meio do pagamento (depois da gravação): nada permanece (RNF-09) | `test_RNF_09_falha_na_auditoria_depois_da_gravacao_...` | Passou |
| Depois da falha, repetir o mesmo pagamento conta uma só vez | `test_RNF_09_apos_a_falha_...` | Passou |

A falha injetada em cada operação (cadastrar, pagar, estornar, cancelar, verificar vencimentos), na gravação e na auditoria, já é verificada em [confiabilidade](confiabilidade.md) (F-01 e F-02). Os testes novos acrescentam o caso do pagamento repetido depois da falha.

## 2. Achado: pagamento parcial repetido é registrado duas vezes (OPEN-22)

O que impede a duplicação hoje é o próprio saldo: um pagamento integral repetido é recusado (RB-21), e um que estoura o saldo é recusado (RB-23). Mas dois pedidos **iguais e parciais** (por exemplo, dois de R$ 30,00 por duplo clique) são indistinguíveis de dois pagamentos reais, e os dois são registrados. É a lacuna do tipo Americanas: a regra de saldo protege o título contra pagar a mais, mas não contra pagar duas vezes o mesmo valor parcial.

Não é defeito da Spec 006: nenhum requisito pede identificação de pedido repetido, e a solução (chave de idempotência gerada pela interface) depende da interface (OPEN-01). Registrado como **OPEN-22**. O teste `test_OPEN_22_provisorio_...` caracteriza o comportamento atual e muda quando houver decisão.

## 3. Pendências e dependências

| Caso | Depende de | Observação |
|---|---|---|
| Execução repetida da régua não repete etapa (DA-08) | Spec 008 | Teste `test_DA_08_...` registrado como pulado, sem código antecipado (regra 1 do CLAUDE.md) |
| Duas transações simultâneas no mesmo título não estouram o saldo | OPEN-02 (banco) | `test_RNF_09_duas_transacoes_simultaneas_...` registrado como pulado |
| Chave de idempotência para pagamento parcial | OPEN-22 | Ver seção 2 |

**Por que a concorrência real não é testada agora.** A unidade de trabalho em memória guarda uma cópia e a restaura em caso de falha; ela não tem trava e **não é segura para threads**. Um teste com threads aqui mediria o dublê, e não o comportamento do sistema. A garantia real virá da transação e das restrições do banco (por exemplo, atualização condicional do saldo ou trava de linha), e a escolha é do banco (OPEN-02). A dependência fica registrada em vez de a solução ser escolhida agora.
