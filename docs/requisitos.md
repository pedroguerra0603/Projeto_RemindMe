# Requisitos — RemindMe

Especificação de requisitos do RemindMe: requisitos funcionais (RF), não funcionais (RNF) e regras de negócio (RB).

- **RF** dizem o que o sistema faz. Escritos em EARS, um comportamento por cláusula.
- **RNF** dizem como o sistema opera. Escritos em EARS, sempre com número ou condição verificável.
- **RB** são invariantes do domínio. Ficam em forma declarativa e indicam o RF que as aplica.

Os termos em itálico do domínio estão definidos no [glossário](glossario.md).

## Convenções

| Padrão EARS | Forma | Uso |
|---|---|---|
| Ubíquo | THE SYSTEM SHALL … | Vale sempre |
| Evento | WHEN … THE SYSTEM SHALL … | Reação a um evento pontual |
| Estado | WHILE … THE SYSTEM SHALL … | Vale enquanto um estado persiste |
| Indesejado | IF … THEN THE SYSTEM SHALL … | Erro, falha ou tentativa inválida |
| Opcional | WHERE … THE SYSTEM SHALL … | Depende de recurso habilitado |

| Obrigação | Significado |
|---|---|
| SHALL | Obrigatório. A falha reprova o aceite. |
| SHOULD | Recomendado. Não bloqueia a entrega. |
| MAY | Opcional. |

Identificadores: `RF-nn`, `RNF-nn`, `RB-nn`, `UC-nn`. Um identificador nunca é reaproveitado: requisito retirado fica marcado como retirado.

Valores marcados com **(P)** são metas propostas que a equipe ainda precisa confirmar. Estão listados em [`.specify/open.md`](../.specify/open.md).

---

## 1. Requisitos funcionais

### 1.1 Clientes, usuários e acesso

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-01 | WHEN um usuário autorizado submeter o cadastro de um cliente com nome e documento válidos, THE SYSTEM SHALL criar o cliente. | UC-03 | |
| RF-02 | WHEN o Administrador submeter o cadastro de um usuário, THE SYSTEM SHALL criar o usuário associado a exatamente um perfil. | UC-02 | |
| RF-03 | WHEN o Administrador alterar as permissões de um perfil, THE SYSTEM SHALL aplicar as novas permissões às operações seguintes dos usuários desse perfil. | UC-02 | |
| RF-04 | WHEN um usuário executar uma operação que cria, altera ou muda o estado de um registro, THE SYSTEM SHALL registrar o usuário responsável. | UC-12 | RB-01 |
| RF-05 | WHEN um usuário alterar um registro, THE SYSTEM SHALL armazenar o valor anterior e o novo valor de cada campo alterado. | UC-12 | RB-01 |
| RF-65 | WHEN um usuário submeter credenciais corretas, THE SYSTEM SHALL iniciar a sessão e apresentar apenas as funcionalidades do seu perfil. | UC-01 | |
| RF-66 | IF as credenciais submetidas forem inválidas, THEN THE SYSTEM SHALL recusar o acesso com mensagem que não revele qual campo está incorreto. | UC-01 | |
| RF-67 | IF um usuário solicitar uma operação que seu perfil não permite, THEN THE SYSTEM SHALL negar a operação e informar o motivo. | UC-01 | RB-03 |

