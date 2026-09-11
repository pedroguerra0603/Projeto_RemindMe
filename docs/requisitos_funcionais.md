Requisitos Funcionais - Projeto RemindMe
1. Gestão de clientes e usuários
RF01: WHEN um usuário autorizado solicitar o cadastro de um cliente THE SYSTEM SHALL cadastrar o cliente com seus dados obrigatórios.
RF02: WHEN um administrador solicitar o cadastro de um usuário THE SYSTEM SHALL cadastrar o usuário e associá-lo a um perfil de acesso.
RF03: WHEN um administrador configurar as permissões de um perfil THE SYSTEM SHALL associar as permissões configuradas ao perfil.
RF04: WHEN um usuário executar uma operação relevante no sistema THE SYSTEM SHALL registrar o usuário responsável pela operação.
RF05: WHEN um usuário alterar um registro THE SYSTEM SHALL armazenar o histórico da alteração.

2. Gestão de orçamentos
RF06: WHEN um usuário autorizado solicitar a criação de um orçamento THE SYSTEM SHALL criar um orçamento associado a um cliente.
RF07: WHEN um usuário incluir itens em um orçamento THE SYSTEM SHALL calcular e armazenar quantidades, valores, descontos e condições de pagamento.
RF08: WHEN um usuário solicitar o envio de um orçamento THE SYSTEM SHALL disponibilizar o orçamento ao cliente pelo canal configurado.
RF09: WHEN o cliente aprovar ou rejeitar um orçamento THE SYSTEM SHALL registrar a decisão e atualizar o estado do orçamento.
RF10: WHEN um usuário consultar os orçamentos THE SYSTEM SHALL permitir a filtragem por cliente, período e estado.
RF11: WHEN um orçamento aprovado for convertido THE SYSTEM SHALL gerar um título financeiro associado ao orçamento.
RF12: IF um usuário tentar converter um orçamento que não esteja aprovado THE SYSTEM SHALL impedir a conversão e informar o motivo.
RF13: WHEN um usuário autorizado cancelar um orçamento THE SYSTEM SHALL alterar seu estado para cancelado e registrar a operação.

3. Descontos e alçadas
RF14: WHEN um administrador configurar uma alçada de desconto THE SYSTEM SHALL associar o percentual máximo ao perfil ou usuário definido.
RF15: WHEN um usuário informar um desconto em um orçamento THE SYSTEM SHALL comparar o desconto informado com a alçada do usuário.
RF16: IF o desconto informado ultrapassar a alçada do usuário THE SYSTEM SHALL solicitar aprovação de um usuário autorizado.
RF17: WHEN um usuário autorizado aprovar ou rejeitar um desconto excepcional THE SYSTEM SHALL registrar o responsável, a decisão e a data.
RF18: WHEN o desconto ou valor de um orçamento for alterado THE SYSTEM SHALL registrar o valor anterior e o novo valor.

4. Títulos e contas a receber
RF19: WHEN um orçamento aprovado for convertido em título THE SYSTEM SHALL gerar o título com os dados financeiros correspondentes.
RF20: WHEN um usuário autorizado solicitar o cadastro manual de um título THE SYSTEM SHALL criar o título com os dados obrigatórios.
RF21: WHEN um título for criado THE SYSTEM SHALL armazenar seu valor, vencimento, cliente, origem, condição de pagamento e estado.
RF22: WHEN um usuário consultar os títulos THE SYSTEM SHALL permitir a filtragem por cliente, vencimento, estado e período.
RF23: WHEN um título atingir o período configurado como próximo do vencimento THE SYSTEM SHALL identificá-lo como próximo do vencimento.
RF24: WHEN a data de vencimento de um título for ultrapassada sem pagamento registrado THE SYSTEM SHALL identificá-lo como vencido.
RF25: WHEN um usuário autorizado registrar um pagamento THE SYSTEM SHALL associar o pagamento ao título correspondente.
RF26: WHEN o pagamento integral de um título for registrado THE SYSTEM SHALL realizar a baixa do título.
RF27: WHEN um pagamento parcial for registrado THE SYSTEM SHALL atualizar o saldo restante do título.
RF28: WHEN um usuário autorizado solicitar uma renegociação THE SYSTEM SHALL registrar as novas condições e manter o vínculo com o título original.
RF29: WHEN uma renegociação for realizada THE SYSTEM SHALL registrar as condições anteriores e posteriores à renegociação.
RF30: WHEN um usuário autorizado solicitar o estorno de uma baixa THE SYSTEM SHALL reverter a baixa e registrar a operação.
RF31: WHEN uma operação financeira crítica for cancelada, estornada ou alterada THE SYSTEM SHALL registrar o motivo informado pelo usuário.

