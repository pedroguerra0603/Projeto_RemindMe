# Regras de Negócio - RemindMe

## 1. Introdução

As regras de negócio abaixo foram derivadas dos requisitos funcionais e não funcionais do sistema e definem o comportamento esperado do produto em termos de operação, segurança, controle financeiro e governança.

As regras têm como objetivo garantir consistência, rastreabilidade, integridade financeira e conformidade com as políticas internas da organização.

---

## 2. Gestão de clientes e usuários

### RB01 - Cadastro de cliente
- Somente usuários autorizados podem cadastrar clientes.
- O cadastro deve conter os dados obrigatórios exigidos pelo processo de negócio.
- O cliente deve ser identificado de forma única no sistema.

### RB02 - Cadastro de usuário
- Usuários só podem ser cadastrados por administradores.
- Todo usuário deve estar associado a um perfil de acesso.
- O perfil define as permissões disponíveis para o usuário.

### RB03 - Perfil e permissões
- As permissões configuradas em um perfil devem refletir exatamente as regras de acesso aplicáveis ao usuário.
- Qualquer alteração no perfil deve impactar imediatamente os usuários vinculados a ele.

### RB04 - Responsabilidade por operação
- Toda ação relevante no sistema deve registrar o usuário que executou a operação.
- O usuário registrado deve ser o responsável diretamente pela ação e não apenas o operador do sistema.

### RB05 - Histórico de alterações
- Toda alteração em registros de negócio deve ser registrada com identificação do usuário, data e descrição da mudança.
- O histórico deve permitir rastrear o valor anterior e o novo valor.

---

## 3. Gestão de orçamentos

### RB06 - Criação de orçamento
- Um orçamento deve estar sempre vinculado a um cliente cadastrado.
- O orçamento deve ser criado por um usuário com permissão para esse processo.
- O estado inicial do orçamento deve ser "em elaboração" ou equivalente.

### RB07 - Inclusão de itens
- Cada item do orçamento deve conter quantidade, valor unitário, condições de pagamento, descontos e observações relevantes.
- O sistema deve recalcular automaticamente o valor total do orçamento sempre que um item for alterado.

### RB08 - Envio do orçamento
- Um orçamento só pode ser enviado ao cliente quando estiver completo e válido para apresentação.
- O envio deve ocorrer pelo canal configurado para o cliente.
- O envio deve registrar data, usuário responsável e canal utilizado.

### RB09 - Aprovação e rejeição
- O cliente pode aprovar ou rejeitar o orçamento.
- A decisão deve ser registrada com data, responsável e motivo, quando houver.
- A aprovação altera o status do orçamento para "aprovado".

### RB10 - Consulta de orçamentos
- A consulta de orçamentos deve permitir filtros por cliente, período e estado.
- O sistema deve apresentar ao usuário apenas os dados permitidos pelo seu perfil.

### RB11 - Conversão em título
- Somente orçamentos aprovados podem ser convertidos em títulos financeiros.
- A conversão deve gerar um título com as informações financeiras correspondentes.
- A conversão deve manter o vínculo com o orçamento origem.

### RB12 - Bloqueio de conversão inválida
- Se o orçamento não estiver aprovado, a conversão deve ser bloqueada.
- O sistema deve informar o motivo do bloqueio ao usuário.

### RB13 - Cancelamento de orçamento
- Um orçamento pode ser cancelado apenas por usuário autorizado.
- O cancelamento deve alterar o estado do orçamento para "cancelado".
- A operação deve ser registrada na auditoria.

---

## 4. Descontos e alçadas

### RB14 - Alçada de desconto
- Cada perfil ou usuário deve possuir um percentual máximo de desconto autorizado.
- O percentual deve ser configurado por administrador.
- A alçada deve ser verificável em todas as operações que envolvam desconto.

### RB15 - Validação do desconto informado
- Ao informar um desconto em um orçamento, o sistema deve comparar o valor informado com a alçada do usuário.
- O desconto deve ser validado antes da confirmação final da operação.

### RB16 - Aprovação de desconto excepcional
- Se o desconto exceder a alçada do usuário, a operação deve exigir aprovação de um usuário autorizado.
- A aprovação deve registrar responsável, decisão e data.

### RB17 - Registro de decisão excepcional
- Todo desconto aprovado ou rejeitado deve ficar registrado com dados do responsável, decisão e data da aprovação.
- O registro deve ser mantido para fins de auditoria.

### RB18 - Histórico de valores alterados
- Sempre que um valor ou desconto de orçamento for alterado, o sistema deve registrar o valor anterior e o novo valor.
- A mudança deve permitir a identificação do usuário que alterou o dado.

---

## 5. Títulos e contas a receber

### RB19 - Geração automática de título
- Quando um orçamento aprovado é convertido, o sistema deve gerar um título com os dados financeiros correspondentes.
- O título deve conter valor, vencimento, cliente, origem, condição de pagamento e estado.

