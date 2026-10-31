# UC-15 — Gerenciar contas a pagar

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Dono, Agendador |
| **Objetivo** | Pagar no prazo o que a empresa deve aos fornecedores e saber quanto vai sair do caixa. |
| **Gatilho** | A empresa compra a prazo de um fornecedor, ou chega a data de pagar. |
| **Regras de negócio** | RB-01, RB-03, RB-31, RB-32, RB-33 |
| **Requisitos** | RF-87 a RF-94 |

Incluído em 2026-10-31 (OPEN-56). Spec 018.

## Pré-condições

- O usuário está autenticado com perfil que tem a permissão da operação (Spec 002).

## Fluxo principal

1. O usuário cadastra o fornecedor com nome, CPF ou CNPJ e contato, ou escolhe um já cadastrado.
2. O usuário cadastra a conta a pagar com fornecedor, descrição, valor, vencimento e forma de pagamento.
3. O sistema cria a conta no estado Aberta, com saldo igual ao valor.
4. O sistema apresenta a conta na lista e no painel, ao lado do que há a receber.
5. O usuário registra o pagamento com valor e data.
6. Quando o saldo chega a zero, o sistema muda o estado para Paga.

## Fluxos alternativos

- **A1 — Pagamento parcial.** No passo 6, o saldo continua maior que zero; a conta segue Aberta ou Vencida.
- **A2 — Vencimento.** O agendador muda para Vencida a conta Aberta cujo vencimento passou (RF-90).
- **A3 — Estorno.** O Dono estorna um pagamento com motivo; o saldo é restaurado (RF-92, RB-33).
- **A4 — Cancelamento.** O Dono cancela a conta Aberta ou Vencida com motivo (RF-93, RB-33).

## Exceções

- **E1 — Dados inválidos.** O sistema recusa e indica os campos (RNF-14).
- **E2 — Pagamento maior que o saldo, zero, com data futura ou em conta Paga ou Cancelada.** O sistema recusa (RB-31, RB-32).
- **E3 — Estorno ou cancelamento por quem não é Dono, ou sem motivo.** O sistema recusa (RB-33).

## Pós-condições

- Sucesso: conta Paga, com os pagamentos e a auditoria de cada operação.
- Atraso: conta Vencida, destacada no painel até ser paga ou cancelada.
