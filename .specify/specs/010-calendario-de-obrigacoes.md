# Spec 010 — Calendário de obrigações

## 1. Identificação

| | |
|---|---|
| **ID** | 010 |
| **Nome** | Calendário de obrigações |
| **Objetivo** | Reunir num calendário único as obrigações fiscais, trabalhistas e contratuais da empresa, avisar o responsável antes do prazo, exigir a evidência de cumprimento quando for o caso, marcar o atraso e escalar o alerta ao Dono. |
| **Valor entregue** | A Dona deixa de anotar obrigações na agenda do celular e de pagar multa por prazo perdido ([personas](../../docs/personas.md)). O Operador Financeiro sabe o que vence e o que falta comprovar. Nenhuma obrigação estoura em silêncio: toda obrigação Atrasada chega ao Dono ([visão](../../docs/visao.md)). |
| **Situação** | **Verificada** — implementada e verificada em 2026-11-20; todos os critérios de aceite passaram (seção 8). |
| **Aprovada por** | Renan Gandolpho, em 2026-11-20 |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-40 a RF-50, RF-77 |
| RB | RB-04, RB-07, RB-13, RB-16, RB-29; preserva RB-01, RB-03, RB-18 e RB-27 (o texto dos alertas vem só do modelo) |
| RNF | RNF-02, RNF-03, RNF-09, RNF-14, RNF-15, RNF-23 |
| UC | [UC-09](../../docs/casos-de-uso/UC-09-gerenciar-obrigacoes.md) (fluxo principal, A1 a A3, E1 a E3) |
| Entidades | `Obrigacao`, `Evidencia`; `Usuario` (responsável); a mensagem do canal simulado, que não é classe do domínio |
| Drivers e ADRs | DA-01, DA-02, DA-03, DA-04, DA-05, DA-07; ADR-001, ADR-002, ADR-004, ADR-007 |
| Depende de | Specs 001, 002, 005 (canal simulado e caixa de saída), 017 e 018 (padrão do agendador). Questões OPEN-13 e OPEN-48 (agendador), OPEN-53 (Administrador), OPEN-62 (só o canal simulado), e OPEN-68 a OPEN-71, decididas nesta spec. |

## 3. Escopo

### Incluído

- Cadastro da obrigação com nome, tipo, periodicidade, prazo, responsável e se exige evidência (RF-40). Tipo de uma lista fixa; periodicidade de uma lista fixa (OPEN-70, OPEN-71).
- Calendário único da empresa, com as obrigações ordenadas por prazo, para Dono e Operador Financeiro (RF-43, RB-04); o Administrador pela OPEN-53.
- Alteração do prazo e do responsável, registrada no histórico da obrigação (RF-41).
- Aviso ao responsável pela antecedência padrão de 7 dias, uma vez por ocorrência, pelo agendador (RF-44, RB-07, OPEN-71).
- Registro do cumprimento, com anexo de evidência: arquivo PDF, PNG ou JPG de até 5 MB, com descrição obrigatória (RF-45 a RF-47, RB-29, OPEN-68).
- Estado Aguardando Evidência quando o cumprimento é registrado sem a evidência exigida, com o alerta visível no painel do Operador Financeiro até o anexo (RF-46, RF-77, RB-13).
- Download da evidência anexada, só para quem pode gerenciar obrigações.
- Geração da próxima ocorrência quando a obrigação recorrente é Cumprida (RF-42, OPEN-70).
- Marcação de Atrasada pelo agendador, a partir do dia seguinte ao prazo (RF-48).
- Alerta escalonado a cada Dono ativo quando a obrigação permanece Atrasada pela tolerância padrão de 0 dias, uma vez por ocorrência (RF-49, RB-16, OPEN-71).
- Histórico da obrigação: ocorrências da mesma série, avisos, atrasos, escalonamentos, alterações, cumprimento e evidências (RF-50).
- Alertas pelo canal de notificação, com o texto montado só pelos modelos de mensagem, gravados na caixa de saída da Spec 005 (ADR-002, RB-18, RB-27, OPEN-62). A mensagem passa a aceitar um usuário como destinatário, além do cliente.
- Painel: destaque das obrigações Atrasadas (RNF-15) e quadro "Obrigações aguardando evidência" para o Operador Financeiro (RF-77); próximas obrigações dos 15 dias seguintes ao lado dos títulos e das contas.
- Interface web: calendário, cadastro, página da obrigação, alteração, cumprimento com upload e download da evidência.
- Dados de demonstração com obrigações em todos os estados e as mensagens correspondentes.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Configurar a antecedência por tipo e a tolerância (RB-07, RB-16) | Spec 014; até lá, 7 e 0 dias (OPEN-71) |
| Painel por perfil completo | Spec 016; aqui só os destaques que RNF-15 e RF-77 exigem |
| Canal de notificação real | Fora do projeto (OPEN-62) |
| Ajuste do prazo para dia útil (fim de semana, feriado) | Fora do MVP: exigiria calendário de feriados (OPEN-70) |
| Alterar nome, tipo, periodicidade ou exigência de evidência depois do cadastro | Nenhum RF prevê; o RF-41 trata só de prazo e responsável |
| Cancelar ou excluir obrigação | O diagrama de estados não prevê; a obrigação termina Cumprida |
| Gerar as ocorrências intermediárias de uma série atrasada | A próxima ocorrência só nasce no cumprimento (RF-42, OPEN-70) |
| Excluir ou substituir evidência anexada | Evidência é comprovação: depois de anexada, fica |

