# Spec 001 — Fundação: estrutura em camadas e auditoria de operações

## 1. Identificação

| | |
|---|---|
| **ID** | 001 |
| **Nome** | Fundação: estrutura em camadas e auditoria de operações |
| **Objetivo** | Garantir que toda operação que cria, altera ou muda o estado de um registro deixe uma prova imutável de quem fez, o quê, quando e sobre qual registro, gravada junto com a própria operação. |
| **Valor entregue** | O Dono consegue provar quem fez cada operação, e nenhuma operação acontece sem registro. A base vale para todas as specs seguintes. |
| **Situação** | Proposta |
| **Aprovada por** | *(nomes e data)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-04, RF-05, RF-61, RF-62 |
| RB | RB-01, RB-30 |
| RNF | RNF-06, RNF-09, RNF-19, RNF-21, RNF-23 |
| UC | [UC-12](../../docs/casos-de-uso/UC-12-consultar-auditoria.md) (dados que a consulta vai apresentar) |
| Entidades | `RegistroAuditoria`; referência a `Usuario` |
| Drivers e ADRs | DA-01, DA-02, DA-03, DA-07, DA-09; ADR-001, ADR-004 |
| Depende de | OPEN-01 (decidida). OPEN-02 não bloqueia: a persistência desta spec é em memória, com testes de contrato a repetir quando houver banco. |

Divergências que esta spec trata: DV-05, sobre o usuário de uma operação automática, em [`docs/qualidade/divergencias.md`](../../docs/qualidade/divergencias.md).

## 3. Escopo

### Incluído

- Registro de auditoria de toda operação aceita que cria, altera ou muda o estado de um registro.
- Valor anterior e novo valor de cada campo alterado.
- Gravação da auditoria na mesma transação da operação.
- Recusa de alteração e de exclusão de registros de auditoria.
- Registro de operação automática, sem usuário.
- Registro de erro não tratado, com identificador de correlação.
- Regra de dependência entre camadas e suíte sem credencial externa, como critérios verificáveis.
- Aplicação da auditoria às operações já implementadas da Spec 006.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Consulta e filtros da auditoria | Spec 013 (RF-64) |
| Autenticação e perfil de quem consulta | Spec 002 |
| Persistência em banco de dados | OPEN-02 |
| Política de retenção dos registros | OPEN-25 |
| Auditoria de orçamento, obrigação e lançamento | Specs 004, 005, 010 e 011, que usam esta fundação |
| Interface web | Primeira spec com interface (OPEN-01) |

## 4. Comportamento

### Pré-condições

- A operação é executada por um serviço da camada de aplicação.
- O usuário que executa a operação é conhecido, salvo em operação automática.

### Fluxo principal: operação auditada

1. Um usuário solicita uma operação que cria, altera ou muda o estado de um registro.
2. O sistema abre uma transação.
3. O domínio executa a operação.
4. O sistema grava um registro de auditoria com usuário, data e hora, operação e registro afetado.
5. Para cada campo alterado, o registro guarda o nome do campo, o valor anterior e o novo valor.
6. O sistema confirma a transação. Operação e auditoria passam a existir juntas.

### Fluxos alternativos

- **A1 — Criação.** No passo 5, um registro criado não tem valor anterior. O registro de auditoria informa o estado inicial como novo valor.
- **A2 — Mudança de estado.** O campo alterado é o estado, com o estado anterior e o novo.
- **A3 — Operação com motivo.** Em estorno, cancelamento ou alteração que exige motivo (RF-31), o registro guarda o motivo.
- **A4 — Operação automática.** Uma operação disparada pelo sistema, sem usuário, como a verificação de vencimento, gera registro sem usuário e identificado como automático (OPEN-24).
- **A5 — Vários registros afetados.** Uma operação que altera mais de um registro gera um registro de auditoria por registro afetado. Por exemplo, o estorno altera o pagamento e o estado do título.

### Exceções

