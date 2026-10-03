# UC-12 — Consultar auditoria

| | |
|---|---|
| **Ator principal** | Dono |
| **Atores de apoio** | Contador, Administrador |
| **Objetivo** | Saber quem fez o quê e quando. |
| **Gatilho** | O usuário solicita o histórico de operações ou de um registro específico. |
| **Regras de negócio** | RB-01, RB-30 |
| **Requisitos** | RF-04, RF-05, RF-61, RF-62, RF-64, RNF-06 |

## Pré-condições

- O usuário está autenticado com perfil Dono, Contador ou Administrador.

## Fluxo principal

1. O usuário informa filtros por usuário, período e tipo de operação.
2. O sistema apresenta os registros de auditoria em ordem cronológica.
3. Cada registro mostra usuário, data e hora, operação e registro afetado.
4. Para alterações, o sistema mostra o valor anterior, o novo valor e o motivo, quando houver.

## Fluxos alternativos

- **A1 — Histórico de um registro.** O usuário abre um orçamento, título, obrigação ou lançamento e consulta apenas o histórico dele.

## Exceções

- **E1 — Sem resultados.** No passo 2, o sistema informa que não há registros para os filtros.
- **E2 — Perfil sem permissão.** O sistema nega a consulta ao Operador Financeiro e ao Cliente (RNF-02).
- **E3 — Tentativa de alterar registro de auditoria.** O sistema nega a operação para qualquer perfil (RB-30).

## Pós-condições

- Nenhum dado é alterado.
