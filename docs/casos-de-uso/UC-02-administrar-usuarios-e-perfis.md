# UC-02 — Administrar usuários e perfis

| | |
|---|---|
| **Ator principal** | Administrador |
| **Atores de apoio** | — |
| **Objetivo** | Manter os usuários do sistema e o que cada perfil pode fazer. |
| **Gatilho** | O Administrador solicita o cadastro ou a alteração de um usuário ou de um perfil. |
| **Regras de negócio** | RB-01, RB-03 |
| **Requisitos** | RF-02, RF-03, RF-04, RF-05, RF-97, RNF-02 |

## Situação da implementação

**Implementado, exceto A3.** Specs 002 e 017: cadastro, perfil, inativação, ativação e matriz de permissões. A redefinição de senha (A3) é da Spec 020, aprovada e ainda não implementada.

## Pré-condições

- O Administrador está autenticado.

## Fluxo principal

1. O Administrador informa nome, e-mail, perfil e uma senha provisória do novo usuário (OPEN-35).
2. O sistema valida os dados e cria o usuário associado ao perfil.
3. O Administrador ajusta as permissões do perfil, quando necessário.
4. O sistema aplica as permissões às operações seguintes dos usuários desse perfil.
5. O sistema registra as alterações na auditoria.

## Fluxos alternativos

- **A1 — Alteração de usuário existente.** No passo 1, o Administrador seleciona um usuário e altera o perfil ou a situação (ativo ou inativo). O fluxo segue no passo 2.
- **A2 — Inativação.** O Administrador inativa um usuário. O usuário perde o acesso e seu histórico é preservado.
- **A3 — Redefinição de senha (OPEN-59).** O Administrador informa uma nova senha provisória para outro usuário, ativo ou inativo, inclusive outro Administrador. O sistema substitui a senha, marca-a como provisória, encerra as sessões desse usuário e registra a redefinição na auditoria, sem a senha (RF-97). Na entrada seguinte, o usuário troca a senha (UC-16, RF-98). A própria senha o Administrador troca pelo UC-16.

## Exceções

- **E1 — E-mail já cadastrado.** No passo 2, o sistema recusa o cadastro e informa o campo e o motivo (RNF-14).
- **E2 — Dados obrigatórios ausentes.** No passo 2, o sistema recusa o cadastro e indica os campos faltantes.

## Pós-condições

- Sucesso: usuário criado ou alterado, com exatamente um perfil; alteração auditada.
- Falha: nenhum dado é alterado.