### RB20 - Cadastro manual de título
- Usuários autorizados podem cadastrar títulos manualmente.
- O título manual deve possuir todos os dados obrigatórios antes de ser salvo.

### RB21 - Estado do título
- O sistema deve controlar automaticamente o estado do título, incluindo pendente, próximo do vencimento, vencido, pago e baixado.
- A mudança de estado deve ser rastreada.

### RB22 - Consulta por filtros
- A consulta de títulos deve permitir filtros por cliente, vencimento, estado e período.
- A exibição deve respeitar as regras de acesso do usuário.

### RB23 - Vencimento próximo
- Quando um título estiver dentro do período configurado como próximo do vencimento, o sistema deve marcá-lo como tal.
- A marcação deve considerar a data atual e a regra configurada.

### RB24 - Título vencido
- Quando a data de vencimento for ultrapassada sem pagamento registrado, o título deve ser identificado como vencido.
- A classificação vencido deve impactar alertas e regras de cobrança e acompanhamento.

### RB25 - Registro de pagamento
- Pagamentos devem ser associados ao título correspondente.
- O sistema deve validar se o título existe e se o pagamento é aplicável ao caso.

### RB26 - Baixa automática
- Quando o pagamento integral for registrado, o sistema deve dar baixa no título.
- A baixa deve gerar a marcação de pagamento concluído e interromper eventos pendentes relacionados.

### RB27 - Pagamento parcial
- Quando o pagamento for parcial, o sistema deve atualizar o saldo restante do título.
- O saldo restante deve refletir a diferença entre o valor original e o valor pago.

### RB28 - Renegociação
- Usuários autorizados podem solicitar renegociação de títulos.
- A renegociação deve manter vínculo com o título original e registrar as novas condições.

### RB29 - Histórico da renegociação
- Toda renegociação deve manter o histórico das condições anteriores e posteriores.
- O registro deve permitir auditoria e acompanhamento do status do cliente.

### RB30 - Estorno de baixa
- Um usuário autorizado pode solicitar o estorno de uma baixa.
- O estorno deve reverter a baixa do título e registrar a operação.

### RB31 - Motivo em operação crítica
- Toda operação financeira crítica cancelada, estornada ou alterada deve exigir o registro do motivo informado pelo usuário.

---

## 6. Cobrança automática

### RB32 - Sequência de cobrança
- Toda sequência de cobrança deve conter etapas, prazos, mensagens e ações definidas por administrador.
- A sequência deve ser armazenada e aplicada conforme as regras configuradas.

### RB33 - Lembrete antes do vencimento
- Quando um título atingir uma etapa de cobrança anterior ao vencimento, o sistema deve enviar o lembrete configurado.
- O envio deve ser registrado com data, etapa e resultado.

### RB34 - Cobrança após vencimento
- Quando o título estiver vencido e atingir uma etapa posterior ao vencimento, o sistema deve enviar a cobrança correspondente.

### RB35 - Registro de envio
- Sempre que uma cobrança for enviada, o sistema deve registrar data, etapa e resultado do envio.
- O histórico deve permitir acompanhar tentativas e falhas.

### RB36 - Configuração da etapa
- A etapa de cobrança deve permitir definição de prazo, mensagem e ação.
- O administrador pode definir a lógica do disparo conforme o status do título.

### RB37 - Encerramento de cobranças
- Quando o título for baixado, as cobranças automáticas pendentes devem ser interrompidas.

### RB38 - Intervenção manual
- Se a cobrança exigir intervenção manual, o sistema deve encaminhar a tarefa ao responsável configurado.
- A tarefa deve manter rastreabilidade de quem assumiu a ação.

### RB39 - Histórico da cobrança
- O histórico de cobrança de um título deve listar as tentativas realizadas e seus resultados.

---

## 7. Calendário de obrigações

### RB40 - Cadastro de obrigação
- Usuários autorizados podem cadastrar obrigações com tipo, periodicidade, prazo e responsável.
- Cada obrigação deve possuir identificador único e descrição clara.

### RB41 - Responsável e prazo
- Quando uma obrigação é cadastrada, o sistema deve permitir definir responsável e prazo de cumprimento.
- O prazo deve ser validado conforme a periodicidade e o tipo da obrigação.

### RB42 - Geração de recorrência
- Quando uma obrigação recorrente for concluída, o sistema deve gerar automaticamente a próxima ocorrência conforme sua periodicidade.

### RB43 - Visualização no calendário
- O calendário deve apresentar obrigações conforme data, responsável, prazo e status.
- A exibição deve facilitar a priorização de ações.

### RB44 - Alerta antecipado
- Quando a obrigação atingir o período configurado para aviso antecipado, o sistema deve enviar alerta ao responsável.

### RB45 - Registro de cumprimento
- O responsável pode registrar o cumprimento da obrigação.
- O status da obrigação deve ser atualizado para "cumprida".

### RB46 - Evidência quando exigida
- Se a obrigação exigir evidência, o usuário deve poder anexar o documento ou comprovante correspondente.
- A evidência deve permanecer vinculada à obrigação.

