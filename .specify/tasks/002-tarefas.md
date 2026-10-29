# Tarefas — Spec 002

Derivadas do [plano](../plans/002-plano.md) da [Spec 002](../specs/002-autenticacao-e-autorizacao.md).

| # | Tarefa | Cobre | Situação |
|---|---|---|---|
| 1 | `Usuario` com e-mail e situação; validação do cadastro, troca de perfil e inativação | RF-02, INV-1, E7, A2, A3, OPEN-46 | Feita |
| 2 | Operações, células fixadas por regra e matriz de permissões | OPEN-32, OPEN-42, RB-02, RB-03, RB-15, RB-26, OPEN-16, INV-4, E5 | Feita |
| 3 | Sessão guardada pelo resumo do identificador, com vencimento | OPEN-03, OPEN-43, RNF-01 | Feita |
| 4 | Autorização em um único ponto e execução de toda operação por ele | INV-2, INV-5, RNF-02, RNF-03 | Feita |
| 5 | Hash de senha por `scrypt` e senha mínima | RNF-04, INV-3, OPEN-33, OPEN-44 | Feita |
| 6 | Serviço de acesso: entrar, sair, usuários, permissões e primeiro Administrador | RF-65, RF-66, RF-03, UC-01, UC-02, OPEN-39, OPEN-45, OPEN-47 | Feita |
| 7 | Operações da Spec 006 com sessão; verificação automática de vencimento separada | INV-2, Spec 001 A4 | Feita |
| 8 | Migração dos testes existentes para sessões abertas no dublê | — | Feita |
| 9 | Testes de aceite CA-01 a CA-16 e das decisões; testes de domínio da matriz | Seção 6 | Feita |
| 10 | Registrar o resultado na seção 8 da spec | Fluxo, passo 6 | Feita |
