# Spec 002 — Autenticação e autorização por perfil

## 1. Identificação

| | |
|---|---|
| **ID** | 002 |
| **Nome** | Autenticação e autorização por perfil |
| **Objetivo** | Garantir que só usuários ativos e autenticados operem o sistema e que cada um execute apenas o que seu perfil permite, com tudo negado por padrão. |
| **Valor entregue** | A Dona sabe que o Contador não altera dados, que só ela estorna e cancela e que um usuário inativado perde o acesso na hora. O Administrador mantém usuários e permissões sem mexer no código. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Silva Guerra, em 2026-10-22 |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-02, RF-03, RF-65, RF-66, RF-67 |
| RB | RB-03; preserva RB-02, RB-15, RB-26 e a decisão OPEN-16 |
| RNF | RNF-01, RNF-02, RNF-03, RNF-04, RNF-14 |
| UC | [UC-01](../../docs/casos-de-uso/UC-01-autenticar-usuario.md), [UC-02](../../docs/casos-de-uso/UC-02-administrar-usuarios-e-perfis.md) |
| Entidades | `Usuario`, `Perfil` |
| Drivers e ADRs | DA-02, DA-04; DT-04, DT-06; ADR-004 |
| Depende de | Spec 001 (auditoria). Decisões OPEN-03, OPEN-10, OPEN-32, OPEN-33 e OPEN-34, tomadas em 2026-10-16 e confirmadas em 2026-10-23; OPEN-35, decidida em 2026-10-23. |

Divergências que esta spec trata: DV-04 (cinco perfis) e DV-11 (Contador cadastra e paga), em [`docs/qualidade/divergencias.md`](../../docs/qualidade/divergencias.md).

## 3. Escopo

### Incluído

- Cadastro de usuário pelo Administrador, com exatamente um perfil.
- Alteração de perfil e inativação de usuário.
- Login com e-mail e senha, com sessão guardada no servidor (OPEN-03).
- Armazenamento de senha só como hash com salt, por `scrypt` (OPEN-33).
- Matriz inicial de permissões por perfil, negada por padrão (OPEN-32).
- Alteração das permissões de um perfil pelo Administrador, sem alterar as permissões fixadas por regra de negócio.
- Verificação de sessão e de permissão em toda operação da camada de aplicação, inclusive nas operações da Spec 006.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Acesso do Cliente, por link com código | Spec 009 (OPEN-08, decidida) |
| Tela de login, painel do perfil (RNF-17) e HTTPS (RNF-05) | Primeira spec com interface (OPEN-01, OPEN-12) |
| Bloqueio após tentativas erradas e expiração de sessão | Fora desta spec (OPEN-34) |
| Encerramento de sessão pelo próprio usuário (logout) | Não há requisito. Fica para a primeira spec com interface |
| Recuperação e troca de senha | Não há requisito. A senha inicial é provisória e informada pelo Administrador (OPEN-35) |
| Permissões das operações das specs ainda não escritas | Cada spec aplica a sua linha da matriz da seção 4 |

## 4. Comportamento

### Pré-condições

- Existe ao menos um usuário com perfil Administrador, criado na instalação.
- A Spec 001 está implementada: as alterações desta spec são auditadas.

### Fluxo principal: login e operação permitida

1. O usuário informa e-mail e senha.
2. O sistema confere a senha contra o hash guardado.
3. O sistema cria uma sessão no servidor, associada ao usuário e ao perfil.
4. O sistema devolve as operações que o perfil pode executar (RF-65).
5. O usuário solicita uma operação, informando a sessão.
6. O sistema confere que a sessão é válida, que o usuário está ativo e que o perfil tem a permissão.
7. A operação segue para o domínio.

### Fluxos alternativos

- **A1 — Cadastro de usuário.** O Administrador informa nome, e-mail, uma senha provisória como senha inicial (OPEN-35) e perfil. O sistema cria o usuário ativo, com exatamente um perfil.
- **A2 — Alteração de perfil.** O Administrador troca o perfil de um usuário. A operação seguinte do usuário já usa o novo perfil.
- **A3 — Inativação.** O Administrador inativa um usuário. As sessões dele deixam de valer, e o histórico é preservado.
- **A4 — Alteração de permissões.** O Administrador concede ou retira uma permissão de um perfil. Vale na operação seguinte de qualquer usuário desse perfil, inclusive com a sessão já aberta (RF-03).

### Exceções

