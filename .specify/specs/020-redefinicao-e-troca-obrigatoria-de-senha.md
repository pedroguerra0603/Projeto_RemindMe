# Spec 020 — Redefinição de senha pelo Administrador e troca obrigatória da senha provisória

## 1. Identificação

| | |
|---|---|
| **ID** | 020 |
| **Nome** | Redefinição de senha pelo Administrador e troca obrigatória da senha provisória |
| **Objetivo** | Permitir que o Administrador devolva o acesso a quem esqueceu a senha, definindo uma nova senha provisória, e obrigar quem recebe uma senha provisória a trocá-la antes de usar o sistema. |
| **Valor entregue** | O Operador Financeiro que esqueceu a senha volta a entrar no mesmo dia, sem perder o usuário nem o histórico. A Dona sabe que nenhuma senha conhecida pelo Administrador continua em uso depois do primeiro acesso. |
| **Situação** | **Aprovada** |
| **Aprovada por** | Renan Gandolpho, em 2026-11-23, na conversa com o agente: decidiu a OPEN-59 e a OPEN-60, escolheu os detalhes (troca obrigatória imposta na aplicação, senhas definitivas da demonstração, redefinição de qualquer outro usuário, usuários existentes com senha definitiva na migração) e aprovou a spec. A revisão do conteúdo fica no PR. |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-97 e RF-98 (novos); RF-02 (cadastro pelo Administrador); RF-95 e RF-96 (troca, Spec 019); RF-04 e RF-05 (auditoria); preserva RF-65 e RF-66 |
| RB | Nenhuma nova |
| RNF | RNF-01, RNF-02, RNF-03, RNF-04, RNF-09, RNF-14 |
| UC | [UC-02](../../docs/casos-de-uso/UC-02-administrar-usuarios-e-perfis.md) (A3, nova) e [UC-16](../../docs/casos-de-uso/UC-16-trocar-a-propria-senha.md) (A2, nova) |
| Entidades | `Usuario`: indicação de senha provisória, registro técnico como o hash da senha; sessão, registro técnico da Spec 002 |
| Drivers e ADRs | DA-02, DA-03, DA-04; ADR-004, ADR-006, ADR-007 |
| Depende de | Specs 001, 002, 017 e 019. Decisões OPEN-33 (`scrypt`), OPEN-34 (sem bloqueio por tentativas), OPEN-35 (senha provisória no cadastro), OPEN-44 (tamanho da senha), OPEN-45 (último Administrador), OPEN-55 (conta pedida pela tela de entrada), OPEN-58 (troca da própria senha) e OPEN-59 e OPEN-60, decididas em 2026-11-23 por Renan Gandolpho. |

## 3. Escopo

### Incluído

- Redefinição, pelo Administrador, da senha de qualquer outro usuário, ativo ou inativo, inclusive de outro Administrador (OPEN-59).
- Indicação de senha provisória no usuário:
  - é provisória a senha informada pelo Administrador no cadastro (UC-02) e na redefinição (UC-02, A3);
  - é definitiva a senha do primeiro Administrador, criada pela linha de comando (OPEN-39); a da conta pedida pela tela de entrada (OPEN-55), que a própria pessoa escolhe; e a dos usuários da demonstração;
  - deixa de ser provisória quando o usuário troca a senha (Spec 019).
- Troca obrigatória, imposta na aplicação: enquanto a senha for provisória, toda operação do usuário é recusada, exceto trocar a própria senha, sair e consultar a sessão (RF-98, OPEN-60).
- Interface: formulário "Redefinir senha" na página do usuário, para quem administra usuários; qualquer página pedida por usuário com senha provisória leva à tela "Trocar senha", com um aviso.
- Migração do SQLite: a indicação de senha provisória entra no armazenamento dos usuários, e os usuários já existentes ficam com a senha definitiva (OPEN-60).

### Fora do escopo

| Item | Motivo |
|---|---|
| Recuperação da senha pelo próprio usuário, sem o Administrador | Exige um canal para falar com o usuário (ADR-002), que não existe; a execução é local (OPEN-12, OPEN-62). |
| Envio da senha provisória ao usuário pelo sistema | Pelo mesmo motivo: o Administrador informa a senha ao usuário por fora, como no cadastro (OPEN-35). |
| Consulta da senha atual pelo Administrador | A senha só existe como hash (RNF-04). |
| Bloqueio após tentativas erradas, histórico e expiração periódica de senhas | Fora do escopo, como na Spec 019 (OPEN-34). |
| Linha nova na matriz de permissões | A redefinição usa a operação "Administrar usuários" da Spec 002, a mesma do cadastro. |

## 4. Comportamento

### Pré-condições

- Redefinição: o usuário que redefine está ativo, tem sessão válida, senha definitiva e a operação "Administrar usuários" (Spec 002).
- Troca obrigatória: o usuário está ativo, tem sessão válida e senha provisória.

### Fluxo principal 1: redefinição da senha pelo Administrador

