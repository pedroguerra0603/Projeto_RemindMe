# src

Código do RemindMe, em Python 3.11, somente com a biblioteca padrão (OPEN-01).

A organização segue as camadas de [`docs/arquitetura.md`](../docs/arquitetura.md):

| Pacote | Camada | Regra |
|---|---|---|
| `remindme/dominio` | Domínio | Não importa nada das outras camadas (ADR-001) |
| `remindme/aplicacao` | Aplicação | Um serviço por caso de uso; permissão, transação e auditoria; interfaces em `portas.py` |
| `remindme/infraestrutura` | Infraestrutura | Implementações das interfaces; por enquanto, em memória |

Specs implementadas: [006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md).
