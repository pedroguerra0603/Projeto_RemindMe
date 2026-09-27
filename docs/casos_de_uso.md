# Casos de Uso — RemindMe

## 1. Objetivo

Este documento descreve os casos de uso do RemindMe a partir da visão do produto,
dos requisitos funcionais e não funcionais, das regras de negócio e das personas
do repositório.

O sistema apoia o ciclo operacional de uma pequena empresa: cadastro de clientes,
orçamento, aprovação, geração e cobrança de títulos, renegociação, cumprimento
de obrigações e apuração do resultado. Todas as mudanças relevantes devem ser
rastreáveis e respeitar as permissões e alçadas configuradas.

## 2. Atores

| Ator | Responsabilidade no sistema |
|---|---|
| **Dono** | Trata exceções, aprova operações fora de alçada, acompanha alertas escalonados e configura regras do negócio. |
| **Operador Financeiro** | Executa a rotina de orçamentos, títulos, pagamentos, cobranças e obrigações dentro das alçadas delegadas. |
| **Cliente** | Consulta seus títulos, recebe comunicações, aprova ou rejeita orçamentos e propõe renegociações. |
| **Contador** | Consulta, filtra e exporta dados financeiros consolidados em modo somente leitura. |
| **Administrador** | Configura usuários, perfis, permissões, alçadas, etapas de cobrança, categorias e tipos de obrigação. Pode ser desempenhado pelo Dono, quando esse papel acumular a administração do sistema. |
| **Serviço de notificações** | Canal configurado para envio de orçamentos, lembretes, cobranças e alertas. Pode ser o simulador padrão ou o WhatsApp quando habilitado. |
| **Serviço de IA** | Sugere classificações contábeis e extrai intenções estruturadas de mensagens de renegociação. |
| **Agendador do sistema** | Dispara transições automáticas, cobranças, alertas, escalonamentos e ocorrências recorrentes. |

## 3. Regras gerais aplicáveis

1. O acesso a qualquer caso de uso protegido exige autenticação e permissão
   compatível com o perfil do usuário.
2. Toda operação relevante deve registrar usuário, data, ação e registro
   afetado. Alterações financeiras também registram o valor anterior, o novo
   valor e, quando aplicável, o motivo.
3. Operações que excedam a alçada do usuário ficam pendentes até aprovação
   de um usuário autorizado.
4. O Contador possui acesso somente leitura aos dados consolidados e aos
   lançamentos.
5. O sistema é a autoridade para decidir estados e aprovações. A IA apenas
   extrai ou sugere dados; não aprova operações nem envia texto livre ao cliente.
6. Falhas em operações financeiras não podem deixar dados parcialmente
   processados.

## 4. Visão geral dos casos de uso

| ID | Caso de uso | Atores principais |
|---|---|---|
| UC01 | Autenticar usuário e controlar acesso | Dono, Operador Financeiro, Contador, Administrador |
| UC02 | Administrar usuários, perfis e permissões | Administrador |
| UC03 | Cadastrar e consultar clientes | Operador Financeiro, Dono |
| UC04 | Criar, enviar e decidir orçamento | Operador Financeiro, Dono, Cliente |
| UC05 | Aprovar desconto excepcional | Dono, Operador Financeiro |
| UC06 | Gerenciar títulos e pagamentos | Operador Financeiro, Dono |
| UC07 | Renegociar título | Cliente, Operador Financeiro, Dono |
| UC08 | Executar régua automática de cobrança | Agendador, Serviço de notificações, Operador Financeiro, Cliente |
| UC09 | Gerenciar calendário de obrigações | Operador Financeiro, Dono, Agendador |
| UC10 | Classificar lançamento financeiro | Operador Financeiro, Dono, Serviço de IA |
| UC11 | Apurar resultado e consultar DRE | Dono, Operador Financeiro, Contador |
| UC12 | Consultar auditoria e histórico | Dono, Contador, Administrador |
| UC13 | Configurar regras operacionais e integrações | Administrador, Dono |
| UC14 | Importar e exportar dados em CSV | Administrador, Operador Financeiro, Contador |

