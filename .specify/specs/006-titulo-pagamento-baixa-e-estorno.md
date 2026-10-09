# Spec 006 — Título: cadastro manual, pagamento, baixa e estorno

## 1. Identificação

| | |
|---|---|
| **ID** | 006 |
| **Nome** | Título: cadastro manual, pagamento, baixa e estorno |
| **Objetivo** | Manter o saldo e o estado de um título a receber corretos diante de pagamentos, estornos, vencimento e cancelamento. |
| **Valor entregue** | O Operador Financeiro registra o que foi pago e sabe, a qualquer momento, quanto falta receber de cada título e em que estado ele está. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Guerra, Renan Gandolpho e Bernardo Sanches, em 2026-10-03 |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-20, RF-21, RF-22, RF-23, RF-24, RF-25, RF-26, RF-27, RF-30, RF-31, RF-68 |
| RB | RB-01, RB-02, RB-21, RB-22, RB-23 |
| RNF | RNF-09, RNF-19 |
| UC | [UC-06](../../docs/casos-de-uso/UC-06-registrar-pagamento-e-baixar-titulo.md) |
| Entidades | `Titulo`, `Pagamento`; referência a `Cliente` e `Usuario` |
| Drivers e ADRs | DA-01, DA-03, DA-09; ADR-001 |
| Depende de | Spec 001 (auditoria). Para uso pela interface: Specs 002 e 003. |

