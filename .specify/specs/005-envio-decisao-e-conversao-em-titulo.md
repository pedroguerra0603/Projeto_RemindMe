# Spec 005 — Envio, decisão do cliente e conversão em título

## 1. Identificação

| | |
|---|---|
| **ID** | 005 |
| **Nome** | Envio, decisão do cliente e conversão em título |
| **Objetivo** | Levar o orçamento pronto até o cliente, registrar a decisão dele e, na aprovação, gerar o título a receber na mesma operação, com o vencimento calculado pelo prazo combinado. |
| **Valor entregue** | O Operador Financeiro envia o orçamento com um clique e registra a resposta do cliente; o título nasce sozinho, com o valor e o vencimento certos. A Dona deixa de ter orçamento aprovado que nunca virou cobrança, a primeira dor da [visão](../../docs/visao.md#2-problema). A caixa de saída mostra o que o sistema mandou a cada cliente. |
| **Situação** | Proposta |
| **Aprovada por** | *(aguardando)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-08, RF-09, RF-11, RF-12, RF-19; RF-24 na aprovação registrada com atraso; RF-71 retirado (OPEN-62) |
| RB | RB-05, RB-18, RB-24, RB-27 (o texto ao cliente vem só do modelo); preserva RB-01, RB-03 e RB-15 |
| RNF | RNF-02, RNF-03, RNF-09, RNF-14, RNF-23 |
| UC | [UC-04](../../docs/casos-de-uso/UC-04-conduzir-orcamento-ate-o-titulo.md) (passos 5 a 9, A2, E1 a E4) |
| Entidades | `Orcamento`, `Titulo`; a mensagem do canal simulado, que não é classe do domínio |
| Drivers e ADRs | DA-01, DA-02, DA-03, DA-04, DA-07; ADR-001, ADR-002, ADR-004, ADR-007 |
| Depende de | Specs 001, 002, 003, 004 e 006. Questões OPEN-15 (um título por orçamento), OPEN-54 (dados da empresa), OPEN-57 (o cliente não acessa o sistema), e OPEN-61 e OPEN-62, decididas nesta spec. |

## 3. Escopo

### Incluído

- Prazo para pagamento do orçamento, em dias inteiros de 0 a 365, informado em Rascunho e exigido para o envio (OPEN-61). A condição de pagamento em texto continua como observação.
- Envio do orçamento ao cliente pelo canal de notificação, com o texto montado por um modelo fixo, e passagem a Enviado com a data do envio (RF-08, RB-27).
- Canal de notificação atrás de uma interface, com o canal simulado como única implementação (ADR-002, RB-18, OPEN-62). O canal simulado guarda cada mensagem, com o resultado, em vez de entregá-la.
- Caixa de saída: tela "Mensagens enviadas", com tudo o que o canal registrou, protegida pela operação nova "Consultar mensagens enviadas" na matriz de permissões (Dono e Operador Financeiro; o Administrador pela OPEN-53).
- Registro da decisão do cliente por um usuário da empresa, com a data em que o cliente decidiu (RF-09, OPEN-57).
- Na aprovação, geração do título a receber e passagem do orçamento a Convertido, na mesma operação (RF-11, RF-19, RB-05).
- Na rejeição, passagem a Rejeitado, com motivo opcional.
- Recusa de conversão de orçamento que não está Aprovado (RF-12).
- Interface web: prazo, envio e decisão na página do orçamento; ligação entre o orçamento e o título; caixa de saída.
- Dados de demonstração com orçamentos Enviado, Convertido e Rejeitado e as mensagens correspondentes.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Resposta do cliente interpretada pelo sistema | Spec 009 |

## 4. Comportamento

### Pré-condições

- O usuário está autenticado com um perfil que tem "Conduzir orçamento" (Dono e Operador Financeiro, na matriz inicial; o Administrador pela OPEN-53).
- O orçamento foi montado pela Spec 004, e o cliente tem contato cadastrado (OPEN-41).

### Fluxo principal

1. Em Rascunho, o Operador Financeiro informa o prazo para pagamento em dias.
2. O Operador pede o envio. O sistema confere que o orçamento pode sair de Rascunho: ao menos um item (RB-24), nenhum desconto pendente (RB-15) e prazo informado (OPEN-61).
3. O sistema monta a mensagem pelo modelo do orçamento e a entrega ao canal de notificação, endereçada ao contato do cliente.
4. O canal confirma a entrega. O orçamento passa a Enviado, com a data do envio.
5. O cliente responde fora do sistema. O Operador registra a aprovação, com a data em que o cliente decidiu; hoje é o padrão.
6. Na mesma operação, o orçamento passa a Aprovado, o sistema gera o título e o orçamento passa a Convertido, ligado ao título.

### Mensagem ao cliente

- O texto vem de um único modelo e traz: o nome fantasia da empresa (OPEN-54), ou a razão social quando não houver nome fantasia; o número do orçamento; cada item com descrição, quantidade e total; o valor bruto, o desconto e o valor líquido; o prazo para pagamento; e a condição de pagamento, quando informada.
- Nenhum outro texto chega ao cliente (RB-27).
- A mensagem guarda o cliente, o contato usado, o assunto, o texto, a data e hora, o resultado (enviada ou falhou) e o orçamento de origem.

### Título gerado

- Cliente, valor e condição de pagamento iguais aos do orçamento; o valor é o valor líquido (RF-19).
- Vencimento = data da decisão + prazo para pagamento (OPEN-61).
- Origem "orçamento", com o vínculo ao orçamento que o gerou.
- O título nasce Aberto (RB-21). Se o vencimento já tiver passado, a mesma operação o marca Vencido (RF-24).

### Fluxos alternativos

- **A1 — Cliente rejeita.** No passo 5, o Operador registra a rejeição, com a data e um motivo opcional. O orçamento passa a Rejeitado, e nenhum título é gerado (UC-04, A2).
- **A2 — Aprovação registrada com atraso.** No passo 5, a data da decisão é anterior a hoje. O vencimento conta a partir dela; se já passou, o título nasce e fica Vencido na mesma operação.
- **A3 — Cancelamento depois do envio.** Um orçamento Enviado pode ser cancelado com motivo, como na Spec 004 (RF-13). Cancelado, ele não aceita decisão.
- **A4 — Prazo zero.** Com prazo 0, o vencimento é a própria data da decisão: pagamento à vista.

### Exceções

- **E1 — Orçamento que não pode ser enviado.** Sem prazo, sem item, com desconto pendente ou fora de Rascunho: o envio é recusado com o motivo, sem mensagem (UC-04, E1).
- **E2 — Falha no canal.** O canal devolve falha. O orçamento continua em Rascunho, a mensagem fica na caixa de saída com o resultado "falhou", e o usuário vê a falha (UC-04, E2; ADR-002).
- **E3 — Decisão fora de Enviado.** Registrar decisão de orçamento em Rascunho, Pendente de Alçada, Rejeitado, Convertido ou Cancelado é recusado, com o estado atual (RF-12).
- **E4 — Data da decisão inválida.** Data ausente, futura ou anterior à data do envio: recusada no campo data.
- **E5 — Falha ao gerar o título.** Se a gravação do título, do orçamento ou da auditoria falhar, nada fica gravado e o orçamento continua Enviado (UC-04, E4; RNF-09).
- **E6 — Prazo inválido.** Prazo ausente no envio, negativo, maior que 365 ou não inteiro: recusado no campo prazo (RNF-14).
- **E7 — Perfil sem permissão.** O Contador não envia, não registra decisão e não consulta a caixa de saída (RB-03), nem chamando o serviço direto (RNF-03).

Toda recusa informa o motivo e não altera nenhum dado. A exceção é a E2, que guarda a mensagem que falhou, como manda o ADR-002.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Um orçamento Convertido tem exatamente um título, e o título aponta para ele; nenhum orçamento gera um segundo título. | RB-05, OPEN-15 |
| INV-2 | Só orçamento Aprovado vira título, e Aprovado nunca fica gravado: a conversão ocorre na mesma operação da aprovação. | RB-05, RF-12, estados |
| INV-3 | Valor do título = valor líquido do orçamento; vencimento do título = data da decisão + prazo para pagamento. | RF-19, OPEN-61 |
| INV-4 | O texto enviado ao cliente vem só do modelo do orçamento, preenchido com dados da empresa, do cliente e do orçamento. | RB-27 |
| INV-5 | O domínio não conhece o canal; quem chama o canal é a camada de aplicação. | ADR-001, ADR-002 |
| INV-6 | Toda mudança de estado do orçamento, o prazo e o título gerado são auditados. | RB-01 |
| INV-7 | Prazo, itens, desconto e condição só mudam em Rascunho. | RF-07, Spec 004 INV-2 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um orçamento em Rascunho com um item | o Operador informa prazo de 30 dias | o prazo fica gravado, e a auditoria guarda o anterior e o novo | OPEN-61, RB-01 |
| CA-02 | um orçamento em Rascunho | o prazo informado é -1, 366 ou 2,5 | as três tentativas são recusadas no campo prazo, e nada muda | E6, RNF-14 |
| CA-03 | um orçamento com item, prazo e sem desconto pendente | o Operador o envia | o orçamento fica Enviado, com a data de hoje; a caixa de saída tem uma mensagem enviada ao contato do cliente; o envio é auditado | RF-08 |
| CA-04 | orçamentos sem prazo, sem item e Pendente de Alçada | o Operador pede o envio de cada um | os três são recusados com o motivo, nenhum muda de estado e a caixa de saída fica vazia | E1, RB-24, RB-15 |
| CA-05 | um canal que falha | o Operador envia um orçamento pronto | o orçamento continua em Rascunho, a caixa de saída tem a mensagem com o resultado "falhou" e o motivo mostra a falha | E2, ADR-002 |
| CA-06 | uma mensagem de orçamento enviada | o texto é lido na caixa de saída | ele tem o nome da empresa, o número do orçamento, cada item, o valor líquido e o prazo, e é igual ao produzido pelo modelo para os mesmos dados | RB-27, INV-4 |
| CA-07 | um orçamento Enviado de R$ 900,00 líquidos, prazo de 30 dias | o Operador registra a aprovação com a data de hoje | há um título Aberto do mesmo cliente, de R$ 900,00, com a condição do orçamento, vencimento em hoje + 30 dias e origem orçamento; o orçamento está Convertido e ligado ao título; a aprovação, a conversão e o título são auditados | RF-09, RF-11, RF-19, RB-05, INV-1, INV-3 |
| CA-08 | um orçamento Enviado há 10 dias, prazo de 5 dias | o Operador registra a aprovação com a data do envio | o título é gerado e já está Vencido | A2, RF-24 |
| CA-09 | um orçamento Enviado | o Operador registra a rejeição com motivo | o orçamento fica Rejeitado, com a data e o motivo, e nenhum título é gerado | A1, RF-09 |
| CA-10 | orçamentos em Rascunho, Rejeitado, Convertido e Cancelado | é registrada uma decisão para cada um | as quatro tentativas são recusadas com o estado atual, e nada muda | E3, RF-12 |
| CA-11 | um orçamento Enviado | a decisão é registrada com data de amanhã e com data anterior ao envio | as duas tentativas são recusadas no campo data | E4 |
| CA-12 | uma falha injetada ao gravar a auditoria da conversão | o Operador registra a aprovação | o orçamento continua Enviado e nenhum título existe | E5, RNF-09 |
| CA-13 | um Contador autenticado | ele tenta enviar, registrar decisão e consultar a caixa de saída | as três operações são negadas, e nada muda | E7, RB-03, RNF-03 |
| CA-14 | um orçamento Convertido | o serviço tenta gerar outro título para ele | a tentativa é recusada, e o orçamento continua com um único título | INV-1, OPEN-15 |

Os testes levam no nome o critério ou a regra, como `test_CA_07_RF_11_...` e `test_RB_05_...`.

## 7. Questões em aberto

| ID | Questão | Situação |
|---|---|---|
| OPEN-61 | De onde vem o vencimento do título gerado de um orçamento? | Decidida em 2026-11-07 por Renan Gandolpho: o orçamento tem prazo para pagamento em dias (0 a 365), exigido no envio; vencimento = data da decisão do cliente + prazo. |
| OPEN-62 | O projeto terá um canal de notificação real? | Decidida em 2026-11-07 por Renan Gandolpho: não. A execução é local (OPEN-12), e o canal simulado é a única implementação; RF-71 retirado. A Spec 009 continua. |

## 8. Verificação

*(preencher após a implementação)*
