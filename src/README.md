# src

Código do RemindMe, em Python 3.11, somente com a biblioteca padrão (OPEN-01).

A organização segue as camadas de [`docs/arquitetura.md`](../docs/arquitetura.md):

| Pacote | Camada | Regra |
|---|---|---|
| `remindme/dominio` | Domínio | Não importa nada das outras camadas (ADR-001) |
| `remindme/aplicacao` | Aplicação | Um serviço por caso de uso; transação, autorização e auditoria num único ponto (`execucao.py`); interfaces em `portas.py` |
| `remindme/infraestrutura` | Infraestrutura | Implementações das interfaces: SQLite (ADR-007), relógio do sistema e os dublês em memória dos testes |
| `remindme/apresentacao` | Apresentação | Interface web sobre WSGI (ADR-006); chama a aplicação e não conhece a infraestrutura |
| `remindme/entradas` | Entradas automáticas | Agendador da verificação de vencimento (DT-07) |
| `remindme/inicializacao.py`, `__main__.py`, `demonstracao.py` | Composição | Montagem das camadas, linha de comando (`python3 -m remindme`) e dados de demonstração |

Specs implementadas: [001](../.specify/specs/001-fundacao-camadas-e-auditoria.md), [002](../.specify/specs/002-autenticacao-e-autorizacao.md), [003](../.specify/specs/003-cadastro-de-clientes.md), [006](../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), [013](../.specify/specs/013-consulta-de-auditoria.md) e [017](../.specify/specs/017-interface-web.md).

Para iniciar a aplicação a partir da raiz do repositório: `python3 iniciar.py demonstracao` ([`docs/execucao.md`](../docs/execucao.md)).