## 4. Comportamento

### Pré-condições

- O usuário está autenticado com um perfil que tem "Gerenciar obrigações" (Dono e Operador Financeiro, na matriz inicial; o Administrador pela OPEN-53). O Contador não vê o calendário (RB-04).
- O responsável é um usuário ativo com perfil Dono ou Operador Financeiro (OPEN-69).

### Dados da obrigação

| Dado | Regra |
|---|---|
| Nome | Texto livre, obrigatório, até 120 caracteres ("DAS", "Aluguel da loja"). |
| Tipo | Fiscal, Trabalhista, Contratual ou Outra (OPEN-71). |
| Periodicidade | Única, Mensal, Trimestral, Semestral ou Anual (OPEN-70). |
| Prazo | Data obrigatória. Pode estar no passado (obrigação já atrasada que se quer registrar). |
| Responsável | Usuário ativo, Dono ou Operador Financeiro (OPEN-69). |
| Exige evidência | Sim ou não. |
| Dia-base | O dia do prazo da primeira ocorrência, guardado para a recorrência (OPEN-70). |
| Prazo de referência | O prazo calculado pela periodicidade, de onde sai a próxima ocorrência. Nasce igual ao prazo e não muda quando o prazo é alterado (OPEN-70). |
| Série | Identificador comum a todas as ocorrências geradas a partir do mesmo cadastro. |

### Fluxo principal

1. O Operador Financeiro cadastra a obrigação. Ela nasce Pendente e aparece no calendário (RF-40, RF-43). O cadastro entra no histórico.
2. Quando faltam 7 dias ou menos para o prazo, o agendador avisa o responsável pelo canal de notificação, uma única vez por ocorrência (RF-44, RB-07). O aviso entra no histórico e na caixa de saída.
3. O Operador registra o cumprimento, com a data em que cumpriu, e anexa a evidência: arquivo e descrição (RF-45, RF-46).
4. A obrigação passa a Cumprida, com a data, o usuário que registrou e a evidência (RF-47). Qualquer usuário com "Gerenciar obrigações" registra; não precisa ser o responsável (OPEN-69).
5. Se a obrigação é recorrente, na mesma operação nasce a próxima ocorrência, Pendente, na mesma série, com o prazo calculado pela periodicidade (RF-42).

### Recorrência

- O próximo prazo é o prazo de referência da ocorrência anterior avançado 1, 3, 6 ou 12 meses, no dia-base. Quando o dia-base não existe no mês, vale o último dia do mês: 31/01 → 28/02 → 31/03 (OPEN-70).
- O prazo novo conta do prazo de referência anterior, e não da data do cumprimento nem do prazo alterado: o DAS de fevereiro pago com atraso, ou prorrogado, não muda o prazo do DAS de março.
- A ocorrência nova copia nome, tipo, periodicidade, responsável, exigência de evidência, dia-base e série. Nasce sem evidência e sem histórico próprio, além do registro "gerada a partir de".
- Se o prazo novo já passou, ela é marcada Atrasada na mesma operação.
- Periodicidade Única não gera ocorrência.

