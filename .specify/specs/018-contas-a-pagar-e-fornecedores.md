# Spec 018 — Contas a pagar, fornecedores e retirada do perfil Cliente

## 1. Identificação

| | |
|---|---|
| **ID** | 018 |
| **Nome** | Contas a pagar, fornecedores e retirada do perfil Cliente |
| **Objetivo** | Registrar o que a empresa deve pagar aos fornecedores, com vencimento, pagamentos e saldo, ao lado do que ela tem a receber; e tirar do controle de acesso o perfil Cliente, que não tem função no sistema. |
| **Valor entregue** | A dona de uma borracharia vê, no mesmo painel, quanto vai receber dos clientes e quanto vai pagar pelas mercadorias que comprou, e o saldo previsto dos próximos dias. O Operador Financeiro lança cada compra a prazo e cada pagamento ao fornecedor; nada vence em silêncio. A tela de Permissões só mostra os perfis que de fato entram no sistema. |
| **Situação** | **Aprovada**; implementada e verificada (seção 8). |
| **Aprovada por** | Renan Gandolpho, em 2026-10-31, na conversa com o agente: escolheu conta a pagar separada da Obrigação, cadastro próprio de fornecedores, sem parcelas nem recorrência nesta spec, e a retirada do perfil Cliente; autorizou seguir até a implementação. A revisão do conteúdo fica no PR. |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-87 a RF-94 (novos); RF-69 retirado; RF-09 reescrito |
| RB | RB-31, RB-32, RB-33 (novas); RB-01; RB-03 (o Contador só consulta); RB-26 retirada |
| RNF | RNF-02, RNF-09, RNF-14, RNF-15, RNF-19 |
| UC | [UC-15](../../docs/casos-de-uso/UC-15-gerenciar-contas-a-pagar.md) (novo) |
| Entidades | `Fornecedor`, `ContaPagar`, `Pagamento` (reaproveitado); `Perfil` sem o valor Cliente |
| Drivers e ADRs | DA-01, DA-02, DA-04; ADR-001, ADR-004, ADR-007 |
| Depende de | Specs 001, 002, 003, 006 e 017. Decisões OPEN-56 e OPEN-57, tomadas em 2026-10-31 por Renan Gandolpho. |

## 3. Escopo

### Incluído

- Cadastro, alteração e pesquisa de fornecedores, com documento conferido e único (RF-87).
- Cadastro de conta a pagar para fornecedor existente (RF-88), consulta com filtros (RF-89) e tela da conta com os pagamentos e o histórico.
- Pagamento parcial ou integral, com baixa automática (RF-91); vencimento automático pelo agendador que já existe (RF-90); estorno e cancelamento pelo Dono, com motivo (RF-92, RF-93).
- Painel: contas a pagar vencidas e dos próximos 15 dias, ao lado dos títulos a receber, e o saldo previsto do período (RF-94).
- Retirada do perfil Cliente do controle de acesso (OPEN-57): o Cliente continua como cadastro de quem deve títulos, mas não é perfil, não aparece na matriz de Permissões e não tem regra fixada.
- Dados de demonstração com fornecedores e contas a pagar em todos os estados.

### Fora do escopo

| Item | Motivo |
|---|---|
| Parcelas e contas recorrentes (aluguel, energia) | Decidido em 2026-10-31: cada conta é cadastrada; fica para uma próxima spec. |
| Obrigações fiscais e contratuais com evidência | Continuam na Spec 010 (UC-09). A conta a pagar não exige evidência. |
| Lançamento automático da conta paga na apuração do resultado | Depende das Specs 011 e 012. |
| Exclusão de fornecedor | O histórico das contas e a auditoria dependem dele, como no cliente. |
| Alteração do valor da conta depois de criada | Mesma regra do título (OPEN-22): corrige-se cancelando e cadastrando de novo. |
| Acesso do cliente aos próprios títulos | Retirado (OPEN-57). O cliente continua recebendo mensagens pelo canal de notificação nas Specs 005, 008 e 009. |