1. O Administrador abre a página do usuário e informa a nova senha provisória.
2. O sistema confere a sessão (RNF-01) e a permissão "Administrar usuários" (RNF-02, RNF-03).
3. O sistema confere que o usuário existe e que não é o próprio Administrador.
4. O sistema valida a senha (OPEN-44).
5. O sistema guarda o hash `scrypt` da nova senha, com salt novo (RNF-04, OPEN-33), e a marca como provisória.
6. O sistema encerra todas as sessões do usuário.
7. O sistema registra a redefinição na auditoria, com o Administrador como responsável e sem a senha (RF-04).
8. O Administrador volta à página do usuário, com o aviso de que a senha foi redefinida e deve ser informada ao usuário.

Os passos 5 a 7 acontecem numa só transação (RNF-09).

### Fluxo principal 2: troca obrigatória da senha provisória

1. O usuário entra com a senha provisória (RF-65).
2. O usuário pede qualquer página do sistema.
3. O sistema o leva à tela "Trocar senha", com o aviso de que a senha provisória deve ser trocada antes de continuar.
4. O usuário troca a senha como na Spec 019, informando a senha provisória como senha atual.
5. Na mesma transação da troca, a senha deixa de ser provisória.
6. O usuário vai ao painel e segue com as permissões do seu perfil.

### Fluxos alternativos

- **A1 — Usuário inativo.** A redefinição muda a senha e a marca como provisória; o usuário continua inativo. Quando for ativado, ele troca a senha no primeiro acesso.
- **A2 — Outro Administrador.** A redefinição vale como para qualquer outro usuário. O Administrador redefinido troca a senha no primeiro acesso.
- **A3 — Cadastro pelo Administrador.** O usuário cadastrado pelo Administrador (UC-02) nasce com a senha provisória e segue o fluxo principal 2 na primeira entrada.
- **A4 — Sair sem trocar.** O usuário com senha provisória pode sair. Na entrada seguinte, continua obrigado a trocar.
- **A5 — Nova redefinição.** Redefinir de novo a senha de quem ainda tem senha provisória substitui a provisória anterior, que deixa de entrar.

### Exceções

- **E1 — Sem permissão.** Quem não tem "Administrar usuários" é recusado, e nada muda (RNF-02, RF-67).
- **E2 — A própria senha.** O Administrador que tenta redefinir a própria senha é recusado, com a indicação de usar "Trocar senha" (Spec 019). A troca da própria senha exige a senha atual (RF-95).
- **E3 — Senha inválida.** Ausente, com menos de 8 ou mais de 256 caracteres (OPEN-44): recusada, com o motivo no campo da senha.
- **E4 — Usuário inexistente.** Recusado, e nada muda.
- **E5 — Sem sessão válida.** Recusado (RNF-01). A interface volta à tela de entrada.
- **E6 — Falha durante a redefinição**, por exemplo na gravação da auditoria. Nenhuma alteração permanece: a senha anterior continua valendo, e as sessões continuam abertas (RNF-09).
- **E7 — Formulário sem a proteção da sessão.** Recusado, como todo formulário da interface (Spec 017).
- **E8 — Operação pedida com senha provisória.** Qualquer operação além de trocar a própria senha, sair e consultar a sessão é recusada com o motivo "Troque a senha provisória antes de continuar." Nenhum dado é lido nem alterado (RF-98).

Toda recusa indica os campos com problema (RNF-14), não altera nenhum dado e não devolve à página a senha digitada.

### Acesso

A redefinição é uma operação de "Administrar usuários", conferida no mesmo ponto único das demais (Spec 002, INV-5).