### Avisos e escalonamento (agendador)

- A verificação roda na inicialização e a cada hora (OPEN-48), pelo mesmo `AgendadorDeVencimentos` dos títulos e das contas a pagar (OPEN-13). Ela é idempotente.
- **Atraso:** obrigação Pendente ou Aguardando Evidência com prazo anterior a hoje passa a Atrasada (RF-48). No próprio dia do prazo ainda está em dia.
- **Aviso:** obrigação não Cumprida, com prazo entre hoje e hoje + 7 dias, sem aviso enviado para o prazo atual, gera um aviso ao responsável (RF-44). Se o responsável estiver inativo, o aviso vai a cada Dono ativo (OPEN-69).
- **Escalonamento:** obrigação Atrasada há pelo menos a tolerância (0 dias), sem escalonamento enviado para o prazo atual, gera um alerta a cada Dono ativo (RF-49, RB-16). Com tolerância 0, isso acontece na mesma rodada que a marca Atrasada. O responsável não recebe o escalonamento.
- O contato do usuário é o e-mail dele. Cada alerta vira uma mensagem na caixa de saída, com o usuário como destinatário e a origem `obrigacao <id>`.
- Se o canal falhar, a mensagem fica com o resultado "falhou", o histórico registra a falha, e o alerta é tentado de novo na rodada seguinte.
- Os valores 7 e 0 ficam num único ponto do domínio, para a Spec 014 os trocar por configuração.
- Só o agendador envia alertas; os casos de uso do usuário não chamam o canal. Obrigação cadastrada ou gerada já Atrasada é marcada na mesma operação e escalada na rodada seguinte do agendador, em até uma hora.
- O controle de envio é por destinatário: cada par (prazo da ocorrência, usuário) recebe no máximo um aviso e um escalonamento entregues. Se o canal falhar para um Dono e entregar para outro, a nova tentativa vai só para quem falhou.
- Obrigação com o cumprimento já registrado (Aguardando Evidência, ou Atrasada à espera da evidência) não recebe aviso de prazo: o que falta é a evidência, e ela já está no quadro do painel. A Atrasada continua sendo escalada ao Dono (RB-16).
- Não há teto de tentativas: com o canal simulado, a falha só ocorre quando injetada nos testes.

### Evidência

- Arquivo PDF, PNG ou JPG, de 1 byte a 5 MB, conferido pelo conteúdo (assinatura do arquivo), e não só pela extensão. Descrição obrigatória, até 200 caracteres (OPEN-68).
- Guarda o nome original do arquivo, o tipo, o tamanho, a descrição, a data e hora do anexo e quem anexou.
- O conteúdo fica no banco da aplicação, na mesma transação do cumprimento (RNF-09). Nada é gravado dentro do repositório.
- O download só é servido a quem tem "Gerenciar obrigações", como anexo para baixar, com o tipo conferido no anexo.
- Uma obrigação pode ter várias evidências (composição, modelo de domínio). Obrigação que não exige evidência aceita anexo opcional.

### Fluxos alternativos