- **E1 — Credenciais inválidas.** E-mail inexistente ou senha errada: o login é recusado com a mesma mensagem nos dois casos, e nenhuma sessão é criada (RF-66).
- **E2 — Usuário inativo.** Com e-mail e senha corretos, o login é recusado, e a mensagem orienta a procurar o Administrador (UC-01, E2).
- **E3 — Sem sessão válida.** Operação sem sessão, com sessão desconhecida ou de usuário inativo é recusada (RNF-01).
- **E4 — Operação não permitida.** Operação que o perfil não tem na matriz é negada, com o motivo, e nada é alterado (RF-67, RNF-02).
- **E5 — Permissão fixada por regra.** O Administrador tenta conceder ou retirar uma permissão fixada por regra de negócio: a alteração é recusada, com a regra no motivo.
- **E6 — E-mail já cadastrado.** O cadastro é recusado, com o campo e o motivo (UC-02, E1).
- **E7 — Dados obrigatórios ausentes.** Nome, e-mail, senha inicial ou perfil ausente: o cadastro é recusado, com os campos faltantes (UC-02, E2).

Toda recusa informa o motivo e não altera nenhum dado.

### Matriz inicial de permissões (OPEN-32)

Proposta montada a partir das personas e dos atores dos casos de uso. **P** = permitido; **—** = negado; **F** = fixado por regra de negócio, não alterável pelo Administrador. Operação que não aparece na matriz é negada.

| Operação | Caso de uso | Dono | Operador Financeiro | Contador | Cliente | Administrador |
|---|---|---|---|---|---|---|
| Cadastrar título, registrar pagamento | UC-06 | P | P | — F (RB-03) | — | — |
| Verificar vencimentos | UC-06 | P | P | — F (RB-03) | — | — |
| Estornar pagamento | UC-06 | P F (RB-02) | — F | — F | — F | — F |
| Cancelar título | UC-06 | P F (OPEN-16) | — F | — F | — F | — F |
| Consultar títulos | UC-06 | P | P | P | Só os próprios, F (RB-26; Spec 009) | — |
| Manter clientes | UC-03 | P | P | — F (RB-03) | — | — |
| Consultar clientes (OPEN-42) | UC-03 | P | P | P | — | — |
| Conduzir orçamento | UC-04 | P | P | — F (RB-03) | Decidir o próprio (Spec 005) | — |
| Aprovar desconto fora da alçada | UC-05 | P F (RB-15) | — F | — F | — F | — F |
| Gerenciar obrigações | UC-09 | P | P | — F (RB-03) | — | — |
| Classificar lançamento | UC-10 | P | P | — F (RB-03) | — | — |
| Apurar e consultar resultado | UC-11 | P | P | P | — | — |
| Consultar auditoria | UC-12 | P | — | P | — | P |
| Configurar regras | UC-13 | — | — | — | — | P |
| Importar CSV | UC-14 | P | P | — F (RB-03) | — | — |
| Exportar CSV | UC-14 | P | P | P | — | — |
| Administrar usuários e permissões | UC-02 | — | — | — | — | P |

