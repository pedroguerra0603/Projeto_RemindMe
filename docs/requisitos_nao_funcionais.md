Requisitos Não Funcionais - Projeto RemindMe
1. Segurança
RNF01: WHEN um usuário tentar acessar uma funcionalidade protegida sem estar autenticado THE SYSTEM SHALL impedir o acesso.
RNF02: WHEN um usuário tentar executar uma operação sem a permissão necessária THE SYSTEM SHALL impedir a operação.
RNF03: WHEN uma operação financeira exigir uma alçada superior à do usuário THE SYSTEM SHALL impedir sua conclusão até que a autorização necessária seja obtida.
RNF04: WHEN uma senha for armazenada THE SYSTEM SHALL armazená-la utilizando um mecanismo seguro de hash.
RNF05: WHEN dados financeiros ou cadastrais forem transmitidos entre cliente e servidor THE SYSTEM SHALL utilizar comunicação protegida.
RNF06: WHEN uma operação financeira crítica for realizada THE SYSTEM SHALL manter seu registro de auditoria.

2. Disponibilidade e confiabilidade
RNF07: WHILE o sistema estiver em operação THE SYSTEM SHALL permanecer disponível conforme o nível de disponibilidade estabelecido para o serviço.
RNF08: WHEN o horário programado para backup for alcançado THE SYSTEM SHALL executar o backup dos dados conforme a política configurada.
RNF09: IF ocorrer uma falha durante uma operação financeira THE SYSTEM SHALL preservar a consistência dos dados envolvidos.
RNF10: IF uma operação não puder ser concluída integralmente THE SYSTEM SHALL impedir que os dados permaneçam em estado parcialmente processado.

3. Desempenho
RNF11: WHEN um usuário executar uma operação comum de consulta ou cadastro THE SYSTEM SHALL apresentar uma resposta em até 2 segundos, em condições normais de operação.
RNF12: WHEN uma cobrança automática atingir seu horário de execução THE SYSTEM SHALL processá-la em até 5 minutos após o horário programado.
RNF13: WHILE o sistema estiver processando cobranças, notificações ou apurações THE SYSTEM SHALL manter as operações interativas dentro do limite de desempenho estabelecido.

4. Usabilidade
RNF14: WHEN um usuário acessar uma funcionalidade operacional THE SYSTEM SHALL apresentar os campos e ações necessários de forma clara e consistente.
RNF15: WHEN existirem títulos vencidos ou obrigações atrasadas THE SYSTEM SHALL destacá-los visualmente no painel operacional.
RNF16: WHEN um usuário consultar um orçamento, título ou obrigação THE SYSTEM SHALL apresentar seu estado atual de forma explícita.
RNF17: WHEN o usuário acessar o painel principal THE SYSTEM SHALL apresentar as informações operacionais prioritárias, incluindo pendências financeiras, cobranças e obrigações.

5. Manutenibilidade e escalabilidade
RNF18: WHEN um administrador alterar uma regra configurável de cobrança, alçada ou obrigação THE SYSTEM SHALL aplicar a nova configuração sem exigir alteração manual dos registros já existentes, salvo quando especificado pela regra.
RNF19: WHEN uma regra de negócio for executada THE SYSTEM SHALL utilizar a mesma definição da regra em todos os módulos que dependam dela.
RNF20: WHEN um administrador cadastrar um novo tipo de obrigação, categoria financeira ou etapa de cobrança THE SYSTEM SHALL permitir sua utilização conforme as configurações realizadas.
RNF21: WHEN ocorrer um erro durante uma operação do sistema THE SYSTEM SHALL registrar informações suficientes para permitir sua investigação e diagnóstico.