### 1.2 Orçamentos

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-06 | WHEN um usuário autorizado solicitar um novo orçamento para um cliente cadastrado, THE SYSTEM SHALL criar o orçamento no estado Rascunho. | UC-04 | |
| RF-07 | WHEN um usuário incluir, alterar ou remover um item de um orçamento em Rascunho, THE SYSTEM SHALL recalcular o valor bruto, o desconto e o valor líquido do orçamento. | UC-04 | RB-24 |
| RF-08 | WHEN um usuário solicitar o envio de um orçamento em Rascunho com desconto dentro da alçada ou aprovado pelo Dono, THE SYSTEM SHALL disponibilizá-lo ao cliente pelo canal de notificação configurado e mudar o estado para Enviado. | UC-04 | RB-15, RB-24 |
| RF-09 | WHEN o cliente aprovar ou rejeitar um orçamento Enviado, THE SYSTEM SHALL registrar a decisão com data e mudar o estado para Aprovado ou Rejeitado. | UC-04 | |
| RF-10 | WHEN um usuário consultar orçamentos, THE SYSTEM SHALL permitir filtrar por cliente, período e estado. | UC-04 | |
| RF-11 | WHEN um orçamento passar ao estado Aprovado, THE SYSTEM SHALL gerar um título a receber vinculado a ele e mudar o estado do orçamento para Convertido. | UC-04 | RB-05 |
| RF-12 | IF for solicitada a conversão de um orçamento que não está Aprovado, THEN THE SYSTEM SHALL impedir a conversão e informar o estado atual. | UC-04 | RB-05 |
| RF-13 | WHEN um usuário autorizado cancelar um orçamento ainda não convertido, THE SYSTEM SHALL mudar o estado para Cancelado e registrar o motivo. | UC-04 | |

### 1.3 Descontos e alçadas

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-14 | WHEN o Administrador configurar uma alçada de desconto, THE SYSTEM SHALL associar o percentual máximo ao perfil indicado. | UC-13 | RB-15 |
| RF-15 | WHEN um usuário informar um desconto em um orçamento, THE SYSTEM SHALL comparar o percentual com a alçada do perfil do usuário. | UC-05 | RB-15 |
| RF-16 | IF o desconto informado ultrapassar a alçada do usuário, THEN THE SYSTEM SHALL mudar o orçamento para Pendente de Alçada e solicitar a decisão do Dono. | UC-05 | RB-15 |
| RF-17 | WHEN o Dono aprovar ou rejeitar um desconto pendente de alçada, THE SYSTEM SHALL registrar o responsável, a decisão e a data, e devolver o orçamento ao estado Rascunho. | UC-05 | RB-15 |
| RF-18 | WHEN o desconto ou o valor de um orçamento for alterado, THE SYSTEM SHALL registrar o valor anterior e o novo valor. | UC-05 | RB-01 |

### 1.4 Títulos e pagamentos

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-19 | WHEN o sistema gerar um título a partir de um orçamento, THE SYSTEM SHALL copiar do orçamento o cliente, o valor líquido e a condição de pagamento. | UC-04 | RB-05 |
| RF-20 | WHEN um usuário autorizado submeter o cadastro manual de um título com cliente, valor e vencimento válidos, THE SYSTEM SHALL criar o título no estado Aberto. | UC-06 | RB-21 |
| RF-21 | WHEN um título for criado, THE SYSTEM SHALL armazenar valor, vencimento, cliente, origem, condição de pagamento e estado. | UC-06 | |
| RF-22 | WHEN um usuário consultar títulos, THE SYSTEM SHALL permitir filtrar por cliente, vencimento, estado e período. | UC-06 | |
| RF-23 | WHILE faltar para o vencimento de um título Aberto um número de dias menor ou igual ao configurado, THE SYSTEM SHALL sinalizá-lo como próximo do vencimento. | UC-06 | |
| RF-24 | IF a data de vencimento de um título Aberto passar sem que o saldo seja zero, THEN THE SYSTEM SHALL mudar o estado para Vencido. | UC-06 | RB-21 |
| RF-25 | WHEN um usuário autorizado registrar um pagamento, THE SYSTEM SHALL associá-lo ao título e reduzir o saldo no valor pago. | UC-06 | RB-23 |
| RF-26 | WHEN o saldo de um título chegar a zero, THE SYSTEM SHALL mudar o estado para Baixado. | UC-06 | RB-22, RB-21 |
| RF-27 | WHEN um pagamento menor que o saldo for registrado, THE SYSTEM SHALL manter o estado do título e apresentar o saldo restante. | UC-06 | RB-22 |
| RF-28 | WHEN uma renegociação for aprovada, THE SYSTEM SHALL aplicar o novo vencimento ao título, devolvê-lo ao estado Aberto e manter o vínculo com as condições originais. | UC-07 | RB-28, RB-21 |
| RF-29 | WHEN uma renegociação for registrada, THE SYSTEM SHALL armazenar as condições anteriores, as novas condições, o responsável e a data. | UC-07 | RB-28 |
| RF-30 | WHEN o Dono solicitar o estorno de um pagamento, THE SYSTEM SHALL anular o pagamento, restaurar o saldo e devolver o título ao estado Aberto ou Vencido conforme o vencimento. | UC-06 | RB-02, RB-21 |
| RF-31 | IF um cancelamento, estorno ou alteração de valor for solicitado sem motivo informado, THEN THE SYSTEM SHALL recusar a operação. | UC-06 | RB-01 |
| RF-68 | IF o valor de um pagamento for maior que o saldo do título ou menor ou igual a zero, THEN THE SYSTEM SHALL recusar o pagamento. | UC-06 | RB-23 |
| RF-69 | WHEN um cliente autenticado consultar seus títulos, THE SYSTEM SHALL apresentar somente os títulos desse cliente, com valor, vencimento, saldo e estado. | UC-07 | RB-26 |

