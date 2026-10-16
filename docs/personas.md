# Personas — RemindMe

Quatro personas, uma por perfil de acesso do sistema. As duas primeiras são as principais: usam o sistema todos os dias e orientam as decisões de prioridade.

Os nomes e as empresas são fictícios.

## Persona 1 — Carla Menezes, a Dona

**Contexto.** 41 anos, dona de uma empresa de manutenção de ar-condicionado com 9 funcionários. Vende a prazo para condomínios e pequenos comércios. Acumula vendas, cobrança e administração. A contabilidade é terceirizada.

**Objetivo.** Receber o que vendeu sem precisar lembrar de cobrar, e saber no fim do mês se a empresa deu resultado.

**Dores.**
- Descobre título vencido semanas depois, quando falta caixa.
- Dá desconto de cabeça e depois não lembra o que combinou.
- Já pagou multa por perder prazo de obrigação.
- Recebe o resultado do contador com meses de atraso.

**Comportamento atual.** Controla recebíveis em uma planilha que só ela entende. Cobra pelo WhatsApp quando lembra. Anota obrigações na agenda do celular.

**Restrições.** Tem poucos minutos por dia para administração. Usa o celular na maior parte do tempo. Não quer aprender um sistema contábil.

**Critérios de sucesso.**
- Só é acionada em exceções: desconto fora de alçada, estorno, obrigação atrasada.
- Vê títulos vencidos e obrigações atrasadas na primeira tela.
- Consulta o resultado do mês sem pedir ao contador.

**Perfil no sistema.** Dono. Casos de uso principais: UC-05, UC-06 (estorno), UC-09, UC-11.

## Persona 2 — Diego Ramos, o Operador Financeiro

**Contexto.** 27 anos, assistente administrativo-financeiro na empresa da Carla. Elabora orçamentos, emite cobranças e registra pagamentos. Trabalha no computador do escritório, em horário comercial.

**Objetivo.** Cumprir a rotina do dia sabendo exatamente o que pode decidir sozinho e o que precisa escalar.

**Dores.**
- Não sabe até onde pode dar desconto e precisa interromper a dona a cada orçamento.
- Refaz a mesma mensagem de cobrança dezenas de vezes.
- Leva a culpa por prazo perdido que ninguém avisou.
- Não tem como provar o que foi combinado com o cliente.

**Comportamento atual.** Mantém a lista de clientes em planilha, copia e cola mensagens de cobrança e guarda comprovantes em pastas no computador.

**Restrições.** Não tem formação contábil. Não pode aprovar desconto acima do limite que lhe foi dado nem estornar pagamento.

**Critérios de sucesso.**
- O sistema informa na hora se o desconto está dentro da sua alçada.
- A cobrança de rotina sai sem ação manual.
- A fila do dia mostra só o que depende dele: tarefas de cobrança, lançamentos a revisar, obrigações aguardando evidência.

**Perfil no sistema.** Operador Financeiro. Casos de uso principais: UC-03, UC-04, UC-06, UC-08, UC-09, UC-10.

## Persona 3 — Sérgio Tavares, o Cliente

**Contexto.** 52 anos, síndico de um condomínio que contrata a empresa da Carla. Aprova orçamentos e autoriza pagamentos, sujeito ao caixa do condomínio.

**Objetivo.** Saber quanto deve e até quando, e conseguir prazo quando o caixa aperta.

**Dores.**
- Recebe cobrança de título que já pagou.
- Não tem um lugar para ver todos os títulos em aberto.
- Negocia prazo por mensagem e depois ninguém lembra do que foi combinado.

**Comportamento atual.** Responde às cobranças pelo WhatsApp e guarda comprovantes no e-mail.

**Restrições.** Não quer instalar aplicativo nem criar conta complicada. Usa o celular.

**Critérios de sucesso.**
- Consulta seus títulos com valor, vencimento e estado.
- Uma promessa de pagamento enviada por mensagem suspende a cobrança automática.
- Recebe respostas claras e padronizadas.

**Perfil no sistema.** Cliente. Casos de uso principais: UC-04 (decisão do orçamento), UC-07.

## Persona 4 — Helena Prado, a Contadora

**Contexto.** 38 anos, contadora em um escritório que atende 40 pequenas empresas, entre elas a da Carla.

**Objetivo.** Receber lançamentos já classificados de forma consistente, para fechar o mês sem reclassificar tudo.

**Dores.**
- Recebe extratos e planilhas sem padrão.
- Não consegue rastrear por que um lançamento foi classificado de certo modo.
- Gasta horas pedindo documentos ao cliente.

**Comportamento atual.** Solicita planilhas por e-mail e reclassifica os lançamentos manualmente no sistema do escritório.

**Restrições.** Não opera a empresa do cliente: só consulta. Precisa de dados exportáveis para o sistema contábil que já usa.

**Critérios de sucesso.**
- Exporta lançamentos e demonstração de resultado em CSV por período.
- Vê quais lançamentos ainda estão pendentes de classificação.
- Consulta o histórico de alterações de uma classificação.

**Perfil no sistema.** Contador, somente leitura (RB-03). Casos de uso principais: UC-11, UC-12, UC-14.

## Tensões entre as personas

| Tensão | Como o sistema arbitra |
|---|---|
| Carla quer receber rápido; Sérgio quer prazo | Renegociação com limites configurados e histórico (RB-28) |
| Diego quer agilidade; Carla quer controle | Alçada de desconto por perfil (RB-15) |
| Carla quer resultado imediato; Helena quer classificação correta | Lançamento sem classificação confirmada fica fora da apuração (RB-12) |