- **A1 — Obrigação sem exigência de evidência.** No passo 3, o cumprimento é registrado sem anexo, e a obrigação passa a Cumprida (UC-09, A1).
- **A2 — Cumprimento sem a evidência exigida.** No passo 3, o cumprimento é registrado sem anexo. A obrigação passa a Aguardando Evidência, com a data e o usuário do cumprimento, e aparece no quadro "Obrigações aguardando evidência" do painel do Operador Financeiro (RF-46, RF-77, RB-13). Quando a evidência é anexada, passa a Cumprida, e a próxima ocorrência nasce nesse momento.
- **A3 — Alteração de prazo ou responsável.** Um usuário autorizado altera o prazo ou o responsável. O histórico guarda o valor anterior e o novo (RF-41). O prazo só muda em Pendente ou Aguardando Evidência, e o novo prazo não pode ser anterior a hoje; um prazo estourado não se apaga. O responsável muda em qualquer estado diferente de Cumprida. Mudar o prazo libera um novo aviso para o prazo novo. A alteração vale só para esta ocorrência: o prazo de referência e o dia-base não mudam, e a próxima volta ao ritmo da série (OPEN-70).
- **A4 — Cumprimento de obrigação Atrasada.** A obrigação Atrasada passa a Cumprida com o cumprimento completo: com evidência, quando exigida. Se o cumprimento é registrado sem a evidência exigida, ela continua Atrasada, com o cumprimento registrado, até o anexo; não volta a Aguardando Evidência.
- **A5 — Aguardando Evidência que estoura o prazo.** O prazo passa enquanto a evidência não chega: a obrigação passa a Atrasada, mantendo a data e o usuário do cumprimento, e o anexo da evidência a leva a Cumprida. Ela continua no quadro "Obrigações aguardando evidência", que mostra toda obrigação com cumprimento registrado e sem a evidência exigida, Aguardando Evidência ou Atrasada (RB-13).
- **A6 — Responsável inativo.** A obrigação continua no calendário, com o aviso "responsável inativo", e os avisos vão aos Donos ativos (OPEN-69).
- **A7 — Cadastro com prazo passado.** A obrigação nasce Pendente e é marcada Atrasada na mesma operação.

### Exceções

- **E1 — Dados obrigatórios ausentes ou inválidos.** Nome vazio ou longo demais, tipo ou periodicidade fora da lista, prazo ausente ou inválido, responsável ausente, inativo ou de outro perfil: o cadastro é recusado, com o motivo em cada campo (UC-09, E3; RNF-14).
- **E2 — Evidência inválida.** Arquivo vazio, maior que 5 MB, de tipo não aceito ou com conteúdo que não corresponde a PDF, PNG ou JPG; descrição vazia ou longa demais: recusado no campo, e nada muda.
- **E3 — Operação fora do estado.** Registrar cumprimento ou anexar evidência em obrigação Cumprida; alterar o prazo de Atrasada ou Cumprida; alterar o responsável de Cumprida: recusado, com o estado atual.
- **E4 — Data do cumprimento inválida.** Ausente ou posterior a hoje: recusada no campo data.
- **E5 — Falha na gravação.** Se a gravação da obrigação, da evidência, da próxima ocorrência, do histórico ou da auditoria falhar, nada fica gravado e a obrigação continua como estava (RNF-09).
- **E6 — Perfil sem permissão.** O Contador não consulta o calendário, não cadastra, não altera, não registra cumprimento e não baixa evidência (RB-03, RB-04), nem chamando o serviço direto (RNF-03).

Toda recusa informa o motivo e não altera nenhum dado. A exceção é a falha do canal, que guarda a mensagem que falhou, como manda o ADR-002.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Uma obrigação está em exatamente um estado: Pendente, Aguardando Evidência, Atrasada ou Cumprida. Cumprida é final. | Estados |
| INV-2 | Obrigação que exige evidência só fica Cumprida com ao menos uma evidência anexada. | RB-29 |
| INV-3 | Obrigação Cumprida tem data e usuário do cumprimento. | RF-47 |
| INV-4 | Numa série, há no máximo uma ocorrência não Cumprida, e cada ocorrência gera no máximo uma próxima. | RF-42 |
| INV-5 | Cada prazo de cada ocorrência gera no máximo um aviso e no máximo um escalonamento entregues. | RB-07, RB-16 |
| INV-6 | O texto dos alertas vem só dos modelos de mensagem. | RB-27 |
| INV-7 | O domínio não conhece o canal nem o banco; quem chama o canal é a camada de aplicação. | ADR-001, ADR-002 |
| INV-8 | Toda mudança de estado, alteração, cumprimento e evidência é auditada e entra no histórico da obrigação. | RB-01, RF-41, RF-50 |
| INV-9 | As regras de antecedência (7 dias) e tolerância (0 dias) estão num único ponto do domínio. | RB-07, RB-16, Spec 014 |

## 6. Critérios de aceitação

