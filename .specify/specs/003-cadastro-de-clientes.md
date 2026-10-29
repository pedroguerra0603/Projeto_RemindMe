# Spec 003 — Cadastro de clientes

## 1. Identificação

| | |
|---|---|
| **ID** | 003 |
| **Nome** | Cadastro de clientes |
| **Objetivo** | Manter os clientes que devem títulos, com documento conferido e único e um contato para a cobrança. |
| **Valor entregue** | O Operador Financeiro cadastra o cliente uma vez e o encontra pelo nome ou pelo documento, com os títulos dele. A Dona sabe que não há dois cadastros do mesmo cliente e que toda alteração fica registrada. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Silva Guerra, em 2026-10-23, por autorização prévia dada ao agente antes da redação; a revisão do conteúdo fica no PR |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-01, RF-04, RF-05 |
| RB | RB-01; RB-03 (o Contador não mantém clientes) |
| RNF | RNF-02, RNF-14 |
| UC | [UC-03](../../docs/casos-de-uso/UC-03-manter-clientes.md) |
| Entidades | `Cliente`; referência a `Titulo` |
| Drivers e ADRs | DA-02, DA-04; ADR-001, ADR-004 |
| Depende de | Specs 001 e 002. Decisões OPEN-40 (documento válido), OPEN-41 (contato) e OPEN-42 (quem consulta clientes), tomadas em 2026-10-23 por delegação. |

## 3. Escopo

### Incluído

- Cadastro de cliente com nome, documento e contato (RF-01).
- Alteração dos dados, com o valor anterior e o novo valor de cada campo alterado (RF-05).
- Pesquisa por parte do nome ou pelo documento, e consulta dos títulos do cliente (UC-03, A2).
- Conferência de que o título é cadastrado para cliente existente (Spec 006, E7).

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Orçamentos do cliente | Spec 004 |
| Importação de clientes por CSV | Spec 015 |
| Acesso do próprio cliente aos títulos | Spec 009 (OPEN-08) |
| Exclusão de cliente | Não há requisito; o histórico de títulos e auditoria depende do cliente |
| Telas | Spec 017 |

## 4. Comportamento

### Pré-condições

- O usuário tem sessão válida (Spec 002).
- Cadastrar e alterar exigem a permissão "Manter clientes"; pesquisar e consultar, a permissão "Consultar clientes" (OPEN-42).

### Fluxo principal: cadastro

1. O usuário informa nome, documento e contato do cliente.
2. O sistema valida os três campos.
3. O sistema confere que nenhum outro cliente tem o mesmo documento.
4. O sistema cria o cliente, com o documento guardado sem pontuação.
5. O sistema registra na auditoria um registro por campo, com o valor informado como novo valor.

### Fluxos alternativos

- **A1 — Alteração.** O usuário altera nome, documento ou contato. O sistema valida como no cadastro e registra, para cada campo que mudou, o valor anterior e o novo. Se nenhum campo muda, nada é gravado.
- **A2 — Pesquisa.** O usuário pesquisa por parte do nome, sem diferença entre maiúsculas e minúsculas, ou pelo documento, com ou sem pontuação. O sistema apresenta os clientes em ordem alfabética.
- **A3 — Títulos do cliente.** O usuário consulta os títulos de um cliente pela consulta de títulos da Spec 006, filtrada por ele (RF-22).

### Exceções

- **E1 — Documento inválido.** CPF ou CNPJ com tamanho errado ou dígito verificador incorreto: a recusa indica o campo documento (OPEN-40).
- **E2 — Documento já cadastrado.** A recusa indica o campo documento e o motivo, e nada é criado nem alterado (UC-03, E1).
- **E3 — Dados obrigatórios ausentes.** A recusa indica todos os campos faltantes (UC-03, E2; RNF-14).
- **E4 — Contato inválido.** Contato que não é e-mail nem telefone com DDD: a recusa indica o campo contato (OPEN-41).
- **E5 — Perfil sem permissão.** O Contador não cadastra nem altera (RB-03); o Administrador e o Cliente não consultam (RNF-02).
- **E6 — Cliente inexistente.** A alteração e a consulta de um cliente que não existe são recusadas.