### 1.5 Cobrança automática

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-32 | WHEN o Administrador salvar uma régua de cobrança, THE SYSTEM SHALL armazenar suas etapas com prazo em dias, mensagem e ação. | UC-13 | |
| RF-33 | WHEN um título Aberto atingir o prazo de uma etapa anterior ao vencimento, THE SYSTEM SHALL enviar o lembrete da etapa ao cliente. | UC-08 | |
| RF-34 | WHILE um título estiver Vencido, WHEN ele atingir o prazo de uma etapa posterior ao vencimento, THE SYSTEM SHALL enviar a cobrança da etapa ao cliente. | UC-08 | RB-10 |
| RF-35 | WHEN o envio de uma etapa for tentado, THE SYSTEM SHALL registrar data, etapa e resultado da tentativa. | UC-08 | |
| RF-36 | WHEN o Administrador alterar uma etapa da régua, THE SYSTEM SHALL aplicar a alteração apenas aos envios ainda não realizados. | UC-13 | |
| RF-37 | WHEN um título for Baixado ou Cancelado, THE SYSTEM SHALL cancelar os envios pendentes da régua para esse título. | UC-08 | RB-10 |
| RF-38 | IF a ação de uma etapa for intervenção manual ou o envio falhar, THEN THE SYSTEM SHALL criar uma tarefa para o Operador Financeiro. | UC-08 | |
| RF-39 | WHEN um usuário consultar o histórico de cobrança de um título, THE SYSTEM SHALL apresentar as tentativas em ordem cronológica com seus resultados. | UC-08 | |
| RF-70 | WHILE um título estiver Em Renegociação, THE SYSTEM SHALL suspender os envios da régua para esse título. | UC-08 | RB-11 |
| RF-71 | WHERE o canal WhatsApp estiver habilitado, THE SYSTEM SHALL enviar cobranças e alertas por esse canal em vez do canal simulado. | UC-08 | RB-18 |

### 1.6 Renegociação assistida por IA

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-72 | WHEN uma mensagem de cliente for recebida, THE SYSTEM SHALL solicitar ao serviço de IA a extração de intenção, título, valor e data prometida. | UC-07 | RB-27 |
| RF-73 | WHILE um título estiver Vencido, WHEN for extraída de uma mensagem do cliente uma promessa de pagamento válida para esse título, THE SYSTEM SHALL mudar o estado do título para Em Renegociação. | UC-07 | RB-20, RB-21 |
| RF-74 | IF o serviço de IA não devolver dados estruturados válidos, THEN THE SYSTEM SHALL encaminhar a mensagem para tratamento manual pelo Operador Financeiro, sem alterar o título. | UC-07 | RB-17 |
| RF-75 | WHEN o sistema responder a uma mensagem de cliente, THE SYSTEM SHALL usar um template pré-aprovado preenchido com dados do título. | UC-07 | RB-27 |
| RF-76 | IF a proposta de renegociação estiver fora dos limites configurados, THEN THE SYSTEM SHALL encaminhá-la para decisão do Operador Financeiro ou do Dono. | UC-07 | RB-28 |

