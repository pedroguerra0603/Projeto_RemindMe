# Plano técnico — Spec 003

Spec: [003 — Cadastro de clientes](../specs/003-cadastro-de-clientes.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01). Testes com `unittest`, sem interface.

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Domínio | `dominio/cliente.py` | `Cliente`; validação de nome, documento (CPF e CNPJ, inclusive o alfanumérico, OPEN-40) e contato (OPEN-41); `alterado` devolve os campos que mudaram (A1) |
| Aplicação | `aplicacao/servico_clientes.py` | Cadastrar, alterar, pesquisar e obter; documento único (INV-1); auditoria campo a campo (INV-4) |
| Aplicação | `aplicacao/portas.py` | `RepositorioClientes`, que também responde se o cliente existe (INV-5) |
| Infraestrutura | `infraestrutura/memoria.py` | `RepositorioClientesEmMemoria`, incluído na unidade de trabalho |

## Decisões locais

- **Documento guardado sem pontuação**, só com letras maiúsculas e dígitos. O CNPJ alfanumérico usa o valor ASCII menos 48 de cada caractere no cálculo do módulo 11, o que mantém o CNPJ numérico como caso particular.
- **Contato normalizado:** e-mail em minúsculas; telefone só com os dígitos, sem o código do país 55.
- **Auditoria do cadastro:** um registro por campo, com o valor informado como novo valor (Spec 001, A1). Na alteração, só os campos que mudaram.
- **Pesquisa em memória** sobre a lista de clientes: basta para o volume de uma empresa pequena (RNF-11); com o banco, pode virar consulta SQL sem mudar o serviço.
- **Títulos do cliente** reaproveitam a consulta de títulos da Spec 006, com o filtro por cliente.

## Tarefas

Em [`../tasks/003-tarefas.md`](../tasks/003-tarefas.md).
