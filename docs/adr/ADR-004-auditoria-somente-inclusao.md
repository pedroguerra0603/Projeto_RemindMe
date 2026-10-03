# ADR-004 — Auditoria somente de inclusão, na mesma transação

- **Situação:** Proposto, aguardando aprovação da equipe
- **Data:** 2026-10-03
- **Decisores:** a definir pela equipe
- **Drivers:** DA-02, DA-03
- **Requisitos e regras:** RB-01, RB-30, RF-04, RF-05, RF-61, RF-62, RNF-06, RNF-09

## Contexto

O sistema arbitra tensões entre dono, operador, cliente e contador. Isso só funciona se for possível provar quem fez o quê e quando. Um registro de auditoria que pode ser editado, ou que pode faltar quando a operação ocorreu, não serve como prova.

## Decisão

1. Registros de auditoria só são incluídos. Não há operação de alteração nem de exclusão, para nenhum perfil.
2. O registro de auditoria é gravado na mesma transação da operação auditada. Se um falha, o outro é desfeito.
3. A gravação é feita pela camada de aplicação, em um único ponto, e não por cada tela.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Registrar auditoria em arquivo de log | Não é consultável pelo UC-12 e pode divergir do dado gravado. |
| Gravar a auditoria de forma assíncrona | Abre a possibilidade de operação sem registro. |
| Guardar apenas "última alteração" no próprio registro | Perde o histórico exigido por RF-05. |

## Consequências

- Positivas: toda mudança de estado tem prova; o UC-12 consulta uma única fonte.
- Negativas: a tabela de auditoria cresce sem limite; uma política de retenção terá de ser decidida depois.
- O que passa a ser obrigatório: nenhum serviço de aplicação altera estado sem registrar auditoria; há teste que verifica a recusa de alteração do registro.