### 1.7 Calendário de obrigações

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-40 | WHEN um usuário autorizado cadastrar uma obrigação, THE SYSTEM SHALL armazenar tipo, periodicidade, prazo, responsável e se exige evidência. | UC-09 | |
| RF-41 | WHEN um usuário autorizado alterar o responsável ou o prazo de uma obrigação, THE SYSTEM SHALL registrar a alteração no histórico da obrigação. | UC-09 | RB-01 |
| RF-42 | WHEN uma obrigação recorrente for Cumprida, THE SYSTEM SHALL gerar a próxima ocorrência com o prazo calculado pela periodicidade. | UC-09 | |
| RF-43 | WHEN o Dono ou o Operador Financeiro acessar o calendário, THE SYSTEM SHALL apresentar as obrigações ordenadas por prazo. | UC-09 | RB-04 |
| RF-44 | WHEN faltar para o prazo de uma obrigação a antecedência de aviso configurada, THE SYSTEM SHALL enviar um alerta ao responsável. | UC-09 | RB-07 |
| RF-45 | WHEN o responsável registrar o cumprimento de uma obrigação que não exige evidência, THE SYSTEM SHALL mudar o estado para Cumprida. | UC-09 | |
| RF-46 | WHERE a obrigação exigir evidência, WHEN o responsável registrar o cumprimento, THE SYSTEM SHALL exigir o anexo da evidência antes de mudar o estado para Cumprida. | UC-09 | RB-29 |
| RF-47 | WHEN uma obrigação for Cumprida, THE SYSTEM SHALL registrar a data, o usuário e a evidência, quando houver. | UC-09 | RB-01 |
| RF-48 | IF o prazo de uma obrigação passar sem que ela esteja Cumprida, THEN THE SYSTEM SHALL mudar o estado para Atrasada. | UC-09 | |
| RF-49 | IF uma obrigação permanecer Atrasada pelo período de tolerância configurado, THEN THE SYSTEM SHALL enviar um alerta escalonado ao Dono. | UC-09 | RB-16 |
| RF-50 | WHEN um usuário consultar uma obrigação, THE SYSTEM SHALL apresentar o histórico de ocorrências, atrasos e alterações. | UC-09 | |
| RF-77 | WHILE uma obrigação estiver Aguardando Evidência, THE SYSTEM SHALL manter o alerta visível no painel do Operador Financeiro. | UC-09 | RB-13 |

### 1.8 Lançamentos e classificação assistida por IA

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-51 | WHEN um pagamento for registrado ou estornado, THE SYSTEM SHALL gerar o lançamento financeiro correspondente. | UC-10 | RB-06 |
| RF-52 | WHEN um usuário autorizado classificar um lançamento, THE SYSTEM SHALL associá-lo à categoria selecionada do plano de contas. | UC-10 | |
| RF-58 | WHILE um lançamento não tiver classificação confirmada, THE SYSTEM SHALL mantê-lo como Pendente de Classificação e fora da apuração. | UC-10 | RB-12 |
| RF-59 | WHEN um usuário autorizado alterar a classificação de um lançamento, THE SYSTEM SHALL atualizar a categoria e registrar a alteração. | UC-10 | RB-01 |
| RF-60 | *Retirado.* Coberto por RF-05 e RF-59. | | |
| RF-78 | WHEN um lançamento for gerado, THE SYSTEM SHALL solicitar ao serviço de IA uma sugestão de categoria com grau de confiança. | UC-10 | RB-08 |
| RF-79 | WHEN a sugestão indicar uma categoria existente no plano de contas com confiança maior ou igual ao limiar configurado, THE SYSTEM SHALL confirmar a classificação automaticamente. | UC-10 | RB-08 |
| RF-80 | IF a sugestão tiver confiança abaixo do limiar, indicar categoria inexistente ou o serviço de IA falhar, THEN THE SYSTEM SHALL colocar o lançamento na fila de revisão humana. | UC-10 | RB-14 |
| RF-81 | WHEN um usuário confirmar uma categoria diferente da sugerida, THE SYSTEM SHALL registrar a divergência com a sugestão original, a categoria final e o usuário. | UC-10 | RB-09 |

