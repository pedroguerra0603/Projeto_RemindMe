# UC-03 — Manter clientes

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Dono |
| **Objetivo** | Manter os dados dos clientes que recebem orçamentos e devem títulos. |
| **Gatilho** | O usuário solicita o cadastro ou a alteração de um cliente. |
| **Regras de negócio** | RB-01 |
| **Requisitos** | RF-01, RF-04, RF-05, RNF-14 |

## Pré-condições

- O usuário está autenticado com perfil Operador Financeiro ou Dono.

## Fluxo principal

1. O usuário informa nome, documento e contato do cliente.
2. O sistema valida os dados.
3. O sistema cria o cliente.
4. O sistema registra a operação na auditoria.

## Fluxos alternativos

- **A1 — Alteração.** O usuário seleciona um cliente e altera seus dados. O sistema guarda o valor anterior e o novo valor de cada campo (RF-05).
- **A2 — Consulta.** O usuário pesquisa clientes por nome ou documento e consulta seus orçamentos e títulos.

## Exceções

- **E1 — Documento inválido ou já cadastrado.** No passo 2, o sistema recusa o cadastro e informa o campo e o motivo.
- **E2 — Dados obrigatórios ausentes.** No passo 2, o sistema recusa o cadastro e indica os campos faltantes.

## Pós-condições

- Sucesso: cliente disponível para orçamentos e títulos; operação auditada.
- Falha: nenhum dado é alterado.