Datas dos exemplos com hoje = 20/11/2026.

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Operador autenticado | ele cadastra "DAS", Fiscal, Mensal, prazo 20/12/2026, responsável ele mesmo, exige evidência | a obrigação existe Pendente, com os dados informados e dia-base 20; o cadastro está no histórico e na auditoria | RF-40, RB-01 |
| CA-02 | um Operador autenticado | ele cadastra sem nome, com tipo "Imposto", com periodicidade "Semanal", sem prazo e com responsável Contador ou inativo | cada tentativa é recusada no campo certo, e nada é gravado | E1, RNF-14, OPEN-69 |
| CA-03 | obrigações com prazos 05/12, 25/11 e 01/01/2027 | o Dono abre o calendário | elas aparecem na ordem 25/11, 05/12, 01/01/2027 | RF-43, RB-04 |
| CA-04 | uma obrigação Pendente com prazo 27/11/2026 | o agendador roda duas vezes | o responsável tem um único aviso na caixa de saída, com o texto do modelo, e o histórico tem um único "aviso enviado" | RF-44, RB-07, INV-5, INV-6 |
| CA-05 | uma obrigação Pendente com prazo 28/11/2026 | o agendador roda | nenhum aviso é enviado | RB-07 |
| CA-06 | uma obrigação que não exige evidência | o Operador registra o cumprimento com a data de hoje | ela fica Cumprida, com a data e o usuário; o histórico e a auditoria registram | RF-45, RF-47, A1 |
| CA-07 | uma obrigação que exige evidência | o Operador registra o cumprimento com um PDF e uma descrição | ela fica Cumprida, com a evidência ligada a ela, e o PDF baixado é idêntico ao enviado | RF-46, RF-47, RB-29 |
| CA-08 | uma obrigação que exige evidência | o Operador registra o cumprimento sem anexo | ela fica Aguardando Evidência e aparece no quadro "Obrigações aguardando evidência" do painel do Operador; depois do anexo, fica Cumprida e sai do quadro | A2, RF-77, RB-13, RB-29 |
| CA-09 | uma obrigação que exige evidência | o anexo é vazio, tem 5 MB + 1 byte, é um .txt, é um texto renomeado para .pdf, ou vem sem descrição | as cinco tentativas são recusadas no campo, e a obrigação continua no estado anterior | E2, OPEN-68 |
| CA-10 | uma obrigação Mensal com prazo 31/01/2027 | ela é Cumprida, e as próximas também | as ocorrências nascem Pendentes, na mesma série, com prazos 28/02/2027 e 31/03/2027 | RF-42, OPEN-70 |
| CA-11 | uma obrigação Mensal com prazo 20/10/2026, Atrasada | ela é Cumprida em 20/11/2026 | a próxima nasce com prazo 20/11/2026, Pendente (o prazo conta do anterior); uma Única não gera próxima | RF-42, OPEN-70 |
| CA-12 | uma obrigação Pendente com prazo 19/11/2026 e outra com prazo 20/11/2026 | o agendador roda | a primeira fica Atrasada e a segunda continua Pendente | RF-48, E1 do UC-09 |
| CA-13 | uma obrigação Aguardando Evidência com prazo 19/11/2026 | o agendador roda e depois a evidência é anexada | ela fica Atrasada, mantendo o cumprimento registrado, e com o anexo fica Cumprida | A5, RF-48 |
| CA-14 | uma obrigação que fica Atrasada nesta rodada e dois Donos ativos, um inativo | o agendador roda duas vezes | cada Dono ativo tem um único alerta escalonado; o Dono inativo e o responsável Operador não recebem; o histórico tem um "escalonada ao Dono" | RF-49, RB-16, INV-5 |
| CA-15 | uma obrigação cujo responsável foi inativado, com prazo em 3 dias | o agendador roda | o aviso vai aos Donos ativos, e o calendário mostra "responsável inativo" | A6, OPEN-69 |
| CA-16 | uma obrigação Pendente | o Operador altera o prazo para 10/12/2026 e o responsável para o Dono | o histórico mostra o prazo e o responsável anteriores e os novos; a auditoria também | RF-41, A3 |
| CA-17 | obrigações Atrasada e Cumprida | o prazo da Atrasada é alterado; o prazo, o responsável, o cumprimento e o anexo da Cumprida são tentados; o prazo de uma Pendente é alterado para ontem | todas as tentativas são recusadas com o motivo, e nada muda | E3, A3 |
| CA-18 | uma obrigação com cadastro, aviso, alteração, atraso, escalonamento e cumprimento, e a próxima ocorrência | o usuário abre a obrigação | ela mostra o histórico em ordem, com os eventos, as evidências e as outras ocorrências da série | RF-50 |
| CA-19 | uma obrigação Pendente | o cumprimento é registrado com data de amanhã | a tentativa é recusada no campo data | E4 |
| CA-20 | uma falha injetada ao gravar a auditoria do cumprimento de uma obrigação recorrente com evidência | o Operador registra o cumprimento | a obrigação continua Pendente, sem evidência, e a próxima ocorrência não existe | E5, RNF-09 |
| CA-21 | um Contador autenticado | ele tenta abrir o calendário, cadastrar, alterar, registrar cumprimento e baixar uma evidência, pela tela e pelo serviço | todas as operações são negadas, e nada muda | E6, RB-03, RB-04, RNF-03 |
| CA-22 | obrigações Atrasadas | o Dono e o Operador abrem o painel | as Atrasadas aparecem em destaque | RNF-15 |
| CA-23 | um canal que falha | o agendador tenta avisar e depois roda de novo com o canal funcionando | a primeira mensagem fica "falhou", e a segunda rodada entrega o aviso; há um único aviso entregue | ADR-002, INV-5 |
| CA-24 | uma obrigação Mensal com prazo 20/12/2026, alterado para 05/01/2027 | ela é Cumprida | a próxima nasce com prazo 20/01/2027, e não 05/02/2027 | A3, RF-42, OPEN-70 |

