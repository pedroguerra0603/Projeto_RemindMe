# UC-11 — Apurar resultado

| | |
|---|---|
| **Ator principal** | Dono |
| **Atores de apoio** | Contador, Operador Financeiro |
| **Objetivo** | Saber o resultado de um período sem depender de fechamento manual. |
| **Gatilho** | O usuário solicita a apuração de um período. |
| **Regras de negócio** | RB-03, RB-06, RB-12 |
| **Requisitos** | RF-53 a RF-57, RF-82, RNF-11 |

## Pré-condições

- O usuário está autenticado com perfil Dono, Operador Financeiro ou Contador.

## Fluxo principal

1. O usuário informa o período e, se quiser, as categorias.
2. O sistema seleciona os lançamentos Classificados do período.
3. O sistema soma receitas e despesas por categoria e calcula o resultado.
4. O sistema apresenta a demonstração de resultado.
5. O sistema informa a quantidade e o valor dos lançamentos Pendentes de Classificação do período.

## Fluxos alternativos

- **A1 — Consulta só de receitas ou só de despesas.** No passo 1, o usuário escolhe apenas um tipo. O sistema apresenta os totais desse tipo por categoria.
- **A2 — Exportação.** Após o passo 4, o usuário exporta a demonstração em CSV (UC-14).

## Exceções

- **E1 — Período sem lançamentos.** No passo 2, o sistema apresenta resultado zero e informa que não há lançamentos no período.
- **E2 — Contador tenta alterar dados.** O sistema nega a operação (RB-03).

## Pós-condições

- Nenhum dado é alterado.
- O resultado apresentado considera todo pagamento e todo estorno já registrados (RB-06).