Referências: [estados do título](../../docs/uml/estados.md#título), [sequência do UC-06](../../docs/uml/seq-UC-06.png).

## 3. Escopo

### Incluído

- Cadastro manual de título.
- Consulta de títulos com filtros.
- Sinalização de título próximo do vencimento.
- Passagem de Aberto para Vencido.
- Registro de pagamento integral e parcial.
- Baixa quando o saldo chega a zero.
- Estorno de pagamento pelo Dono.
- Cancelamento de título.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Geração de título a partir de orçamento | Spec 005 |
| Disparo periódico da verificação de vencimento | Spec 008 |
| Cancelamento dos envios pendentes da régua | Spec 008 |
| Estado Em Renegociação e suas transições | Spec 009 |
| Geração do lançamento financeiro no pagamento e no estorno | Spec 011 |
| Juros e multa por atraso | Fora do MVP (OPEN-11) |
| Interface web | Definida após OPEN-01 |

Esta spec oferece as operações de domínio que as Specs 005, 008, 009 e 011 usam. Ela não as implementa.

## 4. Comportamento

### Pré-condições

- O cliente do título existe.
- O usuário que executa a operação é conhecido, para a auditoria.

### Fluxo principal: pagamento integral

1. O usuário informa o título, o valor e a data do pagamento.
2. O sistema verifica que o título está Aberto ou Vencido.
3. O sistema verifica que o valor é maior que zero e menor ou igual ao saldo.
4. O sistema registra o pagamento.
5. O saldo chega a zero e o sistema muda o estado do título para Baixado.
6. O sistema registra a operação e a mudança de estado na auditoria.

### Fluxos alternativos

- **A1 — Pagamento parcial.** No passo 5, o saldo continua maior que zero. O estado não muda. O sistema devolve o saldo restante.
- **A2 — Cadastro manual.** O usuário informa cliente, valor, vencimento e condição de pagamento. O sistema cria o título em Aberto, com origem "manual" e saldo igual ao valor.
- **A3 — Vencimento.** Dada uma data de referência, todo título Aberto com vencimento anterior a ela e saldo maior que zero passa a Vencido.
- **A4 — Estorno.** O Dono informa o pagamento e o motivo. O sistema marca o pagamento como estornado e recalcula o saldo. O título vai para Aberto, se o vencimento for igual ou posterior à data de referência, ou para Vencido, se for anterior.
- **A5 — Cancelamento.** Um usuário autorizado informa o título e o motivo. Um título Aberto ou Vencido passa a Cancelado.
- **A6 — Consulta.** O usuário filtra títulos por cliente, estado, vencimento e período. Cada título é apresentado com valor, saldo, vencimento, estado e a sinalização de próximo do vencimento.

### Exceções

- **E1 — Valor inválido.** Valor menor ou igual a zero, ou maior que o saldo: o pagamento é recusado.
- **E2 — Estado que não aceita pagamento.** Título Baixado ou Cancelado: o pagamento é recusado.
- **E3 — Estorno por quem não é Dono.** A operação é recusada.
- **E4 — Motivo ausente.** Estorno ou cancelamento sem motivo: a operação é recusada.
- **E5 — Pagamento já estornado.** Novo estorno do mesmo pagamento é recusado.
- **E6 — Cancelamento de título Baixado.** A operação é recusada. É preciso estornar antes.
- **E7 — Dados inválidos no cadastro.** Valor menor ou igual a zero, cliente inexistente ou vencimento ausente: o cadastro é recusado.
- **E8 — Falha durante a operação.** Nenhuma alteração parcial permanece.

Toda recusa informa o motivo e não altera nenhum dado.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | O saldo é sempre o valor do título menos a soma dos pagamentos não estornados. | RB-22 |
| INV-2 | O saldo nunca é negativo nem maior que o valor do título. | RB-23 |
| INV-3 | Um título está Baixado se, e somente se, seu saldo é zero. | RB-22 |
| INV-4 | Um título está em exatamente um estado, e só muda por uma transição da tabela de estados. | RB-21 |
| INV-5 | O valor de um título não muda depois de criado. | RB-21 |
| INV-6 | Um pagamento não é apagado; ele só pode ser marcado como estornado. | RB-01 |
| INV-7 | Toda operação que altera título ou pagamento gera registro de auditoria, na mesma transação. | RB-01, RNF-09 |
| INV-8 | As regras RB-21, RB-22 e RB-23 são implementadas no domínio e valem para qualquer chamador. | RNF-19, ADR-001 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um cliente cadastrado | o usuário cadastra um título de R$ 1.000,00 com vencimento futuro | o título é criado em Aberto, com saldo de R$ 1.000,00 e origem "manual" | RF-20, RF-21 |
| CA-02 | um cliente cadastrado | o usuário cadastra um título com valor zero | o cadastro é recusado e nenhum título é criado | RF-20, E7 |
| CA-03 | um título Aberto de R$ 1.000,00 | o usuário registra um pagamento de R$ 1.000,00 | o saldo fica em R$ 0,00 e o estado passa a Baixado | RF-25, RF-26, RB-22 |
| CA-04 | um título Aberto de R$ 1.000,00 | o usuário registra um pagamento de R$ 400,00 | o saldo fica em R$ 600,00 e o estado continua Aberto | RF-27 |
| CA-05 | um título com saldo de R$ 600,00 | o usuário registra um pagamento de R$ 600,00 | o saldo fica em R$ 0,00 e o estado passa a Baixado | RF-26, INV-3 |
| CA-06 | um título com saldo de R$ 600,00 | o usuário registra um pagamento de R$ 600,01 | o pagamento é recusado e o saldo continua em R$ 600,00 | RF-68, RB-23 |
| CA-07 | um título Aberto | o usuário registra um pagamento de R$ 0,00 ou de valor negativo | o pagamento é recusado | RF-68, RB-23 |
| CA-08 | um título Baixado | o usuário registra um pagamento | o pagamento é recusado e o motivo informa o estado do título | RB-21, E2 |
| CA-09 | um título Cancelado | o usuário registra um pagamento | o pagamento é recusado | RB-21, E2 |
| CA-10 | um título Aberto com vencimento ontem e saldo maior que zero | a verificação de vencimento é executada com a data de hoje | o estado passa a Vencido | RF-24 |
| CA-11 | um título Aberto com vencimento hoje | a verificação de vencimento é executada com a data de hoje | o estado continua Aberto | RF-24 |
| CA-12 | um título Vencido de R$ 1.000,00 | o usuário registra um pagamento de R$ 1.000,00 | o estado passa a Baixado | RF-26, RB-21 |
| CA-13 | um título Baixado por um pagamento de R$ 1.000,00, com vencimento futuro | o Dono estorna o pagamento informando o motivo | o pagamento fica estornado, o saldo volta a R$ 1.000,00 e o estado passa a Aberto | RF-30, RB-02 |
| CA-14 | um título Baixado, com vencimento passado | o Dono estorna o pagamento informando o motivo | o estado passa a Vencido | RF-30, RB-21 |
| CA-15 | um título com um pagamento registrado | o Operador Financeiro tenta estornar o pagamento | a operação é recusada e o pagamento continua válido | RB-02, E3 |
| CA-16 | um título com um pagamento registrado | o Dono solicita o estorno sem informar o motivo | a operação é recusada | RF-31, E4 |
| CA-17 | um pagamento já estornado | o Dono solicita novo estorno do mesmo pagamento | a operação é recusada e o saldo não muda | E5, INV-1 |
| CA-18 | um título Aberto | um usuário autorizado cancela o título informando o motivo | o estado passa a Cancelado | RF-31, RB-21 |
| CA-19 | um título Baixado | um usuário tenta cancelar o título | a operação é recusada | RB-21, E6 |
| CA-20 | um título Aberto com vencimento em 3 dias e antecedência configurada de 5 dias | o usuário consulta o título | o título aparece sinalizado como próximo do vencimento, e seu estado é Aberto | RF-23 |
| CA-21 | títulos de dois clientes, em estados diferentes | o usuário filtra por um cliente e pelo estado Vencido | são apresentados apenas os títulos Vencidos daquele cliente | RF-22 |
| CA-22 | um título Aberto | um pagamento válido é registrado | existe um registro de auditoria com usuário, data, operação e título afetado | RB-01, INV-7 |
| CA-23 | um título Aberto | o registro de auditoria falha durante o registro de um pagamento | nenhum pagamento é gravado, e saldo e estado não mudam | RNF-09, INV-7 |
| CA-24 | qualquer sequência de pagamentos e estornos válidos sobre um título | a sequência termina | o saldo é igual ao valor menos a soma dos pagamentos não estornados | INV-1, INV-2 |

Os testes automatizados levam no nome o identificador da regra ou do critério, por exemplo `RB-23_recusa_pagamento_maior_que_o_saldo`.

## 7. Questões em aberto

| ID | Questão | Situação |
|---|---|---|
| OPEN-01 | Linguagem e framework | Decidida em 2026-10-03: escolha livre, com o domínio isolado do framework. Adotado Python 3.11, só com a biblioteca padrão. O framework web fica para a primeira spec com interface. |
| OPEN-02 | Banco de dados | Aberta. Não bloqueia: a persistência desta spec é em memória. |
| OPEN-11 | Juros e multa em título vencido | Decidida em 2026-10-03: fora do MVP. |
| OPEN-15 | Um título ou um título por parcela | Aberta. Não bloqueia: esta spec trata cada título isoladamente. |
| OPEN-16 | Qual perfil pode cancelar um título | Decidida em 2026-10-03: somente o Dono. |
| OPEN-17 | A data do pagamento pode ser anterior à data do registro? E pode ser futura? | Aberta. A implementação não restringe a data. |
| OPEN-18 | O Dono pode estornar um pagamento de título Cancelado? | Aberta, surgiu na implementação. Comportamento provisório: recusa. |
| OPEN-19 | O filtro "período" do RF-22 é sobre o vencimento ou sobre outra data? | Aberta, surgiu na implementação. Comportamento provisório: intervalo de vencimento. |
| OPEN-20 | Valores monetários podem ter mais de duas casas decimais? | Aberta, surgiu nos testes de exceção (#68). Comportamento atual: aceita. |

## 8. Verificação

Verificada em 2026-10-03, com `python3 -m unittest discover -s tests -t .`: 48 testes, todos passando. Testes em [`tests/aplicacao/test_spec_006_aceite.py`](../../tests/aplicacao/test_spec_006_aceite.py) (critérios) e [`tests/dominio/test_titulo.py`](../../tests/dominio/test_titulo.py) (regras). Plano em [`plans/006-plano.md`](../plans/006-plano.md).

### Critérios de aceitação

| Critério | Teste | Resultado |
|---|---|---|
| CA-01 | `test_CA_01` | Passou |
| CA-02 | `test_CA_02 (2 testes)` | Passou |
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
| CA-14 | `test_CA_14` | Passou |
| CA-15 | `test_CA_15` | Passou |
| CA-16 | `test_CA_16` | Passou |
| CA-17 | `test_CA_17` | Passou |
| CA-18 | `test_CA_18 (3 testes, inclui OPEN-16 e E4)` | Passou |
| CA-19 | `test_CA_19` | Passou |
| CA-20 | `test_CA_20` | Passou |
| CA-21 | `test_CA_21 (2 testes)` | Passou |
| CA-22 | `test_CA_22 (2 testes, inclui RB-01)` | Passou |
| CA-23 | `test_CA_23` | Passou |
| CA-24 | `test_CA_24 (50 sequências aleatórias com semente fixa)` | Passou |

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1, INV-2, INV-3 | CA-24, a cada passo de cada sequência; `test_RB_22_*` | Passou |
| INV-4 | `test_RB_21_*`; o estado é um único valor de `EstadoTitulo` | Passou |
| INV-5 | `test_RB_21_valor_do_titulo_nao_muda_com_pagamentos`; nenhuma operação altera o valor | Passou |
| INV-6 | Revisão de código: não há operação que remova pagamento | Passou |
| INV-7 | CA-22 e CA-23 | Passou |
| INV-8 | RB-21, RB-22 e RB-23 ficam só em `src/remindme/dominio/titulo.py`; o domínio não importa aplicação nem infraestrutura | Passou |

### Divergências e limitações

| Item | Situação |
|---|---|
| A Spec 001 (auditoria) ainda não existe | A auditoria é gravada por uma interface, com implementação em memória. A Spec 001 vai substituí-la sem mudar o domínio. |
| Persistência | Em memória, com transação por cópia e restauração. O banco depende de OPEN-02. |
| Estado Em Renegociação | Fica fora de `EstadoTitulo` até a Spec 009, como está no escopo. |
| Quem cadastra título e registra pagamento | Sem restrição de perfil nesta spec. A autorização geral, inclusive RB-03 (Contador só consulta), é da Spec 002. |
| Data do pagamento | Sem restrição, até a decisão de OPEN-17. |
| Estorno em título Cancelado | Recusado provisoriamente (OPEN-18). |
| Filtro por período | Intervalo de vencimento, provisoriamente (OPEN-19). |
| Nome dos testes | Python não aceita hífen em identificador: `RB-23_...` vira `test_RB_23_...`. |
| Validação de entrada (2026-10-09, #70) | Valor `NaN`, infinito, `float`, texto ou `None` e motivo que não é texto geravam erro interno, e um pagamento em `float` ficava anexado ao título antes do erro. Agora são recusados com motivo, no domínio (E1, E4, E7). Defeitos D-01 a D-05 em [`docs/qualidade/defeitos.md`](../../docs/qualidade/defeitos.md). |
| Precisão monetária | Valor com mais de duas casas decimais é aceito, até a decisão de OPEN-20. |

### Reverificação de 2026-10-09

Rodada de qualidade das issues #48 a #72: 132 testes, todos passando, em Python 3.11, 3.12 e 3.13. Os 24 critérios de aceitação continuam passando, e os 48 testes da verificação original passam contra o código corrigido. Matriz completa em [`docs/qualidade/matriz-criterios-de-aceite.md`](../../docs/qualidade/matriz-criterios-de-aceite.md).