Os testes levam no nome o critério ou a regra, como `test_CA_10_RF_42_...` e `test_RB_29_...`.

## 7. Questões em aberto

| ID | Questão | Situação |
|---|---|---|
| OPEN-68 | Como a evidência é guardada? | Decidida em 2026-11-20 por Renan Gandolpho: arquivo PDF, PNG ou JPG de até 5 MB, conferido pelo conteúdo, com descrição obrigatória. |
| OPEN-69 | Quem pode ser responsável, e quem registra o cumprimento? | Decidida em 2026-11-20 por Renan Gandolpho: responsável é um usuário ativo Dono ou Operador Financeiro; qualquer usuário com "Gerenciar obrigações" registra o cumprimento; com responsável inativo, a obrigação é sinalizada e os avisos vão aos Donos. |
| OPEN-70 | Quais periodicidades, e como se calcula o próximo prazo? | Decidida em 2026-11-20 por Renan Gandolpho: Única, Mensal, Trimestral, Semestral e Anual; mesmo dia-base, ou o último dia do mês; conta do prazo de referência anterior; alteração de prazo vale só para a ocorrência; a próxima nasce no cumprimento; sem ajuste para dia útil. |
| OPEN-71 | O que é o tipo, e quais os valores de aviso e escalonamento até a Spec 014? | Decidida em 2026-11-20 por Renan Gandolpho: tipo de lista fixa (Fiscal, Trabalhista, Contratual, Outra) e nome livre; aviso com 7 dias, uma vez; Atrasada no dia seguinte ao prazo; escalonamento com tolerância 0, uma vez, só aos Donos ativos. |

Nenhuma bloqueia a implementação.

### Alterações na baseline, no mesmo PR

- `docs/modelo-dominio.md` e `docs/uml/dominio-v2.mmd` (e o `.png`): `Obrigacao` ganha `nome`, `diaBase`, `prazoReferencia`, `serie`, `cumpridaEm` e as operações `alterarPrazo()`, `alterarResponsavel()`, `anexarEvidencia()`, `marcarAtrasada()`; `Evidencia` ganha `nomeArquivo`, `tipoArquivo` e `tamanho`; linha nova no histórico.
- `docs/glossario.md`: "Tipo de obrigação", "Periodicidade", "Ocorrência", "Aviso de obrigação" e "Responsável".
- `docs/uml/estados.md`: cláusulas de A4 e A5 (Atrasada com cumprimento registrado só passa a Cumprida com a evidência) e do prazo que não muda em Atrasada. As transições do diagrama não mudam.
- `docs/casos-de-uso/UC-09-gerenciar-obrigacoes.md`: passo 4 e A2 sem exigir que seja o responsável (OPEN-69).
- `docs/requisitos.md`: em RF-45 e RF-46, "o responsável registrar" passa a "um usuário autorizado registrar" (OPEN-69); RB-07 e RB-16 citam os valores padrão de OPEN-71.

