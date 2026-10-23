# Plano técnico — Spec 013

Spec: [013 — Consulta de auditoria](../specs/013-consulta-de-auditoria.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01). Testes com `unittest`, sem interface.

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Aplicação | `aplicacao/servico_auditoria.py` | `FiltroAuditoria`, `VisaoRegistro`, `OpcoesDeFiltro`; consulta e opções de filtro, com a permissão "Consultar auditoria" |
| Aplicação | `aplicacao/portas.py` | `RepositorioAuditoria.listar`, só de leitura |
| Aplicação | `aplicacao/tempo.py` | Data e hora no fuso de referência (OPEN-26) |
| Infraestrutura | `infraestrutura/memoria.py` | `AuditoriaEmMemoria.listar` |

## Decisões locais

- **Filtro na aplicação.** O repositório devolve os registros na ordem de gravação e a aplicação aplica os filtros. Basta para o volume de uma empresa pequena; com muitos registros, o filtro desce para a consulta do banco sem mudar o serviço.
- **Período pela data local.** O registro guarda a hora em UTC; o filtro compara a data no fuso de referência, para que um registro das 23h30 em São Paulo conte no dia certo.
- **Histórico de um registro (A1).** O filtro `registro` aceita a referência exata e as que começam por ela seguida de vírgula, o que traz os pagamentos de um título.
- **Responsável.** O nome vem do cadastro de usuários; a operação automática aparece como "Sistema", com a rotina.
- **A permissão vem antes da validação do período**, para quem não pode consultar não receber nenhuma outra informação.

## Tarefas

Em [`../tasks/013-tarefas.md`](../tasks/013-tarefas.md).