- **E1 — Operação recusada.** Uma operação recusada por regra de negócio não grava nenhum registro de auditoria.
- **E2 — Falha ao gravar a auditoria.** A operação é desfeita, e nenhuma alteração permanece (RNF-09).
- **E3 — Falha ao gravar a operação.** Os registros de auditoria daquela transação são desfeitos.
- **E4 — Tentativa de alterar ou excluir um registro de auditoria.** A operação não existe para nenhum perfil e é recusada. O registro continua igual (RB-30, RNF-06).
- **E5 — Erro não tratado.** O sistema registra data e hora, operação, usuário e um identificador de correlação; desfaz a operação; e não esconde o erro de quem chamou (RNF-21).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Um registro de auditoria gravado nunca muda nem é excluído. | RB-30, RNF-06 |
| INV-2 | Toda operação aceita que cria, altera ou muda estado tem ao menos um registro de auditoria, gravado na mesma transação. Operação recusada ou desfeita não deixa registro. | RB-01, RNF-09, ADR-004 |
| INV-3 | Todo registro de auditoria tem data e hora, operação e registro afetado, e tem usuário, salvo quando a operação é automática. | RF-62; modelo de domínio, relação 18 |
| INV-4 | Os registros são mantidos na ordem em que foram gravados. | UC-12, passo 2 |
| INV-5 | A gravação da auditoria fica em um único ponto da camada de aplicação. | ADR-004, decisão 3; RNF-19 |
| INV-6 | O domínio não importa aplicação, infraestrutura, framework, banco, canal de notificação nem serviço de IA. | ADR-001; RNF-19 |
| INV-7 | A suíte de testes roda sem credencial de serviço externo. | RNF-23 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um cliente cadastrado e o Operador Financeiro | ele cadastra um título | existe um registro com o usuário, a data e hora do relógio, a operação "cadastrar título" e o título como registro afetado, com o estado Aberto como novo valor | RF-04, RF-62, A1 |
| CA-02 | um título Aberto de R$ 100,00 | um pagamento de R$ 100,00 é registrado | existe um registro do pagamento e um registro da mudança de estado, com o campo estado, valor anterior Aberto e novo valor Baixado | RF-05, RF-61, A2 |
| CA-03 | um título Baixado por um pagamento | o Dono estorna o pagamento com o motivo "cheque devolvido" | existe um registro cujo registro afetado é o pagamento, com o campo estornado de "não" para "sim" e o motivo; e um registro da mudança de estado do título | RB-01, RF-05, A3, A5 |
| CA-04 | um título Baixado | um pagamento é solicitado e recusado | nenhum registro de auditoria é gravado | INV-2, E1 |
| CA-05 | um título Aberto | a gravação da auditoria falha durante um pagamento | nenhum pagamento é gravado, e saldo e estado não mudam | RNF-09, E2 |
| CA-06 | um título Aberto | a gravação do título falha depois de a auditoria ser gravada | nenhum registro de auditoria daquela operação permanece | RNF-09, E3 |
| CA-07 | um registro de auditoria gravado | qualquer chamador tenta alterar um de seus campos, inclusive pelo objeto devolvido na leitura | a alteração é recusada e o registro armazenado continua igual | RB-30, RNF-06, E4 |
| CA-08 | um registro de auditoria gravado | qualquer chamador tenta excluí-lo | não há operação de exclusão, e o registro continua armazenado | RB-30, RNF-06, E4 |
| CA-09 | um título Aberto com vencimento ontem | a verificação de vencimento é executada sem usuário | o título passa a Vencido, e o registro da mudança de estado não tem usuário e está identificado como automático | INV-3, A4, OPEN-24 |
| CA-10 | uma operação em andamento | ocorre um erro que não é recusa de regra de negócio | existe um registro de erro com data e hora, operação, usuário e identificador de correlação; nenhuma alteração da operação permanece; e o erro chega a quem chamou | RNF-21, E5 |
| CA-11 | duas operações executadas em sequência | os registros são lidos | aparecem na ordem em que foram gravados | INV-4 |
| CA-12 | o código de `src/remindme/` | as importações de cada camada são verificadas | o domínio não importa aplicação nem infraestrutura, e a aplicação não importa infraestrutura | INV-6, RNF-19, ADR-001 |
| CA-13 | um ambiente sem nenhuma variável de credencial | a suíte inteira é executada | todos os testes passam | INV-7, RNF-23 |

Os testes automatizados levam no nome o identificador do critério ou da regra, por exemplo `test_CA_07_registro_gravado_nao_e_alterado` e `test_RB_30_...`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-02 | Banco de dados | Não. A persistência é em memória; os testes de contrato serão repetidos sobre o banco. |
| OPEN-24 | Como o registro de auditoria identifica uma operação automática, sem usuário? | Sim, para CA-09. Os demais critérios não dependem dela. |
| OPEN-25 | Qual a política de retenção dos registros de auditoria? | Não. Nenhum registro é excluído nesta spec. |

## 8. Verificação

A preencher depois da implementação.
