# UC-16 — Trocar a própria senha

| | |
|---|---|
| **Ator principal** | Usuário de qualquer perfil (Dono, Operador Financeiro, Contador, Administrador) |
| **Atores de apoio** | — |
| **Objetivo** | Substituir a própria senha, como a provisória recebida do Administrador ou uma que pode ter vazado. |
| **Gatilho** | O usuário autenticado pede para trocar a senha. |
| **Regras de negócio** | — |
| **Requisitos** | RF-95, RF-96, RF-98, RF-04, RNF-01, RNF-04, RNF-09, RNF-14 |

Incluído em 2026-11-06 (OPEN-58). Spec 019.

## Situação da implementação

**Implementado, exceto A2.** Spec 019. A troca obrigatória da senha provisória (A2) é da Spec 020, aprovada e ainda não implementada.

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
- **A2 — Senha provisória (OPEN-60).** Enquanto a senha for provisória, informada pelo Administrador no cadastro (UC-02) ou na redefinição (UC-02, A3), o usuário só pode trocar a senha, sair e consultar a sessão; toda outra operação é recusada, e a interface o leva à troca (RF-98). Depois da troca, a senha deixa de ser provisória.

## Exceções

- **E1 — Senha atual incorreta.** No passo 2, o sistema recusa a troca, e nada muda (RF-96).
- **E2 — Nova senha inválida, confirmação diferente ou nova senha igual à atual.** No passo 3, o sistema recusa a troca e indica os campos (RNF-14).

## Pós-condições

- Sucesso: só a nova senha permite entrar; só a sessão em uso continua aberta; a troca está na auditoria.
- Falha: nenhum dado é alterado.
