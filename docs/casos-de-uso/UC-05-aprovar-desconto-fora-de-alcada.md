# UC-05 — Aprovar desconto fora de alçada

| | |
|---|---|
| **Ator principal** | Dono |
| **Atores de apoio** | Operador Financeiro |
| **Objetivo** | Decidir sobre um desconto maior que a alçada de quem elaborou o orçamento. |
| **Gatilho** | Um orçamento passa ao estado Pendente de Alçada (UC-04, A1). |
| **Regras de negócio** | RB-01, RB-15 |
| **Requisitos** | RF-14 a RF-18, RNF-03 |

## Pré-condições

- O orçamento está Pendente de Alçada.
- O Dono está autenticado.

## Fluxo principal

1. O sistema apresenta ao Dono o orçamento, o desconto solicitado e a alçada de quem o elaborou.
2. O Dono aprova o desconto.
3. O sistema registra o responsável, a decisão e a data.
4. O sistema devolve o orçamento ao estado Rascunho, com o desconto aprovado, liberado para envio.

## Fluxos alternativos

- **A1 — Dono rejeita.** No passo 2, o Dono rejeita. O sistema registra a decisão e devolve o orçamento a Rascunho com o desconto anterior.
- **A2 — Dono aprova um desconto menor.** No passo 2, o Dono informa outro percentual. O sistema registra o valor solicitado e o valor aprovado (RF-18).

## Exceções

- **E1 — Usuário sem perfil Dono.** Se outro perfil tentar decidir, o sistema nega a operação (RNF-03).
- **E2 — Orçamento já cancelado.** Se o orçamento for cancelado antes da decisão, o sistema informa que não há pendência.

## Pós-condições

- Sucesso: decisão registrada; orçamento em Rascunho com o desconto resultante.
- Falha: orçamento permanece Pendente de Alçada.
