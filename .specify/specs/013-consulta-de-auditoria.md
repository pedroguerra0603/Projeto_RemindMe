# Spec 013 — Consulta de auditoria

## 1. Identificação

| | |
|---|---|
| **ID** | 013 |
| **Nome** | Consulta de auditoria |
| **Objetivo** | Permitir que os perfis autorizados descubram quem fez o quê, quando e por quê, sem poder alterar nenhum registro. |
| **Valor entregue** | A Dona e a Contadora consultam o histórico de um título ou de um período e veem o responsável, o valor anterior, o novo e o motivo de cada alteração. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Silva Guerra, em 2026-10-23, por autorização prévia dada ao agente antes da redação; a revisão do conteúdo fica no PR |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-64; apresenta o que RF-04, RF-05, RF-61 e RF-62 gravam |
| RB | RB-01, RB-30 |
| RNF | RNF-02, RNF-06, RNF-14 |
| UC | [UC-12](../../docs/casos-de-uso/UC-12-consultar-auditoria.md) |
| Entidades | `RegistroAuditoria`; referência a `Usuario` |
| Drivers e ADRs | DA-02; ADR-004 |
| Depende de | Specs 001 e 002 |

## 3. Escopo

### Incluído

- Consulta dos registros de auditoria, em ordem cronológica, com filtros por usuário, período e tipo de operação (RF-64).
- Histórico de um registro: um título com seus pagamentos, um cliente ou um usuário (UC-12, A1).
- Identificação do responsável pelo nome, e das operações automáticas pela rotina que as disparou.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Exportação da auditoria em CSV | Spec 015, se a equipe decidir incluí-la |
| Política de retenção | OPEN-31 (decidida: nenhum registro é excluído no MVP) |
| Telas | Spec 017 |

## 4. Comportamento

### Pré-condições

- O usuário tem sessão válida e a permissão "Consultar auditoria": Dono, Contador ou Administrador (Spec 002).

### Fluxo principal

1. O usuário informa, se quiser, o usuário responsável, o período e o tipo de operação.
2. O sistema apresenta os registros que atendem a todos os filtros, em ordem cronológica.
3. Cada registro mostra o responsável, a data e a hora no fuso de referência (OPEN-26), a operação e o registro afetado.
4. Para alterações, mostra o campo, o valor anterior, o novo valor e o motivo, quando houver.

### Fluxos alternativos

- **A1 — Histórico de um registro.** O usuário consulta só os registros de um título, que incluem os dos pagamentos dele, de um cliente ou de um usuário.
- **A2 — Operação automática.** O registro sem usuário aparece como operação do sistema, com a rotina que a disparou (Spec 001, A4).
- **A3 — Opções de filtro.** O sistema oferece como opções os usuários e os tipos de operação que aparecem na auditoria.

### Exceções

- **E1 — Sem resultados.** O sistema informa que não há registros para os filtros.
- **E2 — Perfil sem permissão.** O Operador Financeiro e o Cliente não consultam (RNF-02).
- **E3 — Período invertido.** Início depois do fim: a consulta é recusada, indicando o campo (RNF-14).

A consulta não altera nada, e não há operação de alteração nem de exclusão de registro de auditoria (RB-30, RNF-06).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | A consulta apresenta os registros na ordem em que foram gravados. | UC-12, passo 2; Spec 001, INV-4 |
| INV-2 | Nenhuma operação de consulta grava, altera ou exclui registro de auditoria. | RB-30, RNF-06 |
| INV-3 | Só os perfis com a permissão "Consultar auditoria" veem os registros. | RNF-02 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | operações feitas por dois usuários | a Dona consulta sem filtros | todos os registros aparecem em ordem cronológica, com o nome do responsável, a data e a hora, a operação e o registro afetado | RF-64, INV-1 |
| CA-02 | operações de dois usuários | a consulta filtra por um deles | aparecem só os registros desse usuário | RF-64 |
| CA-03 | operações em dois dias | a consulta filtra o período de um dia | aparecem só os registros desse dia, pela data do fuso de referência | RF-64, OPEN-26 |
| CA-04 | cadastros e pagamentos | a consulta filtra o tipo "registrar pagamento" | aparecem só os registros desse tipo | RF-64 |
| CA-05 | dois títulos com pagamentos | o histórico de um título é consultado | aparecem os registros do título e dos pagamentos dele, e nenhum do outro título | A1 |
| CA-06 | um pagamento estornado | a consulta é feita | o registro do estorno mostra o campo, o valor anterior, o novo e o motivo | UC-12, passo 4 |
| CA-07 | um título vencido pela rotina automática | a consulta é feita | o registro aparece como operação do sistema, com a rotina "verificação de vencimento" | A2 |
| CA-08 | nenhum registro no período | a consulta é feita | o resultado é vazio | E1 |
| CA-09 | o Operador Financeiro, o Contador e o Administrador | cada um consulta | o Operador é negado; o Contador e o Administrador são atendidos | E2, INV-3 |
| CA-10 | registros gravados | a consulta é feita várias vezes | os registros continuam os mesmos, e nenhum registro novo é gravado | INV-2 |
| CA-11 | um período com início depois do fim | a consulta é feita | ela é recusada, indicando o campo | E3, RNF-14 |
| CA-12 | registros de vários usuários e operações | as opções de filtro são pedidas | aparecem os usuários e os tipos de operação presentes na auditoria | A3 |

## 7. Questões em aberto

Nenhuma.

## 8. Verificação

Verificada em 2026-10-23, com `python3 -m unittest discover -s tests -t .`: 282 testes, todos passando (7 pulados por dependerem de specs futuras). Testes em [`tests/aplicacao/test_spec_013_aceite.py`](../../tests/aplicacao/test_spec_013_aceite.py). Plano em [`plans/013-plano.md`](../plans/013-plano.md) e tarefas em [`tasks/013-tarefas.md`](../tasks/013-tarefas.md).

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

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1 | CA-01 e CA-05 | Passou |
| INV-2 | CA-10; a porta de auditoria só oferece `registrar` e `listar` (`test_RB_30_a_porta_de_auditoria_so_oferece_incluir_e_ler`) | Passou |
| INV-3 | CA-09 | Passou |

### Divergências e limitações

| Item | Situação |
|---|---|
| Porta de auditoria | Ganhou a leitura (`listar`). Os testes de RB-30 passaram a aceitar `registrar` e `listar`, e continuam recusando qualquer outra operação. |
| Exclusão no armazenamento real | Coberta pela Spec 017, com o gatilho do SQLite que recusa `UPDATE` e `DELETE` (ADR-007). |
| Telas | Spec 017. |
