# UC-01 — Autenticar usuário

| | |
|---|---|
| **Ator principal** | Usuário de qualquer perfil (Dono, Operador Financeiro, Contador, Cliente, Administrador) |
| **Atores de apoio** | — |
| **Objetivo** | Acessar o sistema e ver apenas as funcionalidades do próprio perfil. |
| **Gatilho** | O usuário abre o sistema sem sessão ativa. |
| **Regras de negócio** | RB-03, RB-26 |
| **Requisitos** | RF-65, RF-66, RF-67, RNF-01, RNF-02, RNF-04, RNF-05, RNF-17, RNF-25 |

## Pré-condições

- O usuário está cadastrado, ativo e associado a um perfil.

## Fluxo principal

1. O usuário informa e-mail e senha.
2. O sistema valida as credenciais.
3. O sistema inicia a sessão e identifica o perfil do usuário.
4. O sistema apresenta o painel do perfil, com as pendências que cabem a ele.

## Fluxos alternativos

- **A1 — Sessão já ativa.** No passo 1, o sistema reconhece a sessão e segue direto para o passo 4.

## Exceções

- **E1 — Credenciais inválidas.** No passo 2, o sistema recusa o acesso com mensagem genérica, sem indicar qual campo está errado (RF-66).
- **E2 — Usuário inativo.** No passo 2, o sistema recusa o acesso e orienta a procurar o Administrador.
- **E3 — Operação não permitida.** Depois de autenticado, se o usuário solicitar uma operação fora do seu perfil, o sistema nega e informa o motivo (RF-67).

## Pós-condições

- Sucesso: sessão ativa, associada ao usuário e ao perfil.
- Falha: nenhuma sessão é criada.
