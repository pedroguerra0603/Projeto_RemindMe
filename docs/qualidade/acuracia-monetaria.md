# Acurácia dos Valores Monetários — RemindMe

Issue #78. Subcaracterística **Acurácia** (Adequação funcional, ISO/IEC 25010): resultados corretos, com a precisão esperada. Lições do Ariane 5 (1996), em que uma conversão numérica com estouro derrubou o foguete, e do Citibank (2020), em que um valor errado foi aceito como válido.

- **Data:** 2026-10-16.
- **Objeto:** Spec 006 (saldo, soma de pagamentos, estorno).
- **Requisitos e regras:** RF-23, RF-25, RF-26, RB-15, RB-23 (e RB-22, INV-1).
- **Testes:** [`tests/dominio/test_acuracia_monetaria.py`](../../tests/dominio/test_acuracia_monetaria.py) (16 testes: 13 passam, 2 pulados, 1 falha esperada).

## 1. Revisão do código: nenhum valor monetário usa `float`

| Verificação | Resultado |
|---|---|
| Revisão manual de `src/remindme/` | Valor do título, do pagamento e saldo são `Decimal` (`titulo.py`); `ZERO = Decimal("0.00")`; a soma usa `sum(..., ZERO)`, que parte de `Decimal` |
| Verificação automática | O teste lê a árvore sintática de todo o código de produção e falha se houver literal `float`, uso da palavra `float` ou divisão com `/` (`test_RF_25_codigo_de_producao_nao_usa_float`) |
| Anotação de tipo | Todo campo ou parâmetro `valor` ou `saldo` declara `Decimal` (`test_RF_25_valor_monetario_e_anotado_como_decimal`). O `valor` de `__exit__` é a exceção em curso, e não dinheiro |
| Entrada em `float` | O domínio recusa `float` com motivo, antes de qualquer cálculo (defeitos D-03 e D-04, já corrigidos) |

## 2. Casos de teste

| Caso | Teste | Resultado |
|---|---|---|
| 3 × R$ 33,33 sobre R$ 100,00: saldo restante de R$ 0,01, título ainda Aberto | `test_RB_23_tres_pagamentos_de_33_33_...` | Passou |
| O centavo restante baixa o título; R$ 0,02 é recusado | `test_RB_22_o_centavo_restante_...`, `test_RB_23_o_saldo_de_um_centavo_...` | Passou |
| 100 × R$ 0,01 somam R$ 1,00 exato; 10 × R$ 0,10 baixam R$ 1,00 (em `float`, 0,1 × 10 não fecha) | `test_RF_25_cem_pagamentos_...`, `test_RB_23_dez_pagamentos_...` | Passou |
| Estorno devolve o valor exato; o novo pagamento baixa | `test_RF_30_estorno_devolve_o_valor_exato_ao_saldo` | Passou |
| A ordem dos pagamentos não muda o saldo | `test_RF_25_ordem_dos_pagamentos_...` | Passou |
| Valor de 20 dígitos (R$ 99.999.999.999.999.999.999,99): centavo preservado, baixa exata | `test_RF_25_valor_de_vinte_digitos_...`, `test_RB_22_valor_de_vinte_digitos_...` | Passou |
| Valor de 28 dígitos significativos (26 inteiros + 2 casas) | `test_RF_25_valor_de_vinte_e_seis_digitos_...` | Passou |
| **Valor de 34 dígitos: o saldo é arredondado e o centavo se perde** | `test_D_06_valor_acima_de_28_digitos_...` | **Falha esperada: defeito D-06** |
| Desconto percentual (RB-15) | `test_RB_15_desconto_percentual_...` | Pendente da Spec 004 |
| Apuração do resultado (RF-51, UC-11) | `test_RF_51_apuracao_do_resultado_...` | Pendente da Spec 012 |

## 3. Achado: D-06, perda silenciosa de centavos acima de 28 dígitos

`Decimal` calcula com 28 dígitos significativos por padrão, e a soma e a subtração arredondam além disso. O construtor `Decimal("1000...0.01")` é exato, mas `titulo.saldo` (`valor - pago`) arredonda: um título de 34 dígitos nasce com saldo diferente do valor (INV-1), e pagamentos de centavos não alteram o saldo.

```
Titulo(valor=Decimal("1" + "0"*30 + ".01")).saldo  ->  1.000000000000000000000000000E+30   (o ".01" sumiu)
```

| Item | Avaliação |
|---|---|
| Severidade | Baixa: exige valor acima de 10²⁷, impossível para uma micro ou pequena empresa. Mas é a mesma classe de falha do Ariane 5: o número deixa de caber e o sistema não avisa |
| Por que não foi corrigido | Corrigir exige escolher um limite de valor (recusar acima de N dígitos) ou uma precisão. A baseline não define; a regra 2 do CLAUDE.md manda registrar e perguntar. Registrado como **OPEN-21**, com sugestão de recusar valor acima de 15 dígitos inteiros, com motivo |
| Como o defeito fica visível | O teste `test_D_06_...` está marcado `expectedFailure`. Quando a correção entrar, a suíte avisa com "unexpected success" e a marcação é retirada |

## 4. Regra de arredondamento

Não há arredondamento no sistema: toda operação monetária é soma ou subtração de `Decimal`, que são exatas dentro dos 28 dígitos. O sistema aceita valor com mais de duas casas (R$ 0,001), e então o saldo passa a ter três casas. Isso é a lacuna **OPEN-20**, já registrada em #68, que também trata da regra de arredondamento. Nenhuma `OPEN` nova foi criada para o arredondamento. Quando as Specs 004 (desconto percentual) e 012 (apuração) forem escritas, a divisão por percentual vai exigir a regra de arredondamento, e OPEN-20 precisa estar decidida antes.

## 5. Pendente

| Caso | Depende de |
|---|---|
| Desconto na alçada, um centavo acima e abaixo, sobre valor com centavos (R$ 33,33 × 10%) | Spec 004 (RB-15) |
| Soma de recebimentos e despesas ao centavo; estorno refletido no resultado sem resíduo | Spec 012 (RF-51, RF-55, UC-11) |
| Decisão do limite de valor e da precisão | OPEN-21 e OPEN-20 |