### RB47 - Histórico de cumprimento
- Sempre que uma obrigação for marcada como cumprida, o sistema deve registrar data, usuário responsável e evidência associada, quando existir.

### RB48 - Obrigação atrasada
- Quando uma obrigação ultrapassar o prazo sem registro de cumprimento, ela deve ser identificada como atrasada.

### RB49 - Escalonamento de alerta
- Se a obrigação permanecer atrasada pelo período configurado, o sistema deve escalar o alerta para o proprietário ou responsável superior.

### RB50 - Histórico completo
- Ao consultar uma obrigação, o usuário deve visualizar o histórico de cumprimento, atrasos e alterações.

---

## 8. Apuração do resultado

### RB51 - Geração de lançamento financeiro
- Todo lançamento financeiro gerado pelo ciclo operacional deve ficar disponível para apuração do resultado.
- O lançamento deve ser rastreável ao processo que o originou.

### RB52 - Classificação do lançamento
- O usuário pode classificar um lançamento financeiro em uma categoria disponível.
- A classificação deve ser armazenada no próprio lançamento.

### RB53 - Receitas por período
- A consulta de receitas deve apresentar os valores conforme o período selecionado.

### RB54 - Despesas por período
- A consulta de despesas deve apresentar os valores conforme o período selecionado.

### RB55 - Apuração de resultado
- Ao solicitar apuração de um período, o sistema deve calcular o resultado conforme os lançamentos do período.
- O cálculo deve considerar receitas, despesas e as classificações financeiras aplicadas.

### RB56 - Demonstração de resultado
- A demonstração de resultado deve apresentar receitas, despesas e resultado conforme as classificações financeiras cadastradas.

### RB57 - Filtro por categoria e período
- O usuário deve poder filtrar o resultado por período e categoria.

### RB58 - Lançamentos pendentes
- Lançamentos sem classificação válida devem ser identificados como pendentes de classificação.

### RB59 - Alteração de classificação
- Usuários autorizados podem alterar a classificação de um lançamento.
- A alteração deve refletir imediatamente no cálculo do resultado.

### RB60 - Histórico da classificação
- Toda alteração na classificação de um lançamento deve ser registrada em histórico, preservando os valores anteriores e novos.

---

## 9. Auditoria e segurança

### RB61 - Registro de operação relevante
- Toda operação relevante executada no sistema deve ser registrada para fins de auditoria.
- A auditoria deve permitir rastrear a operação, o usuário, a data e o registro afetado.

### RB62 - Dados mínimos da auditoria
- Cada registro de auditoria deve conter, no mínimo: usuário, data, operação executada e registro afetado.

### RB63 - Alteração de valor financeiro
- Sempre que um valor financeiro for alterado, o sistema deve registrar o valor anterior e o novo valor.

### RB64 - Consulta de auditoria
- Usuários autorizados podem consultar registros de auditoria.
- A consulta deve permitir filtros por usuário, período e tipo de operação.

### RB65 - Segurança de acesso
- Usuários não autenticados não podem acessar áreas protegidas.
- Usuários sem autorização não podem executar operações proibidas.
- Operações financeiras com alçada superior devem exigir autorização específica.

### RB66 - Proteção de dados sensíveis
- Dados sensíveis, como senhas e informações financeiras, devem ser armazenados e transmitidos de forma segura.
- A senha deve ser armazenada utilizando hash seguro.

---

## 10. Regras gerais de disponibilidade, desempenho e usabilidade

### RB67 - Disponibilidade
- O sistema deve manter a disponibilidade mínima definida para o ambiente em operação.
- Backups devem ser executados conforme a política de backup configurada.

### RB68 - Integridade em falha
- Se ocorrer falha durante operação financeira, o sistema deve preservar a consistência dos dados envolvidos.
- Operações incompletas não podem deixar registros em estado parcial inconsistentes.

### RB69 - Desempenho operacional
- Operações comuns de consulta e cadastro devem responder em até 2 segundos em condições normais.
- Cobranças automáticas devem ser processadas em até 5 minutos após o horário programado.

### RB70 - Interface operacional
- A interface deve apresentar campos, ações e indicadores de forma clara, consistente e objetiva.
- Títulos vencidos, obrigações atrasadas e pendências financeiras devem ser destacados visualmente.

### RB71 - Manutenibilidade e escalabilidade
- Regras configuráveis de cobrança, alçada, obrigação e categorização devem ser aplicadas sem necessidade de alteração manual em registros existentes, salvo quando a regra exigir.
- A evolução do sistema deve permitir inclusão de novos tipos de obrigação, categoria financeira e etapas de cobrança sem impacto funcional crítico.

---

## 11. Conclusão

As regras de negócio acima consolidam o comportamento esperado do RemindMe e orientam o desenvolvimento, a operação, a auditoria e o controle financeiro do sistema. Elas garantem que o produto siga as exigências dos requisitos funcionais e não funcionais, mantendo segurança, rastreabilidade, usabilidade e previsibilidade operacional.
