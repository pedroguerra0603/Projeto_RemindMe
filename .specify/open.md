# Questões em aberto — RemindMe

Decisões que a baseline ainda não define. O agente não preenche essas lacunas: cada uma exige decisão da equipe. Ao decidir, registre a decisão aqui, com data, e atualize os documentos afetados no mesmo PR. Decisão cara de reverter também vira ADR.

| ID | Questão | Por que está em aberto | Sugestão | Afeta | Situação |
|---|---|---|---|---|---|
| OPEN-01 | Qual linguagem e qual framework web? | A baseline descreve o domínio, e não a tecnologia. | Escolher pela familiaridade da equipe, desde que o domínio fique sem dependência do framework (ADR-001). | Todas as specs; `docs/execucao.md` | Aberta |
| OPEN-02 | Qual banco de dados? | O modelo conceitual não é modelo físico. | Banco relacional com transações e restrição de unicidade. | Spec 001; `docs/arquitetura.md` | Aberta |
| OPEN-03 | Sessão no servidor ou token? | Os RNF exigem autenticação, mas não escolhem o mecanismo. | — | Spec 002 | Aberta |
| OPEN-04 | Qual provedor de IA? | ADR-003 exige que seja trocável, mas não escolhe. | Começar apenas com a IA simulada. | Specs 009 e 011 | Aberta |
| OPEN-05 | Qual o limiar de confiança para aceitar a sugestão da IA? | RB-08 fala em limiar configurado, sem valor padrão. | 0,85 como padrão, configurável. | Spec 011 | Aberta |
| OPEN-06 | Quais os limites da renegociação automática? | RB-28 fala em limites configurados, sem defini-los. | Prazo máximo de 30 dias após o vencimento original e no máximo 1 renegociação automática por título. | Spec 009 | Aberta |
| OPEN-07 | De onde vêm os lançamentos de despesa? | A apuração usa despesas, mas nenhum RF as cria. Contas a pagar está fora do escopo. | Cadastro manual de lançamento de despesa e importação CSV. Exige novo RF. | Specs 011 e 012; `docs/requisitos.md` | Aberta |
| OPEN-08 | Como o Cliente se autentica? | A persona Cliente não quer criar conta complicada, e RNF-01 exige autenticação. | Link de acesso com código enviado pelo canal de notificação. | Specs 002 e 009 | Aberta |
| OPEN-09 | Quais as metas de disponibilidade, backup e tempo limite da IA? | RNF-07, RNF-08 e RNF-24 estão com valores propostos **(P)**. | 99% ao mês; backup diário com 7 dias de retenção; 10 segundos. | `docs/requisitos.md` | Aberta |
| OPEN-10 | Administrador é um perfil próprio ou um papel do Dono? | Os casos de uso tratam o Administrador como ator; as personas têm quatro perfis. | Perfil próprio, que o Dono pode acumular. | Spec 002; `docs/personas.md` | Aberta |
| OPEN-11 | Há juros ou multa em título vencido? | Nenhum requisito trata disso. O saldo hoje é valor menos pagamentos. | Fora do MVP. | Spec 006 | Aberta |
| OPEN-12 | Onde o sistema será hospedado para a apresentação? | Não definido. | — | `docs/execucao.md` | Aberta |
| OPEN-13 | Qual o mecanismo do agendador? | DT-07 define o papel, e não o mecanismo. | Tarefa periódica no próprio processo da aplicação. | Specs 008 e 010 | Aberta |
| OPEN-14 | O que acontece com a renegociação quando a nova data vence sem pagamento? | RB-20 e RB-28 não cobrem promessa descumprida. | O título volta a Vencido pela regra normal (RF-24) e a régua recomeça. | Spec 009 | Aberta |
| OPEN-15 | O orçamento aprovado gera um título ou um título por parcela? | RF-19 copia a "condição de pagamento", sem dizer se há parcelas. | Um título por orçamento no MVP. | Specs 005 e 006 | Aberta |
| OPEN-16 | Qual perfil pode cancelar um título? | RF-31 exige motivo, mas não diz quem pode cancelar. | Somente o Dono, como no estorno. | Spec 006 | Aberta |
| OPEN-17 | A data de um pagamento pode ser passada ou futura em relação ao registro? | RF-25 não restringe a data. | Aceitar data passada; recusar data futura. | Spec 006 | Aberta |

## Divergências resolvidas na revisão de outubro de 2026

Estas contradições existiam entre os documentos anteriores e foram resolvidas na baseline. A equipe deve confirmar cada uma na revisão do PR.

| Divergência | Resolução adotada |
|---|---|
| A antiga RN05 convertia o orçamento automaticamente; RF11 e RF12 descreviam conversão solicitada por usuário. | A conversão é automática na aprovação (RB-05, RF-11). RF-12 protege contra conversão indevida. |
| A antiga RN16 escalava ao Dono imediatamente; RF49 escalava após período configurado. | Tolerância configurável, com padrão de 0 dias (RB-16). |
| A antiga RN07 fixava 7 dias; RF44 falava em período configurado. | 7 dias como padrão, configurável por tipo (RB-07). |
| A persona Contador registrava operações e validava classificações, mas o perfil era somente leitura. | O Contador só consulta e exporta (RB-03). |
| O modelo ligava `Usuario` e `Perfil` como 1 para 1. | Um perfil tem muitos usuários; cada usuário tem um perfil. |
| O README chamava o sistema de "Fluxo"; os documentos, de "RemindMe". | RemindMe. |
| As regras de negócio usavam `RN` e EARS; os casos de uso misturavam `RN` e `RF`. | Prefixo `RB`, forma declarativa, com a indicação do RF que aplica cada uma. |
| RF11 e RF19 descreviam o mesmo comportamento; RF60 e RF63 repetiam RF05 e RF18. | RF-19 passou a tratar dos dados copiados; RF-60 e RF-63 foram retirados. |
| Não havia requisitos funcionais para login, portal do cliente, IA e CSV, embora constassem na visão e nos casos de uso. | Criados RF-65 a RF-85. |
