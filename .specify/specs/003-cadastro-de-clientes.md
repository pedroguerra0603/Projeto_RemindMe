# Spec 003 — Cadastro de clientes

## 1. Identificação

| | |
|---|---|
| **ID** | 003 |
| **Nome** | Cadastro de clientes |
| **Objetivo** | Manter os clientes que recebem orçamentos e devem títulos, com documento válido e único. |
| **Valor entregue** | O Operador cadastra o cliente uma vez e escolhe-o ao cadastrar títulos; toda alteração fica na auditoria. |
| **Situação** | Proposta — implementada em 2026-10-29 por pedido de Renan Gandolpho; aguarda aprovação da equipe |
| **Aprovada por** | *(nomes e data)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-01, RF-04, RF-05 |
| RB | RB-01, RB-03 |
| RNF | RNF-14 |
| UC | [UC-03](../../docs/casos-de-uso/UC-03-manter-clientes.md) |
| Entidades | `Cliente` |
| Drivers e ADRs | DA-01, DA-02 |
| Depende de | 001, 002 |

## 3. Escopo

### Incluído

- Cadastro com nome, documento (CPF ou CNPJ) e contato (e-mail e telefone, opcionais).
- Alteração, com auditoria de cada campo alterado.
- Pesquisa por nome ou documento.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Orçamentos do cliente | Specs 004 e 005 |
| Acesso do próprio cliente | Spec 009 |
| Importação em CSV | Spec 015 |

## 4. Comportamento

### Fluxo principal

1. O usuário informa nome, documento e contato.
2. O sistema valida os dados: nome obrigatório; documento obrigatório, com dígitos verificadores de CPF (11 dígitos) ou CNPJ (14 dígitos); e-mail e telefone, se informados, em formato válido.
3. O sistema cria o cliente, guardando o documento só com dígitos.
4. A operação é auditada.

### Fluxos alternativos

- **A1 — Alteração.** Um registro de auditoria por campo alterado, com valor anterior e novo (RF-05).
- **A2 — Consulta.** Pesquisa por parte do nome, sem diferenciar maiúsculas, ou por parte do documento.

### Exceções

- **E1 — Documento inválido ou já cadastrado.** Recusa com o campo e o motivo.
- **E2 — Dados obrigatórios ausentes.** Recusa indicando os campos.

## 5. Invariantes

| ID | Invariante |
|---|---|
| INV-1 | Não existem dois clientes com o mesmo documento. |
| INV-2 | Todo cliente tem nome e documento válido. |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Operador autenticado | cadastra um cliente com nome e CNPJ válido | o cliente é criado e a operação é auditada | RF-01, RB-01 |
| CA-02 | um cliente com o CNPJ 11.222.333/0001-81 | outro cliente é cadastrado com o mesmo número, sem pontuação | o cadastro é recusado no campo documento | E1, INV-1 |
| CA-03 | um Operador | cadastra sem nome e sem documento | a recusa indica os dois campos | E2, RNF-14 |
| CA-04 | um cliente | o nome e o telefone são alterados | a auditoria tem um registro por campo, com valor anterior e novo | A1, RF-05 |
| CA-05 | dois clientes | a pesquisa usa parte do nome ou do documento | só o cliente correspondente é devolvido | A2 |
| CA-06 | um Contador | consulta e tenta cadastrar | consulta, mas o cadastro é negado | RB-03 |

## 7. Questões em aberto

Nenhuma bloqueante. A validação de dígitos verificadores é a leitura adotada para "documento válido" (RF-01).

## 8. Verificação

| Critério | Teste (`tests/aplicacao/test_spec_003_clientes.py`) | Resultado |
|---|---|---|
| CA-01 | `test_RF_01_cadastra_cliente_e_audita` | Passou |
| CA-02 | `test_E1_documento_duplicado` | Passou |
| CA-03 | `test_E2_campos_obrigatorios` | Passou |
| CA-04 | `test_A1_alteracao_audita_cada_campo` | Passou |
| CA-05 | `test_A2_busca_por_nome_ou_documento` | Passou |
| CA-06 | `test_RB_03_contador_consulta_mas_nao_cadastra` | Passou |

Validação do documento: `tests/dominio/test_cliente.py`.