## 5. Descrição dos casos de uso

### UC01 — Autenticar usuário e controlar acesso

**Objetivo:** permitir que cada usuário acesse somente as funcionalidades e
operações autorizadas para seu perfil.

**Pré-condições:** usuário cadastrado, ativo e associado a um perfil.

**Fluxo principal:**

1. O usuário informa suas credenciais.
2. O sistema valida as credenciais e a sessão.
3. O sistema identifica o perfil e as permissões do usuário.
4. O sistema apresenta o painel e as funcionalidades permitidas.
5. Ao solicitar uma operação, o sistema verifica a permissão e a alçada
   correspondente.

**Exceções:**

- Credenciais inválidas: o acesso é negado.
- Usuário sem permissão: a operação é impedida e o motivo é informado.
- Operação acima da alçada: a operação é encaminhada para autorização superior.
- Senhas devem ser armazenadas com hash seguro e a comunicação deve ser protegida.

**Requisitos relacionados:** RNF01–RNF06, RF02–RF03.

### UC02 — Administrar usuários, perfis e permissões

**Objetivo:** manter os usuários e as autorizações do sistema.

**Ator principal:** Administrador.

**Fluxo principal:**

1. O Administrador solicita o cadastro ou alteração de um usuário.
2. Informa os dados cadastrais e associa um perfil.
3. O sistema valida os dados e grava o usuário.
4. O Administrador configura as permissões do perfil ou usuário.
5. O sistema aplica as permissões às próximas operações e registra a alteração.

**Exceções:**

- Dados obrigatórios ausentes ou usuário duplicado: o cadastro é rejeitado.
- Tentativa de conceder permissão sem autorização administrativa: a operação é bloqueada.

**Requisitos relacionados:** RF02–RF05, RF61–RF64.

### UC03 — Cadastrar e consultar clientes

**Objetivo:** manter os dados necessários para orçamentos e títulos.

**Atores principais:** Operador Financeiro ou Dono.

**Fluxo principal:**

1. O usuário autorizado informa os dados obrigatórios do cliente.
2. O sistema valida e cadastra o cliente.
3. O usuário consulta clientes e pode filtrar os resultados conforme a
   funcionalidade disponível.
4. O sistema apresenta o histórico de alterações quando solicitado.

**Exceções:**

- Dados inválidos ou incompletos: o sistema solicita correção e não conclui o cadastro.
- Usuário sem permissão: a operação é negada.

**Requisitos relacionados:** RF01, RF04–RF05.

### UC04 — Criar, enviar e decidir orçamento

**Objetivo:** conduzir um orçamento desde a criação até a aprovação, rejeição ou
cancelamento.

**Atores principais:** Operador Financeiro, Dono e Cliente.

**Pré-condições:** cliente cadastrado e usuário autorizado.

**Fluxo principal:**

1. O usuário cria um orçamento associado a um cliente.
2. Inclui itens, quantidades, valores, descontos e condições de pagamento.
3. O sistema calcula e armazena os valores do orçamento.
4. O usuário solicita o envio.
5. O sistema disponibiliza o orçamento ao Cliente pelo canal configurado.
6. O Cliente aprova ou rejeita o orçamento.
7. O sistema registra a decisão e atualiza o estado do orçamento.
8. Quando aprovado dentro das alçadas, o sistema converte o orçamento em um
   título a receber, preservando o vínculo entre os registros.

**Variações e exceções:**

- Desconto acima da alçada: seguir UC05 antes de concluir a aprovação.
- Tentativa de converter orçamento não aprovado: impedir a conversão e informar o motivo.
- Cancelamento autorizado: alterar o estado para cancelado e registrar a operação.
- Falha no envio: informar a falha e manter o orçamento disponível para novo envio,
  sem registrar envio bem-sucedido.

**Requisitos relacionados:** RF06–RF13, RF18–RF19, RN05, RN15.

