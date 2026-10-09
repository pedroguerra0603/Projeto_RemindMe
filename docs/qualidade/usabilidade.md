# Avaliação de Usabilidade — RemindMe

Issue #52. Característica **Usabilidade** da ISO/IEC 25010: facilidade de compreensão, de aprendizado e de operação, proteção contra erro do usuário.

- **Data:** 2026-10-09.
- **Limite da avaliação:** o sistema ainda não tem interface, porque o framework web depende de OPEN-01. O que o usuário já recebe são as **mensagens de recusa** e os **dados da consulta** de títulos (A6). Essas partes foram avaliadas e testadas. As telas têm cenários definidos aqui, para serem executados quando existirem.
- **Requisitos de referência:** RNF-14 (campo e motivo da recusa), RNF-15 (destaque de Vencidos), RNF-16 (estado em toda tela), RNF-17 (painel por perfil), RF-27 (saldo restante).
- **Testes:** [`tests/aplicacao/test_usabilidade.py`](../../tests/aplicacao/test_usabilidade.py).

## 1. Checklist sobre o que existe

| # | Item | Resultado | Evidência |
|---|---|---|---|
| U-01 | Toda recusa informa o motivo, em português | Atende | `test_RNF_14_cada_recusa_informa_o_campo_ou_a_condicao`, 13 cenários |
| U-02 | Toda recusa nomeia o campo ou a condição que a causou (valor, vencimento, cliente, saldo, estado, motivo, perfil) | Atende | Idem |
| U-03 | Recusa por saldo informa quanto ainda pode ser pago | Atende | `test_RNF_14_recusa_por_saldo_informa_o_saldo_disponivel` |
| U-04 | Recusa de cancelamento de título Baixado diz o que fazer ("Estorne os pagamentos antes") | Atende | Cenário "cancelamento de título Baixado" |
| U-05 | Pagamento parcial devolve o saldo restante (RF-27) | Atende | `test_RF_27_pagamento_parcial_devolve_o_saldo_restante` |
| U-06 | A consulta traz valor, saldo, vencimento, estado e sinalização, sem o usuário calcular nada (A6) | Atende | `test_A6_consulta_apresenta_o_que_o_operador_precisa_para_decidir` |
| U-07 | O estado é apresentado com o nome do glossário ("Aberto", "Vencido", "Baixado", "Cancelado") | Atende | `EstadoTitulo.value` |
| U-08 | Recusa por perfil não revela se o título existe | Atende | A permissão é verificada antes de buscar o título |
| U-09 | Mensagens sem jargão interno | **Parcial** | Algumas mensagens terminam com o identificador da regra, por exemplo "(RB-23)" ou "(OPEN-18)". Útil para a equipe, sem sentido para o Diego (Operador Financeiro) |
| U-10 | Valores no formato brasileiro (R$ 600,00) | **Não atende** | A mensagem de saldo mostra "600.00". A formatação é responsabilidade da apresentação, que ainda não existe |
| U-11 | Entrada inválida (texto, número não finito) gera recusa compreensível | **Não atendia** | Gerava erro interno do Python. Defeitos D-01 a D-04, corrigidos em #70 |

## 2. Cenários para quando houver interface

Cada cenário segue a persona e a tarefa mais frequente do perfil ([personas](../personas.md)). Critério: concluído sem ajuda, sem erro e no número de passos indicado.

| ID | Persona | Tarefa | Critério de sucesso | Requisito |
|---|---|---|---|---|
| CU-01 | Diego, Operador Financeiro | Registrar um pagamento parcial a partir do painel | Até 3 passos; o saldo restante aparece na confirmação | RF-27, RNF-17 |
| CU-02 | Diego | Tentar registrar pagamento maior que o saldo | A tela aponta o campo valor e mostra o saldo disponível | RNF-14 |
| CU-03 | Diego | Encontrar os títulos Vencidos de um cliente | Filtro por cliente e estado em uma única tela; Vencidos destacados | RF-22, RNF-15 |
| CU-04 | Carla, Dona | Estornar um pagamento com cheque devolvido | O motivo é obrigatório e a tela mostra o novo estado do título | RF-30, RF-31, RNF-16 |
| CU-05 | Carla | Cancelar um título Baixado | A recusa explica que é preciso estornar antes | E6 |
| CU-06 | Sérgio, Cliente | Ver quanto deve e até quando | Só os próprios títulos, com saldo e vencimento | RNF-25, Spec 009 |
| CU-07 | Helena, Contadora | Consultar títulos sem conseguir alterá-los | Nenhum botão de alteração aparece | RB-03, Spec 002 |
| CU-08 | Qualquer perfil | Entrar no sistema | O painel do perfil aparece sem navegação adicional | RNF-17, Spec 016 |

## 3. Recomendações

| Recomendação | Onde tratar |
|---|---|
| Separar o código da regra do texto da mensagem: `OperacaoRecusada` ganha um campo `regra` (ex.: "RB-23"), e o texto para o usuário fica sem identificador | Proposta para a equipe; não altera comportamento da Spec 006 |
| Formatar valores como moeda brasileira e datas como dd/mm/aaaa na apresentação | Primeira spec com interface |
| Indicar o campo de forma estruturada (ex.: `campo="valor"`) para a tela destacar o campo certo | Proposta para a equipe, junto da anterior |
| Executar CU-01 a CU-08 com uma pessoa de fora da equipe, cronometrando e anotando erros | Após a primeira interface |