### 1.9 Apuração do resultado

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-53 | WHEN um usuário consultar receitas de um período, THE SYSTEM SHALL apresentar a soma dos lançamentos de receita classificados, por categoria. | UC-11 | RB-12 |
| RF-54 | WHEN um usuário consultar despesas de um período, THE SYSTEM SHALL apresentar a soma dos lançamentos de despesa classificados, por categoria. | UC-11 | RB-12 |
| RF-55 | WHEN um usuário solicitar a apuração de um período, THE SYSTEM SHALL calcular o resultado como receitas menos despesas dos lançamentos classificados do período. | UC-11 | RB-06, RB-12 |
| RF-56 | WHEN um usuário solicitar a demonstração de resultado, THE SYSTEM SHALL apresentar receitas, despesas e resultado agrupados por categoria. | UC-11 | |
| RF-57 | WHEN um usuário consultar o resultado, THE SYSTEM SHALL permitir filtrar por período e categoria. | UC-11 | |
| RF-82 | WHEN a apuração for apresentada, THE SYSTEM SHALL informar a quantidade e o valor total dos lançamentos Pendentes de Classificação do período. | UC-11 | RB-12 |

### 1.10 Auditoria

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-61 | WHEN um orçamento, título, pagamento, obrigação ou lançamento mudar de estado, THE SYSTEM SHALL criar um registro de auditoria. | UC-12 | RB-01 |
| RF-62 | WHEN um registro de auditoria for criado, THE SYSTEM SHALL armazenar usuário, data e hora, operação e registro afetado. | UC-12 | RB-01 |
| RF-63 | *Retirado.* Coberto por RF-05 e RF-18. | | |
| RF-64 | WHEN um usuário autorizado consultar a auditoria, THE SYSTEM SHALL permitir filtrar por usuário, período e tipo de operação. | UC-12 | |

### 1.11 Importação e exportação

| ID | Cláusula | UC | RB |
|---|---|---|---|
| RF-83 | WHEN um usuário autorizado enviar um arquivo CSV de clientes ou títulos, THE SYSTEM SHALL validar formato, colunas obrigatórias e valores, e apresentar os erros por linha antes de importar. | UC-14 | RB-19 |
| RF-84 | IF o arquivo enviado tiver qualquer linha inválida, THEN THE SYSTEM SHALL recusar a importação inteira. | UC-14 | RB-19 |
| RF-85 | WHEN um usuário autorizado solicitar a exportação de títulos, lançamentos ou da demonstração de resultado, THE SYSTEM SHALL gerar um arquivo CSV com os dados filtrados. | UC-14 | RB-19 |

---

## 2. Requisitos não funcionais

### 2.1 Segurança e privacidade

| ID | Cláusula | Verificação |
|---|---|---|
| RNF-01 | THE SYSTEM SHALL exigir autenticação em toda funcionalidade, exceto a tela de login. | Teste de acesso sem sessão a cada rota |
| RNF-02 | THE SYSTEM SHALL negar por padrão qualquer operação que não esteja explicitamente permitida ao perfil do usuário. | Teste por perfil × operação |
| RNF-03 | THE SYSTEM SHALL validar permissões e alçadas no servidor, independentemente da interface. | Teste chamando a operação sem a interface |
| RNF-04 | THE SYSTEM SHALL armazenar senhas somente como hash com salt, gerado por algoritmo adaptativo. | Inspeção do armazenamento |
| RNF-05 | THE SYSTEM SHALL trafegar dados entre navegador e servidor somente por HTTPS. | Teste de requisição HTTP sem TLS |
| RNF-06 | THE SYSTEM SHALL impedir a alteração e a exclusão de registros de auditoria por qualquer perfil. | Teste de tentativa de alteração |
| RNF-22 | THE SYSTEM SHALL enviar ao serviço de IA apenas a descrição do lançamento ou o texto da mensagem, sem nome, documento ou contato do cliente. | Inspeção do payload enviado |
| RNF-25 | THE SYSTEM SHALL restringir o perfil Cliente aos dados do próprio cliente. | Teste de acesso a título de outro cliente |

### 2.2 Confiabilidade

