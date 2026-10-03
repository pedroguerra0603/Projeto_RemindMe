# Registros de Decisão de Arquitetura (ADR)

Um ADR registra uma decisão cara de reverter: o que foi decidido, por quê, que alternativas foram consideradas e quais as consequências. Decisão barata de desfazer não precisa de ADR.

| ADR | Decisão | Situação |
|---|---|---|
| [ADR-001](ADR-001-monolito-em-camadas-com-dominio-isolado.md) | Monólito em camadas com domínio isolado | Proposto |
| [ADR-002](ADR-002-canal-de-notificacao-substituivel.md) | Canal de notificação substituível, simulado por padrão | Proposto |
| [ADR-003](ADR-003-ia-extrai-e-classifica-o-sistema-decide.md) | A IA extrai e classifica; o sistema decide | Proposto |
| [ADR-004](ADR-004-auditoria-somente-inclusao.md) | Auditoria somente de inclusão, na mesma transação | Proposto |

Situações possíveis: Proposto, Aceito, Substituído por ADR-nnn, Rejeitado. Um ADR aceito não é editado; uma nova decisão gera um novo ADR que substitui o anterior.

Para criar um ADR, copie [`modelo.md`](modelo.md) e use o próximo número.
