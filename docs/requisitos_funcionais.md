# Requisitos Funcionais em EARS

## 1. Gestão de clientes e usuários

### RF01 - Cadastro de cliente
- Quando um usuário autorizado solicitar o cadastro de um cliente, o sistema deverá cadastrar o cliente com seus dados obrigatórios.

### RF02 - Cadastro de usuário
- Quando um administrador solicitar o cadastro de um usuário, o sistema deverá cadastrar o usuário e associá-lo a um perfil de acesso.

### RF03 - Configuração de permissões
- Quando um administrador configurar as permissões de um perfil, o sistema deverá associar as permissões configuradas ao perfil.

### RF04 - Registro de responsável
- Sempre que um usuário executar uma operação relevante no sistema, o sistema deverá registrar o usuário responsável pela operação.

### RF05 - Histórico de alteração
- Sempre que um usuário alterar um registro, o sistema deverá armazenar o histórico da alteração.

---

## 2. Gestão de orçamentos

### RF06 - Criação de orçamento
- Quando um usuário autorizado solicitar a criação de um orçamento, o sistema deverá criar um orçamento associado a um cliente.

### RF07 - Inclusão de itens
- Quando um usuário incluir itens em um orçamento, o sistema deverá calcular e armazenar quantidades, valores, descontos e condições de pagamento.

### RF08 - Envio de orçamento
- Quando um usuário solicitar o envio de um orçamento, o sistema deverá disponibilizar o orçamento ao cliente pelo canal configurado.

### RF09 - Aprovação ou rejeição
- Quando o cliente aprovar ou rejeitar um orçamento, o sistema deverá registrar a decisão e atualizar o estado do orçamento.

### RF10 - Filtro de consulta
- Quando um usuário consultar os orçamentos, o sistema deverá permitir a filtragem por cliente, período e estado.

### RF11 - Conversão em título
- Quando um orçamento aprovado for convertido, o sistema deverá gerar um título financeiro associado ao orçamento.

### RF12 - Bloqueio de conversão
- Se um usuário tentar converter um orçamento que não esteja aprovado, o sistema deverá impedir a conversão e informar o motivo.

### RF13 - Cancelamento de orçamento
- Quando um usuário autorizado cancelar um orçamento, o sistema deverá alterar seu estado para cancelado e registrar a operação.

---

## 3. Descontos e alçadas

### RF14 - Configuração de alçada
- Quando um administrador configurar uma alçada de desconto, o sistema deverá associar o percentual máximo ao perfil ou usuário definido.

### RF15 - Validação de desconto
- Quando um usuário informar um desconto em um orçamento, o sistema deverá comparar o desconto informado com a alçada do usuário.

### RF16 - Aprovação de desconto excepcional
- Se o desconto informado ultrapassar a alçada do usuário, o sistema deverá solicitar aprovação de um usuário autorizado.

### RF17 - Registro da decisão
- Quando um usuário autorizado aprovar ou rejeitar um desconto excepcional, o sistema deverá registrar o responsável, a decisão e a data.

### RF18 - Histórico de alterações de valor
- Sempre que o desconto ou valor de um orçamento for alterado, o sistema deverá registrar o valor anterior e o novo valor.

---

## 4. Títulos e contas a receber

### RF19 - Geração automática de título
- Quando um orçamento aprovado for convertido em título, o sistema deverá gerar o título com os dados financeiros correspondentes.

### RF20 - Cadastro manual de título
- Quando um usuário autorizado solicitar o cadastro manual de um título, o sistema deverá criar o título com os dados obrigatórios.

### RF21 - Armazenamento dos dados do título
- Sempre que um título for criado, o sistema deverá armazenar seu valor, vencimento, cliente, origem, condição de pagamento e estado.

### RF22 - Filtros de consulta
- Quando um usuário consultar os títulos, o sistema deverá permitir a filtragem por cliente, vencimento, estado e período.

### RF23 - Título próximo do vencimento
- Quando um título atingir o período configurado como próximo do vencimento, o sistema deverá identificá-lo como próximo do vencimento.

### RF24 - Título vencido
- Quando a data de vencimento de um título for ultrapassada sem pagamento registrado, o sistema deverá identificá-lo como vencido.

### RF25 - Registro de pagamento
- Quando um usuário autorizado registrar um pagamento, o sistema deverá associar o pagamento ao título correspondente.

### RF26 - Baixa do título
- Quando o pagamento integral de um título for registrado, o sistema deverá realizar a baixa do título.

### RF27 - Atualização do saldo restante
- Quando um pagamento parcial for registrado, o sistema deverá atualizar o saldo restante do título.

### RF28 - Renegociação
- Quando um usuário autorizado solicitar uma renegociação, o sistema deverá registrar as novas condições e manter o vínculo com o título original.

### RF29 - Histórico da renegociação
- Sempre que uma renegociação for realizada, o sistema deverá registrar as condições anteriores e posteriores à renegociação.

### RF30 - Estorno de baixa
- Quando um usuário autorizado solicitar o estorno de uma baixa, o sistema deverá reverter a baixa e registrar a operação.

### RF31 - Motivo da operação crítica
- Sempre que uma operação financeira crítica for cancelada, estornada ou alterada, o sistema deverá registrar o motivo informado pelo usuário.

---

## 5. Cobrança automática