| ID | Cláusula | Verificação |
|---|---|---|
| RNF-07 | THE SYSTEM SHOULD estar disponível em 99% do tempo de cada mês **(P)**. | Monitoramento |
| RNF-08 | THE SYSTEM SHALL executar backup diário dos dados e manter as cópias dos últimos 7 dias **(P)**. | Verificação da rotina e de uma restauração |
| RNF-09 | IF ocorrer falha durante uma operação financeira, THEN THE SYSTEM SHALL desfazer todas as alterações da operação. | Teste com falha injetada |
| RNF-10 | *Retirado.* Coberto por RNF-09 e RF-84. | |
| RNF-24 | IF o serviço de IA não responder em 10 segundos **(P)**, THEN THE SYSTEM SHALL tratar a chamada como falha. | Teste com serviço simulado lento |

### 2.3 Desempenho

| ID | Cláusula | Verificação |
|---|---|---|
| RNF-11 | THE SYSTEM SHALL responder a 95% das operações de consulta e cadastro em menos de 2 segundos. | Medição de P95 |
| RNF-12 | WHEN um envio da régua atingir o horário programado, THE SYSTEM SHALL processá-lo em até 5 minutos. | Medição do atraso de envio |
| RNF-13 | WHILE o sistema processar cobranças, alertas ou apurações em lote, THE SYSTEM SHALL manter o limite de RNF-11 para as operações interativas. | Medição de P95 durante lote |

### 2.4 Usabilidade

| ID | Cláusula | Verificação |
|---|---|---|
| RNF-14 | IF uma entrada for inválida, THEN THE SYSTEM SHALL informar o campo e o motivo da recusa. | Teste por campo |
| RNF-15 | THE SYSTEM SHALL destacar no painel os títulos Vencidos e as obrigações Atrasadas. | Inspeção do painel |
| RNF-16 | THE SYSTEM SHALL apresentar o estado atual em toda tela de orçamento, título e obrigação. | Inspeção das telas |
| RNF-17 | WHEN um usuário iniciar a sessão, THE SYSTEM SHALL apresentar o painel com pendências financeiras, cobranças e obrigações do seu perfil sem navegação adicional. | Inspeção por perfil |

### 2.5 Manutenibilidade e evolução

| ID | Cláusula | Verificação |
|---|---|---|
| RNF-18 | WHEN uma regra configurável de cobrança, alçada ou obrigação for alterada, THE SYSTEM SHALL aplicá-la apenas a processamentos futuros. | Teste de alteração com registros existentes |
| RNF-19 | THE SYSTEM SHALL implementar cada regra de negócio em um único ponto do domínio, coberto por ao menos um teste nomeado pelo identificador da regra. | Revisão de código e suíte de testes |
| RNF-20 | THE SYSTEM SHALL permitir criar tipos de obrigação, categorias financeiras e etapas de cobrança por configuração, sem alteração de código. | Teste de cadastro e uso |
| RNF-21 | IF ocorrer um erro não tratado, THEN THE SYSTEM SHALL registrar data, operação, usuário e identificador de correlação. | Inspeção de log |
| RNF-23 | THE SYSTEM SHALL executar toda a suíte de testes sem credenciais de serviços externos, usando o canal de notificação e o serviço de IA simulados. | Execução da suíte em ambiente limpo |
| RNF-26 | THE SYSTEM SHALL registrar cada chamada ao serviço de IA com duração, resultado e confiança devolvida. | Inspeção de log |

---

## 3. Regras de negócio

Regras de negócio são verdades do domínio que existiriam mesmo sem o sistema. Por isso ficam em forma declarativa, e não em EARS. A coluna "Aplicada por" aponta os RF que as fazem valer.

