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
| D-06 | Com mais de 28 dígitos significativos, o saldo é arredondado em silêncio: o título nasce com saldo diferente do valor e pagamentos de centavos não o alteram (issue #78) | Baixa | INV-1 (saldo = valor − pagamentos); RB-22 | Corrigido em 2026-10-23: valor com mais de 15 dígitos inteiros é recusado (OPEN-24). Teste `test_D_06_corrigido_*` |

| D-07 | Na consulta de auditoria, o Dono e o Contador viam links para a página de cada usuário (`/usuarios/<id>`) que respondiam 403, porque só quem administra usuários abre essas páginas | Baixa | RF-65 (apresentar apenas as funcionalidades do perfil) | Corrigido em 2026-11-25. Teste `test_RF_65_auditoria_so_liga_usuario_e_permissoes_para_quem_pode_abrir_essas_paginas` |
| D-08 | O campo de valor lia `1.000` como R$ 1,00, e não mil reais, e `1.234.56` como R$ 123.456,00; agrupamento malformado, como `1.2.3,4`, era aceito | Alta | RNF-14 (valor no formato brasileiro, como na ajuda do campo: "Por exemplo, 1.234,56") | Corrigido em 2026-11-25: o ponto é de milhar quando separa grupos de três algarismos, e agrupamento malformado é recusado. Teste `test_RNF_14_valor_le_o_ponto_de_milhar_como_no_brasil_e_recusa_agrupamento_malformado` |
| D-09 | Nos dados da empresa, telefone sem nenhum algarismo (`abc`) era apagado em silêncio, e a tela confirmava a gravação | Baixa | RNF-14 (a recusa indica o campo); OPEN-54 | Corrigido em 2026-11-25. Teste `test_OPEN_54_telefone_sem_nenhum_algarismo_e_recusado_e_nao_apagado_em_silencio` |

| D-10 | A preparação da demonstração falhava quando atravessava a meia-noite de São Paulo: o dia de referência era lido uma vez no início, mas o envio do orçamento gravava a data do relógio no momento do envio, e a decisão do cliente ficava anterior ao envio. Apareceu no CI (macOS, Python 3.11) à 00h00 de 2026-11-25 | Média | CA-19 da Spec 017 (A8); a suíte precisa ser confiável (RNF-19) | Corrigido em 2026-11-25: a preparação inteira usa um só instante (`RelogioCongelavel`, em `infraestrutura/relogio.py`). Teste `test_CA_19_A8_demonstracao_preparada_na_virada_da_meia_noite_nao_falha` |

| D-11 | No histórico e na auditoria, o item do orçamento e a decisão do desconto apareciam no formato canônico, como `2 × 1000` e `aprovado 12.00% de 20.00% solicitados`, e não no brasileiro | Baixa | RNF-14; RF-05 | Corrigido em 2026-11-25, só na exibição: a auditoria continua guardando o valor canônico. Teste `test_RF_05_historico_mostra_item_e_decisao_do_desconto_no_formato_brasileiro` |

D-07 a D-09 foram encontrados na revisão de 2026-11-25, D-10 no CI do PR dessa revisão e D-11 ao ensaiar o roteiro da apresentação no navegador, antes da apresentação: navegação por todas as páginas com os quatro perfis, em 1280 e 360 px de largura, e cerca de 3.000 envios de formulário com valores inválidos (texto, vazio, negativo, `NaN`, `1e999`, datas inexistentes, HTML, 5.000 caracteres). Nenhum envio gerou erro inesperado (500).

Detalhes do D-06 em [acurácia monetária](acuracia-monetaria.md), seção 3. Foi corrigido depois da decisão do limite de valor (OPEN-24).

Valor com mais de duas casas decimais era aceito por lacuna da baseline (**OPEN-20**). Desde a decisão de 2026-10-23, é recusado, sem arredondamento.

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
