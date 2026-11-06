# UC-16 — Trocar a própria senha

| | |
|---|---|
| **Ator principal** | Usuário de qualquer perfil (Dono, Operador Financeiro, Contador, Administrador) |
| **Atores de apoio** | — |
| **Objetivo** | Substituir a própria senha, como a provisória recebida do Administrador ou uma que pode ter vazado. |
| **Gatilho** | O usuário autenticado pede para trocar a senha. |
| **Regras de negócio** | — |
| **Requisitos** | RF-95, RF-96, RF-04, RNF-01, RNF-04, RNF-09, RNF-14 |

Incluído em 2026-11-06 (OPEN-58). Spec 019.

## Pré-condições

- O usuário está autenticado (UC-01) e ativo.
- Nenhuma permissão da matriz é exigida: a troca vale para todo usuário ativo (OPEN-58).

## Fluxo principal

1. O usuário informa a senha atual, a nova senha e a confirmação da nova.
2. O sistema confere a senha atual.
3. O sistema valida a nova senha e a confirmação.
4. O sistema substitui a senha, encerra as demais sessões do usuário e mantém a sessão em uso.
5. O sistema registra a troca na auditoria, sem a senha.

## Fluxos alternativos

- **A1 — Sem outras sessões.** No passo 4, só a senha muda.

## Exceções

- **E1 — Senha atual incorreta.** No passo 2, o sistema recusa a troca, e nada muda (RF-96).
- **E2 — Nova senha inválida, confirmação diferente ou nova senha igual à atual.** No passo 3, o sistema recusa a troca e indica os campos (RNF-14).

## Pós-condições

- Sucesso: só a nova senha permite entrar; só a sessão em uso continua aberta; a troca está na auditoria.
- Falha: nenhum dado é alterado.