## 4. Comportamento

### Pré-condições

- O usuário tem sessão válida (Spec 002).
- Fornecedores: "Manter fornecedores" para cadastrar e alterar; "Consultar fornecedores" para pesquisar.
- Contas: "Cadastrar conta a pagar", "Pagar conta", "Estornar pagamento de conta", "Cancelar conta a pagar" e "Consultar contas a pagar".

### Fluxo principal: compra a prazo paga ao fornecedor

1. O Operador Financeiro cadastra o fornecedor com nome, CPF ou CNPJ válido e contato.
2. O Operador cadastra a conta a pagar com fornecedor, descrição, valor, vencimento e, se quiser, a forma de pagamento.
3. O sistema cria a conta em Aberta, com saldo igual ao valor, e registra na auditoria.
4. Na data do pagamento, o Operador registra o pagamento com valor e data.
5. O saldo chega a zero e a conta passa a Paga; a mudança fica na auditoria.

### Fluxos alternativos

- **A1 — Pagamento parcial.** No passo 5, o saldo continua maior que zero e o estado não muda.
- **A2 — Vencimento.** O agendador, na inicialização e a cada hora (OPEN-48), passa a Vencida toda conta Aberta com vencimento anterior a hoje, com registro de operação automática na auditoria.
- **A3 — Estorno.** O Dono informa o pagamento e o motivo. O pagamento fica estornado e o saldo é restaurado. Conta Paga volta a Aberta, se o vencimento é hoje ou depois, ou a Vencida, se já passou.
- **A4 — Cancelamento.** O Dono informa o motivo. Conta Aberta ou Vencida passa a Cancelada.
- **A5 — Consulta.** O usuário filtra as contas por fornecedor, estado e intervalo de vencimento; cada conta aparece com fornecedor, descrição, valor, saldo, vencimento e estado, ordenadas por vencimento.
- **A6 — Alteração do fornecedor.** Como na Spec 003: um registro de auditoria por campo alterado.
- **A7 — Painel.** Quem consulta contas a pagar vê, na régua do caixa, o total a pagar vencido e o dos próximos 15 dias; quem também consulta títulos vê o saldo previsto: a receber menos a pagar, vencidos e dos próximos 15 dias.

### Exceções

- **E1 — Dados inválidos do fornecedor.** Nome, documento ou contato inválido, ou documento de outro fornecedor: recusado, com o motivo no campo (RNF-14).
- **E2 — Dados inválidos da conta.** Fornecedor inexistente, descrição vazia, vencimento ausente, valor menor ou igual a zero, com mais de duas casas ou mais de 15 dígitos inteiros: recusado.
- **E3 — Pagamento inválido.** Valor menor ou igual a zero ou maior que o saldo (RB-32), data futura, ou conta Paga ou Cancelada (RB-31): recusado.
- **E4 — Estorno ou cancelamento sem motivo, ou por quem não é Dono (RB-33):** recusado.
- **E5 — Estorno repetido, estorno em conta Cancelada, cancelamento de conta Paga:** recusado.
- **E6 — Falha durante a operação.** Nenhuma alteração parcial permanece (RNF-09).

