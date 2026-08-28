Requisitos Funcionais em EARS
Gestão de clientes e usuários
RF01 — Quando um usuário autorizado solicitar o cadastro de um cliente, o sistema deverá cadastrar o cliente com seus dados obrigatórios.
RF02 — Quando um administrador solicitar o cadastro de um usuário, o sistema deverá cadastrar o usuário e associá-lo a um perfil de acesso.
RF03 — Quando um administrador configurar as permissões de um perfil, o sistema deverá associar as permissões configuradas ao perfil.
RF04 — Sempre que um usuário executar uma operação relevante no sistema, o sistema deverá registrar o usuário responsável pela operação.
RF05 — Sempre que um usuário alterar um registro, o sistema deverá armazenar o histórico da alteração.
Gestão de orçamentos
RF06 — Quando um usuário autorizado solicitar a criação de um orçamento, o sistema deverá criar um orçamento associado a um cliente.
RF07 — Quando um usuário incluir itens em um orçamento, o sistema deverá calcular e armazenar quantidades, valores, descontos e condições de pagamento.
RF08 — Quando um usuário solicitar o envio de um orçamento, o sistema deverá disponibilizar o orçamento ao cliente pelo canal configurado.
RF09 — Quando o cliente aprovar ou rejeitar um orçamento, o sistema deverá registrar a decisão e atualizar o estado do orçamento.
RF10 — Quando um usuário consultar os orçamentos, o sistema deverá permitir a filtragem por cliente, período e estado.
RF11 — Quando um orçamento aprovado for convertido, o sistema deverá gerar um título financeiro associado ao orçamento.
RF12 — Se um usuário tentar converter um orçamento que não esteja aprovado, o sistema deverá impedir a conversão e informar o motivo.
RF13 — Quando um usuário autorizado cancelar um orçamento, o sistema deverá alterar seu estado para cancelado e registrar a operação.
Descontos e alçadas
RF14 — Quando um administrador configurar uma alçada de desconto, o sistema deverá associar o percentual máximo ao perfil ou usuário definido.
RF15 — Quando um usuário informar um desconto em um orçamento, o sistema deverá comparar o desconto informado com a alçada do usuário.
RF16 — Se o desconto informado ultrapassar a alçada do usuário, o sistema deverá solicitar aprovação de um usuário autorizado.
RF17 — Quando um usuário autorizado aprovar ou rejeitar um desconto excepcional, o sistema deverá registrar o responsável, a decisão e a data.
RF18 — Sempre que o desconto ou valor de um orçamento for alterado, o sistema deverá registrar o valor anterior e o novo valor.
Títulos e contas a receber
RF19 — Quando um orçamento aprovado for convertido em título, o sistema deverá gerar o título com os dados financeiros correspondentes.
RF20 — Quando um usuário autorizado solicitar o cadastro manual de um título, o sistema deverá criar o título com os dados obrigatórios.
RF21 — Sempre que um título for criado, o sistema deverá armazenar seu valor, vencimento, cliente, origem, condição de pagamento e estado.
RF22 — Quando um usuário consultar os títulos, o sistema deverá permitir a filtragem por cliente, vencimento, estado e período.
RF23 — Quando um título atingir o período configurado como próximo do vencimento, o sistema deverá identificá-lo como próximo do vencimento.
RF24 — Quando a data de vencimento de um título for ultrapassada sem pagamento registrado, o sistema deverá identificá-lo como vencido.
RF25 — Quando um usuário autorizado registrar um pagamento, o sistema deverá associar o pagamento ao título correspondente.
RF26 — Quando o pagamento integral de um título for registrado, o sistema deverá realizar a baixa do título.
RF27 — Quando um pagamento parcial for registrado, o sistema deverá atualizar o saldo restante do título.
RF28 — Quando um usuário autorizado solicitar uma renegociação, o sistema deverá registrar as novas condições e manter o vínculo com o título original.
RF29 — Sempre que uma renegociação for realizada, o sistema deverá registrar as condições anteriores e posteriores à renegociação.
RF30 — Quando um usuário autorizado solicitar o estorno de uma baixa, o sistema deverá reverter a baixa e registrar a operação.
RF31 — Sempre que uma operação financeira crítica for cancelada, estornada ou alterada, o sistema deverá registrar o motivo informado pelo usuário.
Cobrança automática
RF32 — Quando um administrador configurar uma sequência de cobrança, o sistema deverá armazenar as etapas, prazos e mensagens definidos.
RF33 — Quando um título atingir uma etapa de cobrança anterior ao vencimento, o sistema deverá enviar o lembrete configurado.
RF34 — Quando um título permanecer vencido e atingir uma etapa de cobrança posterior ao vencimento, o sistema deverá enviar a cobrança configurada.
RF35 — Sempre que uma cobrança for enviada, o sistema deverá registrar a data, etapa e resultado do envio.
RF36 — Quando um administrador configurar uma etapa de cobrança, o sistema deverá permitir definir seu prazo, mensagem e ação.
RF37 — Quando um título for baixado, o sistema deverá interromper as cobranças automáticas pendentes.
RF38 — Quando uma cobrança exigir intervenção manual, o sistema deverá encaminhar a tarefa ao responsável configurado.
RF39 — Quando um usuário consultar o histórico de cobrança de um título, o sistema deverá apresentar as tentativas realizadas e seus respectivos resultados.
Calendário de obrigações
RF40 — Quando um usuário autorizado cadastrar uma obrigação, o sistema deverá armazenar seu tipo, periodicidade, prazo e responsável.
RF41 — Quando uma obrigação for cadastrada, o sistema deverá permitir definir seu responsável e prazo de cumprimento.
RF42 — Quando uma obrigação recorrente for concluída, o sistema deverá gerar a próxima ocorrência conforme sua periodicidade.
RF43 — Quando um usuário acessar o calendário, o sistema deverá apresentar as obrigações conforme suas respectivas datas.
RF44 — Quando uma obrigação atingir o período configurado para aviso antecipado, o sistema deverá enviar um alerta ao responsável.
RF45 — Quando o responsável registrar o cumprimento de uma obrigação, o sistema deverá alterar o estado da obrigação para cumprida.
RF46 — Quando o responsável concluir uma obrigação que exija evidência, o sistema deverá permitir anexar a evidência correspondente.
RF47 — Sempre que uma obrigação for marcada como cumprida, o sistema deverá registrar a data, o usuário e a evidência associada, quando aplicável.
RF48 — Quando uma obrigação ultrapassar seu prazo sem registro de cumprimento, o sistema deverá identificá-la como atrasada.
RF49 — Quando uma obrigação permanecer atrasada pelo período configurado, o sistema deverá escalar o alerta ao proprietário ou responsável superior.
RF50 — Quando um usuário consultar uma obrigação, o sistema deverá apresentar seu histórico de cumprimento, atrasos e alterações.
Apuração do resultado
RF51 — Sempre que um lançamento financeiro for gerado pelo ciclo operacional, o sistema deverá disponibilizá-lo para a apuração do resultado.
RF52 — Quando um usuário classificar um lançamento financeiro, o sistema deverá associá-lo à categoria selecionada.
RF53 — Quando um usuário consultar as receitas, o sistema deverá apresentar os valores conforme o período selecionado.
RF54 — Quando um usuário consultar as despesas, o sistema deverá apresentar os valores conforme o período selecionado.
RF55 — Quando um usuário solicitar a apuração de um período, o sistema deverá calcular o resultado conforme os lançamentos considerados no período.
RF56 — Quando um usuário solicitar a demonstração de resultado, o sistema deverá apresentar receitas, despesas e resultado conforme as classificações financeiras.
RF57 — Quando um usuário consultar o resultado, o sistema deverá permitir filtrá-lo por período e categoria.
RF58 — Quando um lançamento não possuir classificação válida, o sistema deverá identificá-lo como pendente de classificação.
RF59 — Quando um usuário autorizado alterar a classificação de um lançamento, o sistema deverá atualizar a classificação e registrar a alteração.
RF60 — Sempre que a classificação de um lançamento for alterada, o sistema deverá armazenar o histórico da alteração.
Auditoria
RF61 — Sempre que uma operação relevante for executada, o sistema deverá registrar a operação para fins de auditoria.
RF62 — Sempre que uma operação for registrada para auditoria, o sistema deverá armazenar, no mínimo, usuário, data, operação e registro afetado.
RF63 — Sempre que um valor financeiro for alterado, o sistema deverá registrar o valor anterior e o novo valor.
RF64 — Quando um usuário autorizado consultar a auditoria, o sistema deverá permitir filtrar os registros por usuário, período e tipo de operação.