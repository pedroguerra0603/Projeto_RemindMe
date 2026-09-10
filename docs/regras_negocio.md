# Regras de Negócio - Projeto RemindMe

## 1. Regras Ubíquas (Comportamento Universal)
* **RN01:** THE SYSTEM SHALL registrar uma trilha de auditoria contendo o usuário, a data e a ação para cada mudança de estado em um título ou obrigação.
* **RN02:** THE SYSTEM SHALL permitir que apenas o perfil "Dono" reverta a baixa (cancelamento de pagamento) de um título financeiro.
* **RN03:** THE SYSTEM SHALL apresentar os dados financeiros consolidados e lançamentos estritamente em modo de leitura para o perfil "Contador".
* **RN04:** THE SYSTEM SHALL manter um calendário centralizado de obrigações fiscais e contratuais acessível aos perfis "Dono" e "Operador Financeiro".

## 2. Regras Orientadas a Evento (Gatilhos)
* **RN05:** WHEN um orçamento for aprovado dentro da alçada permitida THE SYSTEM SHALL convertê-lo imediatamente em um título financeiro a receber.
* **RN06:** WHEN um título for baixado como pago THE SYSTEM SHALL atualizar a apuração do resultado financeiro em tempo real.
* **RN07:** WHEN o calendário de obrigações atingir 7 dias antes do vencimento de um compromisso THE SYSTEM SHALL solicitar a evidência de cumprimento ao perfil "Operador Financeiro".
* **RN08:** WHEN o modelo de linguagem processar a descrição de um lançamento financeiro THE SYSTEM SHALL avaliar o grau de confiança da conta contábil sugerida contra o plano de contas da empresa.
* **RN09:** WHEN um usuário humano corrigir uma classificação de conta contábil sugerida pela Inteligência Artificial THE SYSTEM SHALL registrar a divergência no banco de dados para auditoria.

## 3. Regras Orientadas a Estado (Condições Contínuas)
* **RN10:** WHILE um título financeiro permanecer no estado "Vencido" THE SYSTEM SHALL executar a sequência automática de lembretes de cobrança para o perfil "Cliente".
* **RN11:** WHILE um título financeiro permanecer no estado "Em Renegociação" THE SYSTEM SHALL suspender temporariamente o envio de lembretes automáticos de cobrança.
* **RN12:** WHILE um lançamento financeiro estiver na fila de revisão humana THE SYSTEM SHALL excluí-lo do cálculo de apuração do resultado financeiro.
* **RN13:** WHILE uma obrigação estiver no estado "Aguardando Evidência" THE SYSTEM SHALL manter o alerta visível no painel do perfil "Operador Financeiro".

## 4. Comportamentos Indesejados (Exceções e Falhas)
* **RN14:** IF a sugestão de classificação da Inteligência Artificial apresentar um grau de confiança abaixo da métrica aceitável THE SYSTEM SHALL encaminhar o lançamento automaticamente para a fila de revisão humana.
* **RN15:** IF o perfil "Operador Financeiro" tentar aplicar um desconto em um orçamento superior à sua alçada permitida THE SYSTEM SHALL bloquear a aprovação e exigir autorização do perfil "Dono".
* **RN16:** IF o prazo de uma obrigação fiscal ou contratual expirar sem a anexação de uma evidência THE SYSTEM SHALL escalar o alerta imediatamente para o perfil "Dono".
* **RN17:** IF o modelo de linguagem não conseguir extrair dados estruturados de intenção da mensagem de um cliente THE SYSTEM SHALL encaminhar a mensagem para tratamento manual.

## 5. Recursos Opcionais (Variações e Integrações)
* **RN18:** WHERE o canal de notificação via WhatsApp estiver ativado THE SYSTEM SHALL disparar as cobranças e os alertas por esse canal em vez de utilizar o simulador padrão.
* **RN19:** WHERE a funcionalidade de integração via planilhas for acionada THE SYSTEM SHALL processar a exportação ou importação de dados estritamente no formato CSV.

## 6. Regras Complexas (Combinações)
* **RN20:** WHILE um título estiver no estado "Vencido" WHEN o sistema extrair uma promessa de pagamento válida da mensagem do cliente THE SYSTEM SHALL alterar o estado do título para "Em Renegociação".