### RF32 - Configuração da sequência
- Quando um administrador configurar uma sequência de cobrança, o sistema deverá armazenar as etapas, prazos e mensagens definidos.

### RF33 - Envio de lembrete
- Quando um título atingir uma etapa de cobrança anterior ao vencimento, o sistema deverá enviar o lembrete configurado.

### RF34 - Envio de cobrança vencida
- Quando um título permanecer vencido e atingir uma etapa de cobrança posterior ao vencimento, o sistema deverá enviar a cobrança configurada.

### RF35 - Registro do envio
- Sempre que uma cobrança for enviada, o sistema deverá registrar a data, etapa e resultado do envio.

### RF36 - Configuração da etapa
- Quando um administrador configurar uma etapa de cobrança, o sistema deverá permitir definir seu prazo, mensagem e ação.

### RF37 - Interrupção de cobranças
- Quando um título for baixado, o sistema deverá interromper as cobranças automáticas pendentes.

### RF38 - Intervenção manual
- Quando uma cobrança exigir intervenção manual, o sistema deverá encaminhar a tarefa ao responsável configurado.

### RF39 - Histórico de cobrança
- Quando um usuário consultar o histórico de cobrança de um título, o sistema deverá apresentar as tentativas realizadas e seus respectivos resultados.

---

## 6. Calendário de obrigações

### RF40 - Cadastro de obrigação
- Quando um usuário autorizado cadastrar uma obrigação, o sistema deverá armazenar seu tipo, periodicidade, prazo e responsável.

### RF41 - Definição de responsável e prazo
- Quando uma obrigação for cadastrada, o sistema deverá permitir definir seu responsável e prazo de cumprimento.

### RF42 - Próxima ocorrência
- Quando uma obrigação recorrente for concluída, o sistema deverá gerar a próxima ocorrência conforme sua periodicidade.

### RF43 - Visualização no calendário
- Quando um usuário acessar o calendário, o sistema deverá apresentar as obrigações conforme suas respectivas datas.

### RF44 - Alerta antecipado
- Quando uma obrigação atingir o período configurado para aviso antecipado, o sistema deverá enviar um alerta ao responsável.

### RF45 - Registro de cumprimento
- Quando o responsável registrar o cumprimento de uma obrigação, o sistema deverá alterar o estado da obrigação para cumprida.

### RF46 - Evidência obrigatória
- Quando o responsável concluir uma obrigação que exija evidência, o sistema deverá permitir anexar a evidência correspondente.

### RF47 - Histórico de cumprimento
- Sempre que uma obrigação for marcada como cumprida, o sistema deverá registrar a data, o usuário e a evidência associada, quando aplicável.

### RF48 - Identificação de atraso
- Quando uma obrigação ultrapassar seu prazo sem registro de cumprimento, o sistema deverá identificá-la como atrasada.

### RF49 - Escalonamento de alerta
- Quando uma obrigação permanecer atrasada pelo período configurado, o sistema deverá escalar o alerta ao proprietário ou responsável superior.

### RF50 - Histórico da obrigação
- Quando um usuário consultar uma obrigação, o sistema deverá apresentar seu histórico de cumprimento, atrasos e alterações.

---

## 7. Apuração do resultado

### RF51 - Disponibilização do lançamento
- Sempre que um lançamento financeiro for gerado pelo ciclo operacional, o sistema deverá disponibilizá-lo para a apuração do resultado.

### RF52 - Classificação do lançamento
- Quando um usuário classificar um lançamento financeiro, o sistema deverá associá-lo à categoria selecionada.

### RF53 - Consulta de receitas
- Quando um usuário consultar as receitas, o sistema deverá apresentar os valores conforme o período selecionado.

### RF54 - Consulta de despesas
- Quando um usuário consultar as despesas, o sistema deverá apresentar os valores conforme o período selecionado.

### RF55 - Cálculo do resultado
- Quando um usuário solicitar a apuração de um período, o sistema deverá calcular o resultado conforme os lançamentos considerados no período.

### RF56 - Demonstração de resultado
- Quando um usuário solicitar a demonstração de resultado, o sistema deverá apresentar receitas, despesas e resultado conforme as classificações financeiras.

### RF57 - Filtro de resultado
- Quando um usuário consultar o resultado, o sistema deverá permitir filtrá-lo por período e categoria.

### RF58 - Lançamento pendente de classificação
- Quando um lançamento não possuir classificação válida, o sistema deverá identificá-lo como pendente de classificação.

### RF59 - Alteração de classificação
- Quando um usuário autorizado alterar a classificação de um lançamento, o sistema deverá atualizar a classificação e registrar a alteração.

### RF60 - Histórico de alteração da classificação
- Sempre que a classificação de um lançamento for alterada, o sistema deverá armazenar o histórico da alteração.

---

## 8. Auditoria

### RF61 - Registro de operação relevante
- Sempre que uma operação relevante for executada, o sistema deverá registrar a operação para fins de auditoria.

### RF62 - Dados da auditoria
- Sempre que uma operação for registrada para auditoria, o sistema deverá armazenar, no mínimo, usuário, data, operação e registro afetado.

### RF63 - Registro de alteração de valor financeiro
- Sempre que um valor financeiro for alterado, o sistema deverá registrar o valor anterior e o novo valor.

### RF64 - Consulta da auditoria
- Quando um usuário autorizado consultar a auditoria, o sistema deverá permitir filtrar os registros por usuário, período e tipo de operação.