5. Cobrança automática
RF32: WHEN um administrador configurar uma sequência de cobrança THE SYSTEM SHALL armazenar as etapas, prazos e mensagens definidos.
RF33: WHEN um título atingir uma etapa de cobrança anterior ao vencimento THE SYSTEM SHALL enviar o lembrete configurado.
RF34: WHEN um título permanecer vencido e atingir uma etapa de cobrança posterior ao vencimento THE SYSTEM SHALL enviar a cobrança configurada.
RF35: WHEN uma cobrança for enviada THE SYSTEM SHALL registrar a data, etapa e resultado do envio.
RF36: WHEN um administrador configurar uma etapa de cobrança THE SYSTEM SHALL permitir definir seu prazo, mensagem e ação.
RF37: WHEN um título for baixado THE SYSTEM SHALL interromper as cobranças automáticas pendentes.
RF38: WHEN uma cobrança exigir intervenção manual THE SYSTEM SHALL encaminhar a tarefa ao responsável configurado.
RF39: WHEN um usuário consultar o histórico de cobrança de um título THE SYSTEM SHALL apresentar as tentativas realizadas e seus respectivos resultados.

6. Calendário de obrigações
RF40: WHEN um usuário autorizado cadastrar uma obrigação THE SYSTEM SHALL armazenar seu tipo, periodicidade, prazo e responsável.
RF41: WHEN uma obrigação for cadastrada THE SYSTEM SHALL permitir definir seu responsável e prazo de cumprimento.
RF42: WHEN uma obrigação recorrente for concluída THE SYSTEM SHALL gerar a próxima ocorrência conforme sua periodicidade.
RF43: WHEN um usuário acessar o calendário THE SYSTEM SHALL apresentar as obrigações conforme suas respectivas datas.
RF44: WHEN uma obrigação atingir o período configurado para aviso antecipado THE SYSTEM SHALL enviar um alerta ao responsável.
RF45: WHEN o responsável registrar o cumprimento de uma obrigação THE SYSTEM SHALL alterar o estado da obrigação para cumprida.
RF46: WHEN o responsável concluir uma obrigação que exija evidência THE SYSTEM SHALL permitir anexar a evidência correspondente.
RF47: WHEN uma obrigação for marcada como cumprida THE SYSTEM SHALL registrar a data, o usuário e a evidência associada, quando aplicável.
RF48: WHEN uma obrigação ultrapassar seu prazo sem registro de cumprimento THE SYSTEM SHALL identificá-la como atrasada.
RF49: WHEN uma obrigação permanecer atrasada pelo período configurado THE SYSTEM SHALL escalar o alerta ao proprietário ou responsável superior.
RF50: WHEN um usuário consultar uma obrigação THE SYSTEM SHALL apresentar seu histórico de cumprimento, atrasos e alterações.

7. Apuração do resultado
RF51: WHEN um lançamento financeiro for gerado pelo ciclo operacional THE SYSTEM SHALL disponibilizá-lo para a apuração do resultado.
RF52: WHEN um usuário classificar um lançamento financeiro THE SYSTEM SHALL associá-lo à categoria selecionada.
RF53: WHEN um usuário consultar as receitas THE SYSTEM SHALL apresentar os valores conforme o período selecionado.
RF54: WHEN um usuário consultar as despesas THE SYSTEM SHALL apresentar os valores conforme o período selecionado.
RF55: WHEN um usuário solicitar a apuração de um período THE SYSTEM SHALL calcular o resultado conforme os lançamentos considerados no período.
RF56: WHEN um usuário solicitar a demonstração de resultado THE SYSTEM SHALL apresentar receitas, despesas e resultado conforme as classificações financeiras.
RF57: WHEN um usuário consultar o resultado THE SYSTEM SHALL permitir filtrá-lo por período e categoria.
RF58: IF um lançamento não possuir classificação válida THE SYSTEM SHALL identificá-lo como pendente de classificação.
RF59: WHEN um usuário autorizado alterar a classificação de um lançamento THE SYSTEM SHALL atualizar a classificação e registrar a alteração.
RF60: WHEN a classificação de um lançamento for alterada THE SYSTEM SHALL armazenar o histórico da alteração.

8. Auditoria
RF61: WHEN uma operação relevante for executada THE SYSTEM SHALL registrar a operação para fins de auditoria.
RF62: WHEN uma operação for registrada para auditoria THE SYSTEM SHALL armazenar, no mínimo, usuário, data, operação e registro afetado.
RF63: WHEN um valor financeiro for alterado THE SYSTEM SHALL registrar o valor anterior e o novo valor.
RF64: WHEN um usuário autorizado consultar a auditoria THE SYSTEM SHALL permitir filtrar os registros por usuário, período e tipo de operação.