Nesta spec, a matriz é aplicada às operações das Specs 002 e 006. As demais linhas valem quando a spec de cada operação for implementada. O Dono que também administra o sistema usa um segundo usuário, com perfil Administrador (OPEN-10), porque cada usuário tem exatamente um perfil (RF-02).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Todo usuário tem exatamente um perfil. | RF-02; modelo de domínio, relação 1 |
| INV-2 | Nenhuma operação da camada de aplicação executa sem sessão válida de usuário ativo e sem permissão explícita do perfil. | RNF-01, RNF-02 |
| INV-3 | A senha nunca é armazenada, auditada nem devolvida em claro. | RNF-04 |
| INV-4 | As permissões marcadas com F não mudam por configuração. | RB-02, RB-03, RB-15, RB-26, OPEN-16 |
| INV-5 | A autorização é verificada na camada de aplicação, em um único ponto, antes de chamar o domínio. | DT-06, RNF-03 |
| INV-6 | Não existem dois usuários com o mesmo e-mail. | UC-02, E1 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Administrador autenticado | ele cadastra um usuário com nome, e-mail, senha provisória e perfil Operador Financeiro | o usuário é criado ativo, com exatamente esse perfil, e a operação é auditada sem a senha | RF-02, INV-1, INV-3, OPEN-35 |
| CA-02 | um usuário com o e-mail diego@exemplo.com | o Administrador cadastra outro usuário com o mesmo e-mail | o cadastro é recusado, informando o campo e-mail e o motivo | E6, INV-6, RNF-14 |
| CA-03 | um Administrador autenticado | ele cadastra um usuário sem perfil e sem e-mail | o cadastro é recusado, indicando os dois campos | E7, RNF-14 |
| CA-04 | um Operador Financeiro autenticado | ele tenta cadastrar um usuário | a operação é negada e nenhum usuário é criado | RNF-02, E4 |
| CA-05 | dois usuários cadastrados com a mesma senha | o armazenamento é inspecionado | nenhum registro contém a senha; cada um guarda hash `scrypt` e salt próprios, e os dois hashes são diferentes | RNF-04, INV-3 |
| CA-06 | um usuário ativo com perfil Contador | ele faz login com e-mail e senha corretos | uma sessão é criada, e as operações devolvidas são exatamente as permitidas ao Contador na matriz | RF-65 |
| CA-07 | um usuário cadastrado | o login é tentado com e-mail inexistente e, depois, com senha errada | as duas tentativas são recusadas com a mesma mensagem, e nenhuma sessão é criada | RF-66, E1 |
| CA-08 | um usuário inativo | ele faz login com e-mail e senha corretos | o login é recusado, a mensagem orienta a procurar o Administrador, e nenhuma sessão é criada | E2 |
| CA-09 | nenhuma sessão, ou uma sessão desconhecida | uma operação de título é solicitada | a operação é recusada e nada é alterado | RNF-01, E3 |
| CA-10 | um Contador autenticado e um título Aberto | ele tenta cadastrar um título e registrar um pagamento | as duas operações são negadas com o motivo, e nada é alterado | RB-03, RF-67, DV-11 |
| CA-11 | um Operador Financeiro autenticado | ele solicita uma operação que não está na matriz | a operação é negada | RNF-02, E4 |
| CA-12 | um Operador Financeiro com sessão aberta | o Administrador retira de seu perfil a permissão de cadastrar título | o próximo cadastro de título desse Operador é negado, sem novo login | RF-03, A4 |
| CA-13 | um Administrador autenticado | ele tenta conceder ao Operador Financeiro a permissão de estornar, ou ao Contador a de registrar pagamento | a alteração é recusada, com a regra no motivo, e a matriz não muda | INV-4, E5, RB-02, RB-03 |
| CA-14 | um usuário com sessão aberta | o Administrador o inativa | a operação seguinte dessa sessão é recusada, e os registros feitos por ele continuam na auditoria | A3, OPEN-03 |
| CA-15 | um usuário Operador Financeiro | o Administrador muda seu perfil para Contador | a operação seguinte usa o perfil Contador, e a auditoria guarda o perfil anterior e o novo | A2, RF-05 |
| CA-16 | um Operador Financeiro autenticado | ele chama diretamente o serviço de estorno, sem interface | a operação é negada | RNF-03, RB-02 |

Os testes automatizados levam no nome o identificador do critério ou da regra, por exemplo `test_CA_10_contador_nao_registra_pagamento` e `test_RB_03_...`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-03 | Sessão no servidor ou token | Decidida em 2026-10-16 e confirmada em 2026-10-23: sessão no servidor. |
| OPEN-08 | Como o Cliente se autentica | Decidida em 2026-10-16 e confirmada em 2026-10-23: link com código pelo canal de notificação, na Spec 009. Não bloqueia esta spec. |
| OPEN-10 | Administrador é perfil próprio ou papel do Dono | Decidida em 2026-10-16 e confirmada em 2026-10-23: perfil próprio; o Dono pode ter também um usuário Administrador. |
| OPEN-32 | Matriz inicial de permissões | Decidida em 2026-10-16 e confirmada em 2026-10-23: a matriz da seção 4, sujeita à revisão desta spec. |
| OPEN-33 | Algoritmo de hash de senha | Decidida em 2026-10-16 e confirmada em 2026-10-23: `scrypt`, da biblioteca padrão. |
| OPEN-34 | Bloqueio após tentativas e expiração de sessão | Decidida em 2026-10-16 e confirmada em 2026-10-23: fora desta spec. |
| OPEN-35 | Como o usuário recebe a senha inicial? | Decidida em 2026-10-23: o Administrador informa uma senha provisória no cadastro. Não bloqueia mais. |
| OPEN-39 | Como é criado o primeiro Administrador? | Decidida em 2026-10-23, por delegação: comando de instalação, só quando não há Administrador ativo. |
| OPEN-42 | Quem consulta clientes? | Decidida em 2026-10-23, por delegação: Dono, Operador Financeiro e Contador; linha nova na matriz. |
| OPEN-43 | Quanto tempo vale uma sessão? | Decidida em 2026-10-23, por delegação: 8 horas a partir da entrada. |
| OPEN-44 | Qual o tamanho mínimo da senha? | Decidida em 2026-10-23, por delegação: 8 caracteres. |
| OPEN-45 | O último Administrador ativo pode ser inativado ou rebaixado? | Decidida em 2026-10-23, por delegação: não; e o perfil Administrador não perde a administração de usuários e permissões. |
| OPEN-46 | O cadastro de usuário aceita o perfil Cliente? | Decidida em 2026-10-23, por delegação: não; o Cliente acessa por link com código (Spec 009). |
| OPEN-47 | Entrar e sair são auditados? | Decidida em 2026-10-23, por delegação: sim, sem senha e sem identificador da sessão. |

