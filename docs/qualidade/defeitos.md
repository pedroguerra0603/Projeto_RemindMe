# Registro de Defeitos — RemindMe

Issue #70. Problemas encontrados pelos testes desta rodada de qualidade, correção e nova execução dos testes afetados.

- **Data:** 2026-10-09.
- **Origem:** casos de exceção X-04 a X-06 ([exceções](excecoes.md), #68).
- **Ponto de correção:** `src/remindme/dominio/titulo.py`, no domínio, para valer para qualquer chamador (INV-8, ADR-001).

## 1. Defeitos

| ID | Defeito | Severidade | Requisito violado | Situação |
|---|---|---|---|---|
| D-01 | `Decimal("NaN")` ou `Decimal("sNaN")` como valor do título ou do pagamento gera `decimal.InvalidOperation` | Média | Spec 006, seção 4: "Toda recusa informa o motivo"; E1, E7 | Corrigido |
| D-02 | `Decimal("Infinity")` é aceito como valor do título: o título nasce com saldo infinito e nunca pode ser Baixado | Alta | E7; INV-3 deixa de ser alcançável | Corrigido |
| D-03 | Pagamento em `float` passa pelas validações, é anexado a `titulo.pagamentos` e só então o cálculo do saldo gera `TypeError`. O objeto do domínio fica com um pagamento inválido. Na aplicação, a unidade de trabalho desfaz a gravação, mas qualquer outro chamador do domínio (agendador, importação CSV) ficaria com o título corrompido | Alta | "Nenhum dado é alterado" (`OperacaoRecusada`); INV-1; INV-8 | Corrigido |
| D-04 | Valor em texto (`"100.00"`) ou `None` gera `TypeError` | Média | "Toda recusa informa o motivo"; RNF-14 | Corrigido |
| D-05 | Motivo que não é texto (`123`, lista) gera `AttributeError` | Baixa | E4; RF-31 | Corrigido |

Não é defeito, e sim lacuna da baseline: valor com mais de duas casas decimais é aceito. Foi registrado como **OPEN-20** e não foi alterado, para não preencher a lacuna sem decisão da equipe (regra 2 do CLAUDE.md).

## 2. Evidência antes da correção

Executado sobre `019fa45`, chamando o domínio diretamente:

```
titulo NaN      ERRO InvalidOperation [<class 'decimal.InvalidOperation'>]
titulo Inf      OK -> Infinity
titulo float    ERRO TypeError unsupported operand type(s) for -: 'float' and 'decimal.Decimal'
titulo str      ERRO TypeError '<=' not supported between instances of 'str' and 'decimal.Decimal'
pag NaN         ERRO InvalidOperation [<class 'decimal.InvalidOperation'>]
pag float       ERRO TypeError unsupported operand type(s) for +: 'decimal.Decimal' and 'float'
pagamentos apos float: [Pagamento(id='p', valor=0.1, ...)]
motivo int      ERRO AttributeError 'int' object has no attribute 'strip'
```

Suíte em `019fa45`: `Ran 132 tests ... OK (expected failures=3)`.

## 3. Correção

| Defeito | Alteração |
|---|---|
| D-01 a D-04 | Nova função `_exigir_decimal`, chamada por `Titulo.cadastrar_manual` e `Titulo.registrar_pagamento` antes de qualquer comparação: o valor precisa ser `Decimal` e finito, senão a operação é recusada com motivo. A verificação fica antes de anexar o pagamento, o que elimina a alteração parcial de D-03 |
| D-05 | `_exigir_motivo` passa a tratar motivo que não é texto como motivo ausente |

A ordem das verificações do pagamento continua a mesma da spec: primeiro o estado (E2), depois o valor (E1). Nenhum comportamento com entrada válida mudou.

## 4. Nova execução dos testes afetados

| Teste | Antes | Depois |
|---|---|---|
| `test_E7_cadastro_com_valor_invalido_e_recusado` (6 valores) | Falha esperada | Passou |
| `test_E1_pagamento_com_valor_invalido_e_recusado_sem_alterar_o_titulo` (6 valores) | Falha esperada | Passou |
| `test_E4_motivo_que_nao_e_texto_e_recusado` (2 valores) | Falha esperada | Passou |

A marcação `@unittest.expectedFailure` foi retirada dos três testes. Se o defeito voltar, a suíte falha.

## Regressão depois da correção

| Execução | Python 3.11 | Python 3.12 | Python 3.13 |
|---|---|---|---|
| 48 testes da linha de base (`b17b1ed`) contra o código corrigido | 48, passou | 48, passou | 48, passou |
| Suíte inteira | 132, passou | 132, passou | 132, passou |

Nenhuma regressão: o comportamento verificado da Spec 006 é o mesmo, e as entradas inválidas passaram a ser recusadas.