A troca obrigatória também é conferida nesse ponto único: com senha provisória, a sessão vale só para trocar a própria senha, sair e consultar a sessão. Assim a regra vale para qualquer chamada da camada de aplicação, com ou sem a interface (RNF-03).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | A senha, provisória ou definitiva, nunca é armazenada, auditada nem devolvida em claro, inclusive na página de recusa e na página do usuário. | RNF-04; Spec 019, INV-1 |
| INV-2 | A senha é provisória se, e somente se, foi definida pelo Administrador, no cadastro ou na redefinição, e o usuário ainda não a trocou. | RF-97, RF-98, OPEN-60 |
| INV-3 | Com senha provisória, nenhuma operação além de trocar a própria senha, sair e consultar a sessão lê ou altera dados. | RF-98, RNF-03 |
| INV-4 | Na redefinição, o novo hash, a marca de provisória, o encerramento das sessões do usuário e o registro de auditoria são gravados na mesma transação. Na troca obrigatória, o novo hash e o fim da marca de provisória também são. | RNF-09 |
| INV-5 | Ninguém redefine a própria senha por esta operação; a própria senha só muda pela troca da Spec 019. | OPEN-58, OPEN-59 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Operador Financeiro ativo, com senha definitiva e duas sessões abertas | o Administrador redefine a senha dele para "provisoria-123" | a redefinição é aceita; as duas sessões são recusadas na operação seguinte; a entrada com a senha antiga é recusada com a mensagem genérica, e com "provisoria-123" abre sessão | RF-97, RF-66 |
| CA-02 | o Operador do CA-01, que entrou com "provisoria-123" | ele pede a consulta de títulos e, depois, o cadastro de um cliente | as duas operações são recusadas com o motivo de trocar a senha provisória, e nenhum dado é alterado | RF-98, E8, INV-3 |
| CA-03 | o Operador do CA-01, com sessão aberta e senha provisória | ele troca a senha para "definitiva-456", informando "provisoria-123" como atual | a troca é aceita; a senha deixa de ser provisória, e a consulta de títulos passa a ser aceita | RF-95, RF-98, INV-2 |
| CA-04 | um usuário com senha provisória | ele sai, entra de novo com a senha provisória e pede uma operação | a operação continua recusada | A4, RF-98 |
| CA-05 | o Administrador cadastra um Contador com senha provisória | o Contador entra e pede uma consulta | a consulta é recusada até ele trocar a senha | A3, RF-02, OPEN-60 |
| CA-06 | o primeiro Administrador criado pela linha de comando, uma conta pedida pela tela de entrada e já ativada, e os usuários da demonstração | cada um entra e pede uma operação permitida ao seu perfil | as operações são aceitas, sem troca obrigatória | OPEN-60 |
| CA-07 | um usuário inativo, com senha definitiva | o Administrador redefine a senha dele e, depois, o ativa | o usuário continua inativo até ser ativado; ao entrar, é obrigado a trocar a senha | A1, RF-97 |
| CA-08 | dois Administradores ativos | um redefine a senha do outro | a redefinição é aceita, e o outro Administrador é obrigado a trocar a senha no primeiro acesso | A2, OPEN-59 |
| CA-09 | um Administrador com sessão aberta | ele tenta redefinir a própria senha | a redefinição é recusada com a indicação de usar "Trocar senha", e nada muda | E2, INV-5 |
| CA-10 | um Dono, um Operador Financeiro e um Contador, sem "Administrar usuários" | cada um tenta redefinir a senha de outro usuário | as três tentativas são negadas, e nada muda | E1, RNF-02, RNF-03 |
| CA-11 | um Administrador com sessão aberta | ele redefine uma senha com 7 caracteres, outra com 257, outra vazia, e a de um usuário inexistente | as quatro são recusadas, com o motivo no campo da senha nas três primeiras; nada muda | E3, E4, RNF-14 |
| CA-12 | nenhuma sessão, uma sessão desconhecida e uma vencida | a redefinição é pedida em cada caso | as três são recusadas, e nenhuma senha muda | E5, RNF-01 |
| CA-13 | uma falha injetada na gravação da auditoria | o Administrador redefine a senha de um usuário com sessão aberta | a operação falha; a senha anterior continua entrando, a sessão continua aberta e a senha não fica provisória | E6, RNF-09, INV-4 |
| CA-14 | um usuário cuja senha foi redefinida | o armazenamento e a auditoria são inspecionados | o usuário tem novo hash `scrypt`, com salt diferente do anterior; a auditoria tem um registro "senha: redefinida", com o Administrador como responsável; nenhum registro contém a senha | RNF-04, RF-04, INV-1 |
| CA-15 | um usuário com senha provisória ainda não trocada | o Administrador redefine a senha de novo | a provisória anterior deixa de entrar, e a nova entra e continua provisória | A5 |
| CA-16 | a interface web, com o Administrador na página de outro usuário | ele envia o formulário "Redefinir senha" com uma senha válida | volta à página do usuário com o aviso da redefinição; o HTML não contém a senha; sem a proteção da sessão, o envio é recusado e nada muda | Fluxo 1, E7, INV-1 |
| CA-17 | a interface web, com um usuário de senha provisória | ele pede o painel, a lista de títulos e uma página de cliente | cada pedido leva à tela "Trocar senha", com o aviso da senha provisória; sair continua possível | RF-98, Fluxo 2 |
| CA-18 | a interface web, com o Administrador na página do próprio usuário | a página é aberta | não há formulário "Redefinir senha"; há o caminho para "Trocar senha" | E2, INV-5 |
| CA-19 | um banco SQLite criado antes desta spec, com usuários cadastrados | a aplicação é aberta sobre ele | os usuários existentes entram sem troca obrigatória; uma redefinição feita depois continua provisória quando a aplicação é reaberta | ADR-007, OPEN-60 |
| CA-20 | o sistema em execução, num navegador real | o Administrador redefine a senha de um usuário; o usuário entra com a senha provisória, é levado à troca, troca a senha e chega ao painel | o fluxo completo funciona, e a senha provisória deixa de entrar | RF-97, RF-98, ponta a ponta |

Os testes automatizados levam no nome o identificador do critério, por exemplo `test_CA_02_senha_provisoria_recusa_outras_operacoes`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-59 | O Administrador pode redefinir a senha de outro usuário? | Não: decidida em 2026-11-23 por Renan Gandolpho. |
| OPEN-60 | A senha provisória deve ser trocada no primeiro acesso? | Não: decidida em 2026-11-23 por Renan Gandolpho, com a regra imposta na aplicação, as senhas definitivas listadas no escopo e os usuários existentes com senha definitiva na migração. |

## 8. Verificação

Não verificada: a spec está aprovada e ainda não foi implementada.