## 8. Verificação

Verificada em 2026-10-23, com `python3 -m unittest discover -s tests -t .`: 254 testes, todos passando (7 pulados por dependerem de specs futuras). Testes em [`tests/aplicacao/test_spec_002_aceite.py`](../../tests/aplicacao/test_spec_002_aceite.py) (critérios e decisões) e [`tests/dominio/test_permissoes.py`](../../tests/dominio/test_permissoes.py) (matriz e usuário). Plano em [`plans/002-plano.md`](../plans/002-plano.md) e tarefas em [`tasks/002-tarefas.md`](../tasks/002-tarefas.md).

### Critérios de aceitação

| Critério | Teste | Resultado |
|---|---|---|
| CA-01 | `test_CA_01` | Passou |
| CA-02 | `test_CA_02` (inclui RNF-14) | Passou |
| CA-03 | `test_CA_03` (inclui RNF-14) | Passou |
| CA-04 | `test_CA_04` | Passou |
| CA-05 | `test_CA_05` (inclui RNF-04) | Passou |
| CA-06 | `test_CA_06` (inclui RF-65) | Passou |
| CA-07 | `test_CA_07` (inclui RF-66) | Passou |
| CA-08 | `test_CA_08` | Passou |
| CA-09 | `test_CA_09` (inclui RNF-01) | Passou |
| CA-10 | `test_CA_10` (inclui RB-03); também a matriz de `test_seguranca_de_acesso.py` | Passou |
| CA-11 | `test_CA_11` | Passou |
| CA-12 | `test_CA_12` (inclui RF-03) | Passou |
| CA-13 | `test_CA_13`; `test_RB_02_RB_15_OPEN_16_*`, `test_RB_03_*`, `test_RB_26_*` | Passou |
| CA-14 | `test_CA_14` | Passou |
| CA-15 | `test_CA_15` (inclui RF-05) | Passou |
| CA-16 | `test_CA_16` (inclui RNF-03 e RB-02) | Passou |

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1 | `test_RF_02_*`, CA-01, CA-15: o perfil é um único valor de `Perfil` | Passou |
| INV-2 | CA-09, CA-10, CA-14 e a matriz de `test_seguranca_de_acesso.py`; toda operação dos serviços recebe a sessão | Passou |
| INV-3 | CA-01, CA-05, `test_OPEN_47_*` | Passou |
| INV-4 | CA-13 e `PermissoesFixadas` | Passou |
| INV-5 | `test_INV_5_somente_a_execucao_chama_a_autorizacao` | Passou |
| INV-6 | CA-02 e `test_INV_6_*` | Passou |

### Divergências e limitações

| Item | Situação |
|---|---|
| Assinatura dos serviços | As operações da Spec 006 passaram a receber a sessão no lugar do usuário. Os testes antigos abrem sessões direto no dublê (`tests/apoio.py`); o comportamento verificado não mudou. |
| `Auditoria` da Spec 001 | A transação e o erro não tratado foram para `Execucao`, junto da autorização. A gravação da auditoria continua só em `OperacaoAuditada` (Spec 001, INV-5). O plano da Spec 001 foi atualizado. |
| Linha nova na matriz | "Consultar clientes", decidida em OPEN-42, para o Contador ver o cliente dos títulos que consulta. |
| Defeito encontrado pelos testes | Perfil desconhecido fazia a mensagem de negação falhar em vez de negar. Corrigido em `dominio/permissoes.py` (`test_RNF_02_perfil_desconhecido_e_negado_em_tudo`). |
| Telas | Login, painel, logout e telas de usuários e permissões ficam na Spec 017. |
| Persistência | Em memória nesta spec; o SQLite entra na Spec 017 (ADR-007), com os mesmos testes de contrato. |