### UC05 — Aprovar desconto excepcional

**Objetivo:** controlar descontos superiores à alçada do usuário que elaborou o
orçamento.

**Atores principais:** Dono ou usuário com alçada superior.

**Fluxo principal:**

1. O Operador Financeiro informa o desconto no orçamento.
2. O sistema compara o percentual com a alçada do usuário.
3. Se estiver dentro da alçada, o fluxo prossegue normalmente.
4. Se exceder a alçada, o sistema bloqueia a aprovação e solicita autorização.
5. O Dono analisa o orçamento e aprova ou rejeita a exceção.
6. O sistema registra responsável, decisão, data, valores anterior e posterior.

**Exceções:**

- Rejeição: o orçamento permanece pendente de ajuste ou é rejeitado, sem conversão.
- Alçada não configurada: a aprovação excepcional não pode ser concluída até
  que uma alçada válida seja definida.

**Requisitos relacionados:** RF14–RF18, RN03, RN15.

### UC06 — Gerenciar títulos e pagamentos

**Objetivo:** controlar contas a receber, seus estados e respectivos pagamentos.

**Atores principais:** Operador Financeiro e Dono.

**Fluxo principal:**

1. O sistema cria o título a partir de um orçamento aprovado ou o usuário
   autorizado cadastra o título manualmente.
2. O sistema armazena valor, vencimento, cliente, origem, condição e estado.
3. O usuário consulta e filtra títulos por cliente, vencimento, estado e período.
4. O sistema identifica títulos próximos do vencimento e títulos vencidos.
5. O usuário registra um pagamento associado ao título.
6. Para pagamento parcial, o sistema atualiza o saldo restante.
7. Para pagamento integral, o sistema baixa o título como pago e interrompe
   cobranças automáticas pendentes.
8. O sistema registra a operação e atualiza a apuração do resultado.

**Variações e exceções:**

- Dados do pagamento inválidos ou título inexistente: rejeitar o registro.
- Estorno de baixa: somente o Dono pode reverter a baixa; o motivo é obrigatório.
- Falha durante a operação: preservar a consistência do título e do pagamento,
  sem estado parcialmente processado.

**Requisitos relacionados:** RF19–RF27, RF30–RF31, RF37, RN01–RN02, RN06.

### UC07 — Renegociar título

**Objetivo:** registrar uma nova condição de pagamento para um título, mantendo
o histórico e o vínculo com o título original.

**Atores principais:** Cliente e Operador Financeiro.

**Fluxo principal:**

1. O Cliente consulta seus títulos e seleciona um título elegível.
2. O Cliente envia uma proposta com valor e data prometida.
3. O sistema ou o Serviço de IA extrai o título, valor e data da mensagem.
4. O sistema valida os dados estruturados contra as regras de renegociação.
5. Se aprovada, a proposta atualiza as condições e altera o título para
   **Em Renegociação**.
6. O sistema registra as condições anteriores, posteriores, responsável e data.
7. Enquanto o título estiver em renegociação, os lembretes automáticos ficam suspensos.

**Variações e exceções:**

- Proposta fora das regras: rejeitar ou encaminhar ao Operador Financeiro para análise.
- IA sem confiança suficiente ou sem dados estruturados: encaminhar a mensagem
  para tratamento manual.
- Mensagem de cliente sem promessa válida: não alterar o estado do título.

**Requisitos relacionados:** RF28–RF29, RN10–RN11, RN17, RN20.

### UC08 — Executar régua automática de cobrança

**Objetivo:** enviar lembretes e cobranças nas etapas configuradas para cada título.

**Atores principais:** Agendador do sistema e Serviço de notificações.

**Fluxo principal:**

1. O Agendador verifica títulos próximos do vencimento ou vencidos.
2. Identifica a etapa da régua aplicável conforme prazo e estado do título.
3. O sistema seleciona a mensagem e a ação configuradas.
4. O Serviço de notificações envia a comunicação ao Cliente.
5. O sistema registra data, etapa e resultado do envio.
6. Quando uma etapa exigir intervenção manual, o sistema encaminha a tarefa ao
   responsável configurado.