Toda recusa informa o motivo e não altera nenhum dado.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Dois clientes não têm o mesmo documento. | UC-03, E1 |
| INV-2 | O documento guardado é um CPF ou CNPJ válido, sem pontuação. | RF-01, OPEN-40 |
| INV-3 | Todo cliente tem nome, documento e contato. | UC-03, OPEN-41 |
| INV-4 | Cadastro e alteração de cliente são auditados na mesma transação, campo a campo. | RB-01, RF-04, RF-05, Spec 001 |
| INV-5 | Um título só é cadastrado para um cliente que existe. | Spec 006, E7 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | o Operador Financeiro autenticado | ele cadastra "Padaria Pão Quente Ltda", com um CNPJ válido digitado com pontuação e um e-mail | o cliente é criado com o CNPJ só com os caracteres, e a auditoria tem nome, documento e contato como novos valores | RF-01, INV-2, INV-4 |
| CA-02 | o Operador Financeiro autenticado | ele cadastra um cliente com CPF de dígito verificador errado | o cadastro é recusado, indicando o campo documento | E1, RNF-14 |
| CA-03 | um cliente com um CPF | outro cliente é cadastrado com o mesmo CPF, escrito com outra pontuação | o cadastro é recusado, indicando o campo documento, e nada é criado | E2, INV-1 |
| CA-04 | o Operador Financeiro autenticado | ele cadastra um cliente sem nome e sem contato | o cadastro é recusado, indicando os dois campos | E3, RNF-14 |
| CA-05 | o Operador Financeiro autenticado | ele informa o contato "abc"; depois, "(11) 98765-4321" | o primeiro é recusado no campo contato; o segundo é aceito | E4, OPEN-41 |
| CA-06 | um cliente cadastrado | o contato dele é alterado | a auditoria tem um único registro, do campo contato, com o valor anterior e o novo | A1, RF-05 |
| CA-07 | dois clientes cadastrados | um deles é alterado para o documento do outro | a alteração é recusada, e os dois continuam como estavam | E2, INV-1 |
| CA-08 | o Contador autenticado | ele tenta cadastrar um cliente e depois pesquisa os clientes | o cadastro é negado (RB-03), e a pesquisa é atendida | E5, OPEN-42 |
| CA-09 | clientes cadastrados | o usuário pesquisa "pão" e, depois, o documento sem pontuação | as duas pesquisas encontram "Padaria Pão Quente Ltda" | A2 |
| CA-10 | nenhum cliente com o identificador informado | um título é cadastrado para ele | o cadastro do título é recusado; para um cliente cadastrado, é aceito | INV-5 |
| CA-11 | títulos de dois clientes | os títulos de um deles são consultados | aparecem apenas os títulos desse cliente | A3, RF-22 |
| CA-12 | o Administrador autenticado | ele pesquisa os clientes | a pesquisa é negada | E5, RNF-02 |
| CA-13 | o Operador Financeiro autenticado | ele cadastra um cliente com um CNPJ alfanumérico válido | o cliente é criado | OPEN-40 |

Os testes automatizados levam no nome o identificador do critério ou da regra, por exemplo `test_CA_03_documento_repetido_e_recusado`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-40 | O que é um documento válido de cliente? | Decidida em 2026-10-23, por delegação: CPF ou CNPJ, inclusive o alfanumérico, com dígitos verificadores. |
| OPEN-41 | O que é o contato do cliente? | Decidida em 2026-10-23, por delegação: obrigatório; e-mail ou telefone com DDD. |
| OPEN-42 | Quem consulta clientes? | Decidida em 2026-10-23, por delegação: Dono, Operador Financeiro e Contador. |

## 8. Verificação

Verificada em 2026-10-23, com `python3 -m unittest discover -s tests -t .`: 270 testes, todos passando (7 pulados por dependerem de specs futuras). Testes em [`tests/aplicacao/test_spec_003_aceite.py`](../../tests/aplicacao/test_spec_003_aceite.py). Plano em [`plans/003-plano.md`](../plans/003-plano.md) e tarefas em [`tasks/003-tarefas.md`](../tasks/003-tarefas.md).

### Critérios de aceitação

| Critério | Teste | Resultado |
|---|---|---|
| CA-01 | `test_CA_01` | Passou |
| CA-02 | `test_CA_02` | Passou |
| CA-03 | `test_CA_03` | Passou |
| CA-04 | `test_CA_04` | Passou |
| CA-05 | `test_CA_05` | Passou |
| CA-06 | `test_CA_06` | Passou |
| CA-07 | `test_CA_07` | Passou |
| CA-08 | `test_CA_08` | Passou |
| CA-09 | `test_CA_09` | Passou |
| CA-10 | `test_CA_10` | Passou |
| CA-11 | `test_CA_11` | Passou |
| CA-12 | `test_CA_12` | Passou |
| CA-13 | `test_CA_13` | Passou |

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1 | CA-03 e CA-07 | Passou |
| INV-2 | CA-01, CA-02, CA-13 e `test_OPEN_40_*` | Passou |
| INV-3 | CA-04 e CA-05: o cadastro sem um dos campos é recusado | Passou |
| INV-4 | CA-01 e CA-06 | Passou |
| INV-5 | CA-10 | Passou |

### Divergências e limitações

| Item | Situação |
|---|---|
| CNPJ alfanumérico | Aceito desde a implementação, porque a Receita Federal o emite desde julho de 2026 (OPEN-40). |
| Persistência | Em memória nesta spec; o SQLite entra na Spec 017. A unicidade do documento também vira restrição do banco. |
| Telas | Spec 017. |
