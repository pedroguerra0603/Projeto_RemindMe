Requisitos Não Funcionais em EARS
Para requisitos não funcionais, o EARS funciona melhor quando transformamos a qualidade desejada em um comportamento observável e verificável.
Segurança
RNF01 — Quando um usuário tentar acessar uma funcionalidade protegida sem estar autenticado, o sistema deverá impedir o acesso.
RNF02 — Quando um usuário tentar executar uma operação sem a permissão necessária, o sistema deverá impedir a operação.
RNF03 — Quando uma operação financeira exigir uma alçada superior à do usuário, o sistema deverá impedir sua conclusão até que a autorização necessária seja obtida.
RNF04 — Sempre que uma senha for armazenada, o sistema deverá armazená-la utilizando um mecanismo seguro de hash.
RNF05 — Sempre que dados financeiros ou cadastrais forem transmitidos entre cliente e servidor, o sistema deverá utilizar comunicação protegida.
RNF06 — Sempre que uma operação financeira crítica for realizada, o sistema deverá manter seu registro de auditoria.
Disponibilidade e confiabilidade
RNF07 — Enquanto o sistema estiver em operação, o sistema deverá permanecer disponível conforme o nível de disponibilidade estabelecido para o serviço.
RNF08 — Sempre que ocorrer o horário programado para backup, o sistema deverá executar o backup dos dados conforme a política configurada.
RNF09 — Se ocorrer uma falha durante uma operação financeira, o sistema deverá preservar a consistência dos dados envolvidos.
RNF10 — Se uma operação não puder ser concluída integralmente, o sistema deverá impedir que os dados permaneçam em estado parcialmente processado.
Desempenho
Aqui é importante colocar valores mensuráveis. Sem isso, "tempo adequado" fica ambíguo.
RNF11 — Quando um usuário executar uma operação comum de consulta ou cadastro, o sistema deverá apresentar uma resposta em até 2 segundos, em condições normais de operação.
RNF12 — Quando uma cobrança automática atingir seu horário de execução, o sistema deverá processá-la em até 5 minutos após o horário programado.
RNF13 — Enquanto o sistema estiver processando cobranças, notificações ou apurações, o sistema deverá manter as operações interativas dentro do limite de desempenho estabelecido.
Usabilidade
RNF14 — Quando um usuário acessar uma funcionalidade operacional, o sistema deverá apresentar os campos e ações necessários de forma clara e consistente.
RNF15 — Quando existirem títulos vencidos ou obrigações atrasadas, o sistema deverá destacá-los visualmente no painel operacional.
RNF16 — Quando um usuário consultar um orçamento, título ou obrigação, o sistema deverá apresentar seu estado atual de forma explícita.
RNF17 — Quando o usuário acessar o painel principal, o sistema deverá apresentar as informações operacionais prioritárias, incluindo pendências financeiras, cobranças e obrigações.
Manutenibilidade e escalabilidade
RNF18 — Quando um administrador alterar uma regra configurável de cobrança, alçada ou obrigação, o sistema deverá aplicar a nova configuração sem exigir alteração manual dos registros já existentes, salvo quando especificado pela regra.
RNF19 — Sempre que uma regra de negócio for executada, o sistema deverá utilizar a mesma definição da regra em todos os módulos que dependam dela.
RNF20 — Quando um administrador cadastrar um novo tipo de obrigação, categoria financeira ou etapa de cobrança, o sistema deverá permitir sua utilização conforme as configurações realizadas.
RNF21 — Sempre que ocorrer um erro durante uma operação do sistema, o sistema deverá registrar informações suficientes para permitir sua investigação e diagnóstico.