**Variações e exceções:**

- Título pago: interromper cobranças pendentes.
- Título em renegociação: suspender temporariamente as cobranças.
- Falha no canal: registrar o resultado e encaminhar para tratamento conforme
  a configuração da etapa.
- WhatsApp habilitado: utilizar esse canal no lugar do simulador padrão.

**Requisitos relacionados:** RF32–RF39, RN10–RN11, RN18, RNF12–RNF13.

### UC09 — Gerenciar calendário de obrigações

**Objetivo:** controlar obrigações fiscais e contratuais, seus prazos, evidências
e escalonamentos.

**Atores principais:** Operador Financeiro e Dono; Agendador como ator de suporte.

**Fluxo principal:**

1. O usuário autorizado cadastra o tipo, periodicidade, prazo e responsável.
2. O sistema apresenta a obrigação no calendário centralizado.
3. No período de aviso configurado, o Agendador alerta o responsável.
4. O responsável registra o cumprimento e anexa a evidência quando exigida.
5. O sistema altera o estado para cumprida e registra data, usuário e evidência.
6. Para obrigação recorrente, o sistema gera a próxima ocorrência.
7. Se o prazo expirar sem cumprimento, o sistema marca a obrigação como atrasada.
8. Após o período configurado em atraso, o sistema escala o alerta ao Dono.

**Variações e exceções:**

- Evidência obrigatória ausente: manter o estado **Aguardando Evidência** e o
  alerta visível no painel do Operador Financeiro.
- Obrigação atrasada: não permitir que seja tratada como cumprida sem os dados
  exigidos e registrar o atraso.

**Requisitos relacionados:** RF40–RF50, RN04, RN07, RN13, RN16.

### UC10 — Classificar lançamento financeiro

**Objetivo:** atribuir uma categoria contábil aos lançamentos e controlar
classificações sugeridas pela IA.

**Atores principais:** Operador Financeiro ou Dono; Serviço de IA como suporte.

**Fluxo principal:**

1. Um lançamento é gerado pelo ciclo operacional.
2. O Serviço de IA analisa a descrição e sugere uma conta do plano de contas,
   com grau de confiança.
3. O sistema compara a sugestão com a métrica configurada.
4. Para confiança alta, o sistema aceita a classificação conforme a regra.
5. Para confiança baixa, o sistema coloca o lançamento na fila de revisão humana.
6. O usuário autorizado confirma ou corrige a classificação.
7. O sistema registra a classificação, a divergência e o histórico da alteração.
8. Lançamentos sem classificação válida ficam fora do cálculo do resultado até
   serem regularizados.

**Variações e exceções:**

- IA indisponível ou incapaz de extrair uma classificação: encaminhar para revisão humana.
- Correção humana: registrar a sugestão original, a classificação final e o usuário.
- Usuário sem permissão: impedir alteração.

**Requisitos relacionados:** RF51–RF52, RF58–RF60, RN08–RN09, RN12, RN14.

### UC11 — Apurar resultado e consultar DRE

**Objetivo:** disponibilizar receitas, despesas e resultado financeiro com base nos
lançamentos válidos do período.

**Atores principais:** Dono, Operador Financeiro e Contador.

**Fluxo principal:**

1. O usuário seleciona período e, opcionalmente, categorias.
2. O sistema considera os lançamentos classificados e elegíveis.
3. O sistema calcula receitas, despesas e resultado.
4. O sistema apresenta a DRE e permite filtrar os dados.
5. O Contador consulta os dados consolidados e pode exportá-los, sem alterar
   lançamentos ou classificações.
6. A baixa de um título atualiza a apuração em tempo real.

**Variações e exceções:**

- Lançamento pendente de classificação: excluir do cálculo e indicar a pendência.
- Tentativa do Contador de alterar dados: impedir a operação por acesso somente leitura.