Toda recusa informa o motivo e não altera nenhum dado.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | O saldo da conta é o valor menos a soma dos pagamentos não estornados, e fica entre zero e o valor. | RB-32 |
| INV-2 | A conta está Paga se, e somente se, o saldo é zero. | RB-31 |
| INV-3 | A conta está em exatamente um estado (Aberta, Vencida, Paga ou Cancelada). O valor não muda depois de criada. | RB-31 |
| INV-4 | Pagamento não é apagado; só é marcado como estornado. | RB-01 |
| INV-5 | Toda operação que cria ou altera fornecedor, conta ou pagamento gera registro de auditoria na mesma transação. | RB-01, RNF-09 |
| INV-6 | O documento identifica um único fornecedor. | RF-87 |
| INV-7 | Nenhum perfil chamado Cliente existe no controle de acesso. | OPEN-57 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | nenhum fornecedor | o Operador cadastra "Distribuidora de Pneus Ltda" com CNPJ válido e contato | o fornecedor é criado, com um registro de auditoria por campo | RF-87, RB-01 |
| CA-02 | um fornecedor com o CNPJ X | o Operador cadastra outro com o mesmo CNPJ, com ou sem pontuação | o cadastro é recusado com o motivo no campo documento | RF-87, INV-6, E1 |
| CA-03 | um fornecedor cadastrado | o Operador cadastra uma conta de R$ 1.200,00 com vencimento futuro | a conta nasce Aberta, com saldo de R$ 1.200,00 | RF-88 |
| CA-04 | — | o Operador cadastra conta para fornecedor inexistente, sem descrição ou com valor zero | o cadastro é recusado e nada é gravado | RF-88, E2 |
| CA-05 | uma conta Aberta de R$ 1.200,00 | o Operador paga R$ 500,00 e depois R$ 700,00 | o saldo vai a R$ 700,00, com a conta Aberta, e depois a R$ 0,00, com a conta Paga | RF-91, RB-31, INV-2 |
| CA-06 | uma conta com saldo de R$ 700,00 | o Operador paga R$ 700,01, R$ 0,00 ou com data de amanhã | o pagamento é recusado e o saldo não muda | RB-32, E3 |
| CA-07 | uma conta Paga ou Cancelada | o Operador registra um pagamento | é recusado, com o estado no motivo | RB-31, E3 |
| CA-08 | uma conta Aberta com vencimento ontem | o agendador executa a verificação | a conta passa a Vencida, com registro automático na auditoria; a de vencimento hoje continua Aberta | RF-90 |
| CA-09 | uma conta Paga, com vencimento passado | o Dono estorna o pagamento com motivo | o saldo volta e a conta passa a Vencida | RF-92 |
| CA-10 | uma conta com um pagamento | o Operador tenta estornar ou cancelar; o Dono tenta sem motivo | as três operações são recusadas | RB-33, E4 |
| CA-11 | uma conta Aberta | o Dono cancela com motivo | a conta passa a Cancelada e o motivo fica na auditoria | RF-93 |
| CA-12 | contas de dois fornecedores, em estados diferentes | o usuário filtra por um fornecedor e pelo estado Vencida | aparecem só as contas Vencidas daquele fornecedor, ordenadas por vencimento | RF-89 |
| CA-13 | o Contador | consulta fornecedores e contas; tenta cadastrar fornecedor, conta ou pagamento | consulta normalmente; as alterações são negadas, e as células estão fixadas na matriz | RB-03 |
| CA-14 | títulos a receber e contas a pagar vencidos e nos próximos 15 dias | a Dona abre o painel | a régua do caixa mostra o total a pagar e o saldo previsto (a receber menos a pagar) | RF-94 |
| CA-15 | a interface web | o Operador cadastra fornecedor e conta, registra pagamento pela tela; o Dono estorna e cancela pela tela | cada operação funciona pela tela, e recusas voltam com o motivo no campo | RF-87 a RF-93 |
| CA-16 | a tela de Permissões e a lista de perfis | o Administrador abre a tela | não há coluna nem opção "Cliente"; um banco antigo é migrado sem perda | OPEN-57, INV-7 |
| CA-17 | o banco de uma versão anterior | a aplicação é iniciada | as tabelas novas são criadas e Dono e Operador ganham as permissões novas, como na matriz inicial | ADR-007 |

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-56 | Contas a pagar entram no produto? | Não: decidida em 2026-10-31. |
| OPEN-57 | O perfil Cliente continua no controle de acesso? | Não: decidida em 2026-10-31. |

## 8. Verificação

*(preenchida após a implementação)*
