# src

Código do RemindMe, em Python 3.11, somente com a biblioteca padrão (OPEN-01).

A organização segue as camadas de [`docs/arquitetura.md`](../docs/arquitetura.md):

| Pacote | Camada | Regra |
|---|---|---|
| `remindme/dominio` | Domínio | Não importa nada das outras camadas (ADR-001) |
| `remindme/aplicacao` | Aplicação | Um serviço por caso de uso; permissão, transação e auditoria; interfaces em `portas.py` |
| `remindme/infraestrutura` | Infraestrutura | Implementações das interfaces: SQLite (`sqlite.py`), relógio real (`relogio.py`) e, para os testes, em memória |
| `remindme/apresentacao` | Apresentação | Interface web WSGI (`web.py`), linha de comando (`cli.py`) e montagem (`montagem.py`); sem regra de negócio |

Specs implementadas: [001](../.specify/specs/001-fundacao-camadas-e-auditoria.md), [002](../.specify/specs/002-autenticacao-e-autorizacao.md), [003](../.specify/specs/003-cadastro-de-clientes.md), [006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) e [017](../.specify/specs/017-interface-web.md).

A interface chama somente `aplicacao/sistema.py`, que autoriza cada operação antes de chamar o serviço do caso de uso.