## 8. Verificação

Implementada e verificada em 2026-11-20, pelo [plano](../plans/010-plano.md). Suíte completa: 635 testes, todos passando, com 9 pulados (4 de navegador sem o Playwright, opcional, e 5 marcadores de outras specs).

| Critério | Teste (`tests/aplicacao/test_spec_010_aceite.py`, salvo indicação) | Resultado |
|---|---|---|
| CA-01 | `test_CA_01_RF_40_cadastro_pendente_com_historico_e_auditoria` | Passou |
| CA-02 | `test_CA_02_E1_dados_invalidos_sao_recusados_no_campo` | Passou |
| CA-03 | `test_CA_03_RF_43_RB_04_calendario_ordenado_por_prazo` | Passou |
| CA-04 | `test_CA_04_RF_44_RB_07_aviso_unico_com_o_texto_do_modelo` | Passou |
| CA-05 | `test_CA_05_RB_07_fora_da_janela_nao_avisa` | Passou |
| CA-06 | `test_CA_06_RF_45_RF_47_cumprimento_sem_exigencia` | Passou |
| CA-07 | `test_CA_07_RF_46_RB_29_cumprimento_com_pdf` | Passou |
| CA-08 | `test_CA_08_A2_RF_77_aguardando_evidencia_ate_o_anexo`; no painel, `test_CA_08_RF_77_quadro_aguardando_evidencia_no_painel` (web) | Passou |
| CA-09 | `test_CA_09_E2_evidencia_invalida_e_recusada_no_campo` | Passou |
| CA-10 | `test_CA_10_RF_42_mensal_no_fim_do_mes` | Passou |
| CA-11 | `test_CA_11_RF_42_prazo_conta_do_anterior_e_unica_nao_gera` | Passou |
| CA-12 | `test_CA_12_RF_48_atrasada_no_dia_seguinte_ao_prazo` | Passou |
| CA-13 | `test_CA_13_A5_aguardando_evidencia_que_estoura` | Passou |
| CA-14 | `test_CA_14_RF_49_RB_16_escalonamento_unico_aos_donos_ativos` | Passou |
| CA-15 | `test_CA_15_A6_responsavel_inativo_avisa_os_donos` | Passou |
| CA-16 | `test_CA_16_RF_41_alteracao_de_prazo_e_responsavel_no_historico` | Passou |
| CA-17 | `test_CA_17_E3_alteracoes_fora_do_estado_sao_recusadas` | Passou |
| CA-18 | `test_CA_18_RF_50_historico_e_ocorrencias_da_serie` | Passou |
| CA-19 | `test_CA_19_E4_data_de_amanha_e_recusada` | Passou |
| CA-20 | `test_CA_20_E5_RNF_09_falha_na_auditoria_desfaz_o_cumprimento`; também no SQLite, `test_CA_20_RNF_09_falha_na_auditoria_do_cumprimento_nao_deixa_nada_no_banco` | Passou |
| CA-21 | `test_CA_21_E6_RB_03_RB_04_contador_nao_acessa_obrigacoes`; pela tela, `test_CA_21_contador_nao_ve_o_menu_nem_abre_as_rotas` (web) | Passou |
| CA-22 | `test_CA_22_RNF_15_painel_destaca_atrasadas` (`tests/apresentacao/test_spec_010_web.py`) | Passou |
| CA-23 | `test_CA_23_ADR_002_canal_que_falha_e_tentado_de_novo` | Passou |
| CA-24 | `test_CA_24_A3_alteracao_de_prazo_vale_so_para_a_ocorrencia` | Passou |

Também verificado:

- Regras do domínio, sem banco: `tests/dominio/test_obrigacao.py`, com 44 testes nomeados por RF, RB, OPEN, INV, A e E. Cobrem estados, cumprimento com e sem evidência, conferência do arquivo pelo conteúdo, recorrência no fim do mês, aviso e escalonamento uma vez por prazo e por destinatário.
- Modelos dos alertas (RB-27, INV-6): `tests/aplicacao/test_modelos_de_mensagem.py` (`ModelosDosAlertasDeObrigacao`), com o texto exato.
- Leitura do formulário com arquivo, sem o módulo `cgi`: `tests/apresentacao/test_multipart.py`.
- SQLite (`tests/infraestrutura/test_sqlite.py`, `Spec010NoSQLite`): ida e volta da obrigação com histórico e evidências, conteúdo da evidência à parte, mensagens a usuários junto das mensagens a clientes, e migração de um banco da versão 5 sem perda de dados.
- Interface web (`tests/apresentacao/test_spec_010_web.py`): cadastro, cumprimento com PDF, próxima ocorrência, erros por campo, escape de HTML, alteração de prazo e responsável, caixa de saída com o alerta, auditoria ligada à obrigação e demonstração com obrigações nos quatro estados.
- Foco de revisão do plano:
  - nome de arquivo com caminho ou aspas: `test_foco_1_*`, no domínio e na web;
  - campo de arquivo vazio vale como sem anexo: `test_foco_2_*`;
  - multipart fora da rota ou grande demais: `test_foco_3_*`;
  - Dono que também é o responsável não recebe alerta duplicado: `test_foco_4_*`;
  - dia-base 29, 30 ou 31: `test_foco_5_*`.
- No navegador (Chromium), com a demonstração, em 1280 px e 360 px, para a Dona e o Operador: painel, calendário, todas as obrigações, detalhe de cada uma e Mensagens enviadas, sem rolagem horizontal da página. O download da evidência sai como anexo `application/pdf`.
- Pirâmide de testes recontada: a unidade foi de 36,1% para 38,7% ([`docs/testes.md`](../../docs/testes.md)).

Revisão final da branch, por um revisor independente: nenhum problema crítico. Três achados foram corrigidos, cada um com um teste que falhou antes da correção:
- nome de arquivo com mais de 120 caracteres perdia a extensão e o PDF era recusado: o corte agora preserva a extensão (`test_foco_1_nome_longo_preserva_a_extensao`);
- caracteres de formatação Unicode, como o que inverte o texto (U+202E), passavam para o nome mostrado: agora são descartados (`test_foco_1_caracteres_de_formatacao_unicode_sao_descartados`);
- descrição preenchida sem arquivo era descartada em silêncio: agora é recusada no campo arquivo (`test_descricao_sem_arquivo_e_recusada_no_campo_arquivo`).

Suíte depois das correções: 638 testes, todos passando, com 9 pulados.

Depois da verificação, a branch recebeu a `main` com o PR #106. As decisões desta spec passaram de OPEN-63 a OPEN-66 para OPEN-68 a OPEN-71, porque a `main` já tinha usado aqueles números (regra 7 do `SPECS.md`). As telas foram levadas para a divisão da apresentação por módulo (OPEN-65): `rotas_obrigacoes.py` e `requisicao.py`. As rotas novas entraram em `tests/apresentacao/test_tabela_de_rotas.py`. Suíte depois do merge: 645 testes, todos passando, com 7 pulados.

Dois testes de outras specs mudaram, sem mudar o que verificam. O teste da migração 5 passou a esperar a última versão do banco. O teste da demonstração da Spec 005 passou a contar só as mensagens de orçamento, porque a caixa de saída agora tem também os alertas de obrigação.

### Onde está cada parte

| Parte | Arquivo |
|---|---|
| Regras, estados, recorrência e alertas | `src/remindme/dominio/obrigacao.py` |
| Texto dos alertas (RB-27) | `src/remindme/aplicacao/modelos_de_mensagem.py` |
| Casos de uso, autorização, auditoria e verificação automática | `src/remindme/aplicacao/servico_obrigacoes.py`; `src/remindme/entradas/agendador.py` |
| Persistência | `src/remindme/infraestrutura/sqlite.py` (migração 6) e `memoria.py` |
| Telas e upload | `src/remindme/apresentacao/web/paginas_obrigacoes.py` e `rotas_obrigacoes.py`; `multipart.py` e `requisicao.py` (upload); `aplicacao_web.py` (tabela de rotas); `paginas_painel.py` e `paginas.py` (painel e menu) |
