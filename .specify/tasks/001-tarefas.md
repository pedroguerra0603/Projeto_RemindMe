# Tarefas — Spec 001

Derivadas do [plano](../plans/001-plano.md) da [Spec 001](../specs/001-fundacao-camadas-e-auditoria.md).

| # | Tarefa | Cobre | Situação |
|---|---|---|---|
| 1 | `RegistroAuditoria` com campo alterado, indicação de operação automática e rotina; validação de INV-3 | RF-05, RF-62, INV-3, A4 | Feita |
| 2 | Ponto único de auditoria na aplicação, com transação, recusa e erro não tratado | INV-2, INV-5, E1, E2, E3, E5, RNF-21 | Feita |
| 3 | Porta e dublê em memória do registro de erro, fora da transação | RNF-21, CA-10 | Feita |
| 4 | Leitura da auditoria em memória por cópia, sem atribuição nem exclusão | RB-30, RNF-06, CA-07, CA-08 | Feita |
| 5 | Operações da Spec 006 sobre o ponto único: cadastro, pagamento, vencimento, estorno e cancelamento | RF-04, RF-61, A1, A2, A3, A5 | Feita |
| 6 | Verificação de vencimento sem usuário, como rotina automática | A4, CA-09, OPEN-30 | Feita |
| 7 | Ajuste dos testes da Spec 006 ao novo registro do pagamento | Spec 006, CA-22 | Feita |
| 8 | Testes de aceite CA-01 a CA-13 e testes de INV-3 e INV-5 | Seção 6 | Feita |
| 9 | Registrar o resultado na seção 8 da spec | Fluxo, passo 6 | Feita |