**Requisitos relacionados:** RF53–RF57, RN03, RN06, RN12.

### UC12 — Consultar auditoria e histórico

**Objetivo:** fornecer rastreabilidade das operações e alterações realizadas.

**Atores principais:** Dono, Contador e Administrador.

**Fluxo principal:**

1. O usuário autorizado informa filtros por usuário, período e tipo de operação.
2. O sistema retorna os registros de auditoria.
3. Cada registro apresenta, no mínimo, usuário, data, operação e registro afetado.
4. Para alterações financeiras, o sistema apresenta valores anterior e posterior
   e o motivo, quando informado.
5. O sistema permite consultar o histórico de um orçamento, título, obrigação,
   lançamento ou renegociação.

**Exceções:**

- Usuário sem permissão de auditoria: impedir a consulta.
- Registro inexistente: informar que não há histórico para os filtros utilizados.

**Requisitos relacionados:** RF04–RF05, RF29, RF31, RF47, RF50, RF60–RF64,
RN01, RN06 e RN09.

### UC13 — Configurar regras operacionais e integrações

**Objetivo:** permitir que o Administrador ou Dono configure as regras variáveis
do processo sem alterar registros históricos.

**Fluxo principal:**

1. O usuário autorizado seleciona a regra a configurar.
2. Define alçadas, etapas e mensagens de cobrança, tipos e periodicidades de
   obrigações, categorias financeiras ou limiar de confiança da IA.
3. Configura o canal de notificações e, quando necessário, habilita o WhatsApp.
4. O sistema valida a configuração, registra a alteração e a torna disponível
   para novos processamentos.
5. O sistema mantém a definição única da regra para todos os módulos dependentes.

**Exceções:**

- Configuração inválida ou incompleta: não publicar a alteração.
- Alteração que exigiria reprocessar registros existentes: solicitar decisão
  explícita conforme a regra aplicável.

**Requisitos relacionados:** RF03, RF14, RF32, RF36, RF40–RF41, RN18–RN19,
RNF18–RNF20.

### UC14 — Importar e exportar dados em CSV

**Objetivo:** permitir interoperabilidade padronizada com planilhas sem depender
de integrações externas no MVP.

**Atores principais:** Administrador, Operador Financeiro e Contador.

**Fluxo principal:**

1. O usuário autorizado seleciona o tipo de dado e um arquivo CSV.
2. O sistema valida formato, colunas obrigatórias e valores.
3. O sistema apresenta os registros válidos e os erros encontrados.
4. Após confirmação, o sistema importa os dados ou gera o arquivo de exportação.
5. Operações que alterem registros são registradas na auditoria.

**Exceções:**

- Formato diferente de CSV ou colunas inválidas: rejeitar o arquivo e informar os erros.
- Registros inconsistentes: não concluir uma importação parcialmente; informar
  os registros que precisam de correção.
- Contador: permitir exportação e consulta, mas não alteração por importação.

**Requisitos relacionados:** RN19, RNF09–RNF10, RNF20–RNF21.

## 6. Matriz de cobertura dos requisitos funcionais

| Requisitos | Casos de uso |
|---|---|
| RF01–RF05 | UC01, UC02, UC03, UC12 |
| RF06–RF13 | UC04 |
| RF14–RF18 | UC05 |
| RF19–RF31 | UC04, UC06, UC07, UC12 |
| RF32–RF39 | UC08, UC13 |
| RF40–RF50 | UC09, UC12 |
| RF51–RF60 | UC10, UC11, UC12 |
| RF61–RF64 | UC01, UC02, UC12 |

## 7. Limites do escopo

Os casos de uso não incluem emissão de Nota Fiscal Eletrônica, integração direta
com a SEFAZ, folha de pagamento, RH ou aconselhamento financeiro. O sistema
registra obrigações e evidências relacionadas, mas não executa a emissão fiscal.
Os canais externos de mensageria são substituíveis e podem permanecer simulados
no MVP; a integração com planilhas utiliza exclusivamente CSV.