| ID | Regra | Aplicada por |
|---|---|---|
| RB-01 | Toda mudança de estado de orçamento, título, pagamento, obrigação ou lançamento tem responsável, data e ação registrados. | RF-04, RF-05, RF-61, RF-62 |
| RB-02 | Somente o Dono estorna um pagamento. | RF-30 |
| RB-03 | O Contador consulta e exporta dados financeiros, mas não cria nem altera registros. | RF-67 |
| RB-04 | O calendário de obrigações é único para a empresa e visível ao Dono e ao Operador Financeiro. | RF-43 |
| RB-05 | Orçamento aprovado pelo cliente vira título a receber, e somente orçamento aprovado vira título. | RF-11, RF-12, RF-19 |
| RB-06 | O resultado financeiro reflete todo pagamento registrado ou estornado, sem etapa manual de fechamento. | RF-51, RF-55 |
| RB-07 | Toda obrigação é avisada ao responsável antes do prazo. A antecedência padrão é de 7 dias e pode ser configurada por tipo de obrigação. | RF-44 |
| RB-08 | Uma sugestão de classificação da IA só vale se apontar uma categoria existente no plano de contas e tiver confiança igual ou superior ao limiar configurado. | RF-78, RF-79 |
| RB-09 | Toda correção humana de uma sugestão da IA fica registrada como divergência. | RF-81 |
| RB-10 | Título Vencido é cobrado pela régua até ser Baixado, Cancelado ou entrar em renegociação. | RF-34, RF-37 |
| RB-11 | Título Em Renegociação não recebe cobrança automática. | RF-70 |
| RB-12 | Lançamento sem classificação confirmada não entra na apuração do resultado. | RF-58, RF-53, RF-54, RF-55, RF-82 |
| RB-13 | Obrigação Aguardando Evidência permanece como pendência visível do Operador Financeiro. | RF-77 |
| RB-14 | Sugestão da IA que não atende à RB-08 é decidida por uma pessoa. | RF-80 |
| RB-15 | Cada perfil tem um percentual máximo de desconto (alçada). Desconto acima da alçada de quem elaborou o orçamento depende de aprovação do Dono. O Dono não tem limite. | RF-14, RF-15, RF-16, RF-17 |
| RB-16 | Obrigação Atrasada é escalada ao Dono. A tolerância padrão é de 0 dias e pode ser configurada. | RF-49 |
| RB-17 | Mensagem de cliente da qual não se extrai intenção válida é tratada por uma pessoa. | RF-74 |
| RB-18 | O canal de notificação é substituível. O canal padrão é o simulado. | RF-71 |
| RB-19 | A troca de dados com planilhas ocorre somente em CSV, e uma importação é aceita inteira ou recusada inteira. | RF-83, RF-84, RF-85 |
| RB-20 | Promessa de pagamento válida do cliente sobre um título Vencido coloca o título Em Renegociação. | RF-73 |
| RB-21 | Um título está em exatamente um estado: Aberto, Vencido, Em Renegociação, Baixado ou Cancelado. As transições válidas estão no [diagrama de estados do título](uml/estados.md). | RF-20, RF-24, RF-26, RF-28, RF-30, RF-73 |
| RB-22 | Um título só é Baixado quando a soma dos pagamentos não estornados é igual ao seu valor. | RF-26, RF-27 |
| RB-23 | Um pagamento tem valor maior que zero e menor ou igual ao saldo do título. | RF-25, RF-68 |
| RB-24 | Um orçamento só é enviado se tiver ao menos um item. | RF-07, RF-08 |
| RB-26 | O cliente só vê e só propõe renegociação de títulos em que ele é o devedor. | RF-69 |
| RB-27 | A IA extrai e classifica; o sistema decide. Nenhum valor financeiro é produzido pela IA e nenhum texto gerado pela IA chega ao cliente. | RF-72, RF-75 |
| RB-28 | Uma renegociação altera as condições do título sem apagar as condições originais. Propostas fora dos limites configurados dependem de decisão humana. | RF-28, RF-29, RF-76 |
| RB-29 | Obrigação que exige evidência só é Cumprida com a evidência anexada. | RF-46 |
| RB-30 | Registros de auditoria não são alterados nem excluídos. | RNF-06 |

`RB-25` não foi usado.

### Histórico de identificadores

Até a revisão de outubro de 2026, as regras de negócio usavam o prefixo `RN` e estavam escritas em EARS. `RN01` a `RN20` correspondem a `RB-01` a `RB-20`, na mesma ordem. O comportamento que estava embutido nas antigas regras passou para os RF-65 em diante.
