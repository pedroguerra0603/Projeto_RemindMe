# Spec 001 — Fundação: estrutura em camadas e auditoria de operações

## 1. Identificação

| | |
|---|---|
| **ID** | 001 |
| **Nome** | Fundação: estrutura em camadas e auditoria de operações |
| **Objetivo** | Garantir que toda operação que cria, altera ou muda o estado de um registro deixe uma prova imutável de quem fez, o quê, quando e sobre qual registro, gravada junto com a própria operação. |
| **Valor entregue** | O Dono consegue provar quem fez cada operação, e nenhuma operação acontece sem registro. A base vale para todas as specs seguintes. |
| **Situação** | **Verificada** — todos os critérios de aceitação passaram (seção 8). |
| **Aprovada por** | João Pedro Guerra, em 2026-10-16 |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-04, RF-05, RF-61, RF-62 |
| RB | RB-01, RB-30 |
| RNF | RNF-06, RNF-09, RNF-19, RNF-21, RNF-23 |
| UC | [UC-12](../../docs/casos-de-uso/UC-12-consultar-auditoria.md) (dados que a consulta vai apresentar) |
| Entidades | `RegistroAuditoria`; referência a `Usuario` |
| Drivers e ADRs | DA-01, DA-02, DA-03, DA-07, DA-09; ADR-001, ADR-004 |
| Depende de | OPEN-01 (decidida). OPEN-02 não bloqueia: a persistência desta spec é em memória, com testes de contrato a repetir quando houver banco. |

Divergências que esta spec trata: DV-05, sobre o usuário de uma operação automática, em [`docs/qualidade/divergencias.md`](../../docs/qualidade/divergencias.md).

## 3. Escopo

### Incluído

- Registro de auditoria de toda operação aceita que cria, altera ou muda o estado de um registro.
- Valor anterior e novo valor de cada campo alterado.
- Gravação da auditoria na mesma transação da operação.
- Recusa de alteração e de exclusão de registros de auditoria.
- Registro de operação automática, sem usuário.
- Registro de erro não tratado, com identificador de correlação.
- Regra de dependência entre camadas e suíte sem credencial externa, como critérios verificáveis.
- Aplicação da auditoria às operações já implementadas da Spec 006.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Consulta e filtros da auditoria | Spec 013 (RF-64) |
| Autenticação e perfil de quem consulta | Spec 002 |
| Persistência em banco de dados | OPEN-02 |
| Política de retenção dos registros | OPEN-31 |
| Auditoria de orçamento, obrigação e lançamento | Specs 004, 005, 010 e 011, que usam esta fundação |
| Interface web | Primeira spec com interface (OPEN-01) |

## 4. Comportamento

### Pré-condições

- A operação é executada por um serviço da camada de aplicação.
- O usuário que executa a operação é conhecido, salvo em operação automática.

### Fluxo principal: operação auditada

1. Um usuário solicita uma operação que cria, altera ou muda o estado de um registro.
2. O sistema abre uma transação.
3. O domínio executa a operação.
4. O sistema grava um registro de auditoria com usuário, data e hora, operação e registro afetado.
5. Para cada campo alterado, o registro guarda o nome do campo, o valor anterior e o novo valor.
6. O sistema confirma a transação. Operação e auditoria passam a existir juntas.

### Fluxos alternativos

- **A1 — Criação.** No passo 5, um registro criado não tem valor anterior. O registro de auditoria informa o estado inicial como novo valor.
- **A2 — Mudança de estado.** O campo alterado é o estado, com o estado anterior e o novo.
- **A3 — Operação com motivo.** Em estorno, cancelamento ou alteração que exige motivo (RF-31), o registro guarda o motivo.
- **A4 — Operação automática.** Uma operação disparada pelo sistema, sem usuário, como a verificação de vencimento, gera registro sem usuário, identificado como automático e com o nome da rotina que disparou a operação (OPEN-30).
- **A5 — Vários registros afetados.** Uma operação que altera mais de um registro gera um registro de auditoria por registro afetado. Por exemplo, o estorno altera o pagamento e o estado do título.

### Exceções

- **E1 — Operação recusada.** Uma operação recusada por regra de negócio não grava nenhum registro de auditoria.
- **E2 — Falha ao gravar a auditoria.** A operação é desfeita, e nenhuma alteração permanece (RNF-09).
- **E3 — Falha ao gravar a operação.** Os registros de auditoria daquela transação são desfeitos.
- **E4 — Tentativa de alterar ou excluir um registro de auditoria.** A operação não existe para nenhum perfil e é recusada. O registro continua igual (RB-30, RNF-06).
- **E5 — Erro não tratado.** O sistema registra data e hora, operação, usuário e um identificador de correlação; desfaz a operação; e não esconde o erro de quem chamou (RNF-21).

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Um registro de auditoria gravado nunca muda nem é excluído. | RB-30, RNF-06 |
| INV-2 | Toda operação aceita que cria, altera ou muda estado tem ao menos um registro de auditoria, gravado na mesma transação. Operação recusada ou desfeita não deixa registro. | RB-01, RNF-09, ADR-004 |
| INV-3 | Todo registro de auditoria tem data e hora, operação e registro afetado, e tem usuário, salvo quando a operação é automática. | RF-62; modelo de domínio, relação 18 |
| INV-4 | Os registros são mantidos na ordem em que foram gravados. | UC-12, passo 2 |
| INV-5 | A gravação da auditoria fica em um único ponto da camada de aplicação. | ADR-004, decisão 3; RNF-19 |
| INV-6 | O domínio não importa aplicação, infraestrutura, framework, banco, canal de notificação nem serviço de IA. | ADR-001; RNF-19 |
| INV-7 | A suíte de testes roda sem credencial de serviço externo. | RNF-23 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um cliente cadastrado e o Operador Financeiro | ele cadastra um título | existe um registro com o usuário, a data e hora do relógio, a operação "cadastrar título" e o título como registro afetado, com o estado Aberto como novo valor | RF-04, RF-62, A1 |
| CA-02 | um título Aberto de R$ 100,00 | um pagamento de R$ 100,00 é registrado | existe um registro do pagamento e um registro da mudança de estado, com o campo estado, valor anterior Aberto e novo valor Baixado | RF-05, RF-61, A2 |
| CA-03 | um título Baixado por um pagamento | o Dono estorna o pagamento com o motivo "cheque devolvido" | existe um registro cujo registro afetado é o pagamento, com o campo estornado de "não" para "sim" e o motivo; e um registro da mudança de estado do título | RB-01, RF-05, A3, A5 |
| CA-04 | um título Baixado | um pagamento é solicitado e recusado | nenhum registro de auditoria é gravado | INV-2, E1 |
| CA-05 | um título Aberto | a gravação da auditoria falha durante um pagamento | nenhum pagamento é gravado, e saldo e estado não mudam | RNF-09, E2 |
| CA-06 | um título Aberto | a gravação do título falha depois de a auditoria ser gravada | nenhum registro de auditoria daquela operação permanece | RNF-09, E3 |
| CA-07 | um registro de auditoria gravado | qualquer chamador tenta alterar um de seus campos, inclusive pelo objeto devolvido na leitura | a alteração é recusada e o registro armazenado continua igual | RB-30, RNF-06, E4 |
| CA-08 | um registro de auditoria gravado | qualquer chamador tenta excluí-lo | não há operação de exclusão, e o registro continua armazenado | RB-30, RNF-06, E4 |
| CA-09 | um título Aberto com vencimento ontem | a verificação de vencimento é executada sem usuário | o título passa a Vencido, e o registro da mudança de estado não tem usuário, está identificado como automático e informa a rotina "verificação de vencimento" | INV-3, A4, OPEN-30 |
| CA-10 | uma operação em andamento | ocorre um erro que não é recusa de regra de negócio | existe um registro de erro com data e hora, operação, usuário e identificador de correlação; nenhuma alteração da operação permanece; e o erro chega a quem chamou | RNF-21, E5 |
| CA-11 | duas operações executadas em sequência | os registros são lidos | aparecem na ordem em que foram gravados | INV-4 |
| CA-12 | o código de `src/remindme/` | as importações de cada camada são verificadas | o domínio não importa aplicação nem infraestrutura, e a aplicação não importa infraestrutura | INV-6, RNF-19, ADR-001 |
| CA-13 | um ambiente sem nenhuma variável de credencial | a suíte inteira é executada | todos os testes passam | INV-7, RNF-23 |

Os testes automatizados levam no nome o identificador do critério ou da regra, por exemplo `test_CA_07_registro_gravado_nao_e_alterado` e `test_RB_30_...`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-02 | Banco de dados | Não. A persistência é em memória; os testes de contrato serão repetidos sobre o banco. |
| OPEN-30 | Como o registro de auditoria identifica uma operação automática, sem usuário? | Decidida em 2026-10-16 por João Pedro Guerra: usuário vazio e a indicação "automática" no registro, com o nome da rotina que disparou a operação. Não bloqueia mais. |
| OPEN-31 | Qual a política de retenção dos registros de auditoria? | Não. Nenhum registro é excluído nesta spec. |

## 8. Verificação

Verificada em 2026-10-16, com `python3 -m unittest discover -s tests -t .`: 235 testes, todos passando (9 pulados, pendentes de outras specs, e 1 falha esperada, o defeito conhecido de `tests/dominio/test_acuracia_monetaria.py`; nenhum dos dois é desta spec). Antes desta spec eram 199 testes. Testes em [`tests/aplicacao/test_spec_001_aceite.py`](../../tests/aplicacao/test_spec_001_aceite.py) (critérios), [`tests/dominio/test_auditoria.py`](../../tests/dominio/test_auditoria.py) (registro de auditoria) e [`tests/infraestrutura/test_memoria.py`](../../tests/infraestrutura/test_memoria.py) (auditoria em memória, registro de erros e unidade de trabalho). Plano em [`plans/001-plano.md`](../plans/001-plano.md). Executado em Python 3.11, 3.12 e 3.13, com o mesmo resultado.

### Critérios de aceitação

| Critério | Teste | Resultado |
|---|---|---|
| CA-01 | `test_CA_01_cadastro_de_titulo_gera_registro_com_estado_inicial` | Passou |
| CA-02 | `test_CA_02_pagamento_gera_registro_do_pagamento_e_da_mudanca_de_estado` | Passou |
| CA-03 | `test_CA_03_estorno_gera_registro_do_pagamento_e_da_mudanca_de_estado` | Passou |
| CA-04 | `test_CA_04_RB_01_pagamento_recusado_nao_grava_auditoria` | Passou |
| CA-05 | `test_CA_05_falha_na_auditoria_durante_o_pagamento_desfaz_tudo` (o primeiro registro é gravado e o segundo falha) | Passou |
| CA-06 | `test_CA_06` (2 testes: falha na gravação do segundo título depois da auditoria do primeiro, na verificação de vencimentos; falha na gravação do título no cadastro) | Passou |
| CA-07 | `test_CA_07` (3 testes: todos os campos, objeto lido com a imutabilidade contornada, objeto alterado depois de gravado) | Passou |
| CA-08 | `test_CA_08` (2 testes: porta, implementação e serviço sem alterar nem excluir; apagar a lista lida não exclui) | Passou |
| CA-09 | `test_CA_09` (2 testes: sem usuário, automática com a rotina "verificação de vencimento"; com usuário, não automática) | Passou |
| CA-10 | `test_CA_10` (5 testes: registro, desfazer e propagação; correlação própria por erro; operação automática; recusa não é erro; falha ao registrar o erro não esconde o original) | Passou |
| CA-11 | `test_CA_11_registros_aparecem_na_ordem_de_gravacao` | Passou |
| CA-12 | `test_CA_12_RNF_19_dominio_e_aplicacao_importam_somente_camadas_permitidas`; `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas` | Passou |
| CA-13 | `test_CA_13_RNF_23_suite_inteira_passa_sem_variavel_de_credencial` (a suíte roda em outro processo, só com `PATH` e variáveis mínimas do sistema); `test_RNF_23_codigo_nao_le_variaveis_de_ambiente` | Passou |

### Invariantes

| Invariante | Como foi verificada | Resultado |
|---|---|---|
| INV-1 | CA-07 e CA-08; `test_RB_30_nenhum_campo_do_registro_muda`; `test_RB_30_leitura_devolve_copias_em_lista_nova` | Passou |
| INV-2 | CA-01 a CA-06 e CA-10; os testes de recusa e de falha da Spec 006 (`test_confiabilidade.py`, `test_idempotencia.py`, `test_integracao.py`) continuam passando | Passou |
| INV-3 | `test_INV_3_*` e `test_OPEN_30_*` em `tests/dominio/test_auditoria.py`: o registro incompleto não é criado; CA-09 | Passou |
| INV-4 | CA-11; `test_ADR_004_registros_sao_acrescentados_em_ordem` | Passou |
| INV-5 | `test_INV_5_a_auditoria_e_gravada_em_um_unico_ponto_da_aplicacao`: só `aplicacao/auditoria.py` cria `RegistroAuditoria` ou chama `auditoria.registrar` | Passou |
| INV-6 | CA-12; `test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao` | Passou |
| INV-7 | CA-13 | Passou |

### Verificação de sensibilidade

Erros introduzidos de propósito, um de cada vez, e desfeitos em seguida. Em todos, a suíte falhou nos testes esperados e voltou a passar depois de desfeito o erro.

| Erro introduzido | Testes que falharam (amostra) |
|---|---|
| Gravar registro de auditoria quando a operação é recusada | CA-04 e 7 testes de recusa da Spec 006 |
| `RegistroAuditoria` sem `frozen` | CA-07, `test_RB_30_*`, `test_RNF_06_*` |
| Auditoria em memória devolvendo a própria lista e os próprios objetos | CA-07, CA-08, `test_ADR_004_a_lista_devolvida_...` |
| Unidade de trabalho que não desfaz em falha | CA-05, CA-06, CA-10 e os testes de RNF-09 da Spec 006 |
| Operação automática gravada com um usuário fictício | CA-09 |
| Erro não tratado sem registro | CA-10 |

### Divergências e limitações

| Item | Situação |
|---|---|
| Testes da Spec 006 ajustados | `test_UC_06_ciclo_completo_grava_estado_e_trilha_de_auditoria` (`tests/integracao/test_integracao.py`): o registro do estorno passou a ter o pagamento como registro afetado e "não" → "sim" no campo estornado (A5, CA-03). `test_ADR_004_provisorio_o_duble_em_memoria_expoe_a_lista_de_registros` (`tests/aplicacao/test_seguranca_de_acesso.py`) documentava a fragilidade S-01, que esta spec resolve; passou a se chamar `test_ADR_004_a_lista_devolvida_pela_auditoria_em_memoria_nao_altera_o_armazenado`. Nenhum outro teste mudou. |
| Destino do registro de erro e origem do identificador de correlação | Em aberto: **OPEN-36**. O registro passa pela porta `RegistroErros`, com implementação em memória; o identificador é gerado pela aplicação. |
| Porta de erros opcional | `ServicoTitulos` recebe `erros` como parâmetro opcional, para não mudar a criação do serviço nos testes da Spec 006. Sem a porta, o erro é desfeito e propagado, mas não registrado. |
| Consulta de títulos | Não altera dados, não é auditada e não recebe usuário; um erro nela não gera registro de erro. A consulta com usuário depende da Spec 002. |
| Operação do registro de mudança de estado | Continua "mudar estado", como na Spec 006, e não o nome da operação solicitada. A spec não fixa os nomes das operações. |
| CA-06 | A falha da gravação de um título depois de uma auditoria já gravada só acontece, na mesma operação, na verificação de vencimentos com dois títulos: nas demais operações, o título é gravado antes da auditoria. O teste usa dois títulos Abertos, e não um. A unidade de trabalho também é testada diretamente nessa ordem (`test_RNF_09_falha_desfaz_so_os_registros_da_transacao`). |
| Persistência | Em memória. A garantia de RB-30 no armazenamento real (por exemplo, permissão só de inclusão) depende de OPEN-02. |
| Glossário | "Registro de erro" e "identificador de correlação" não estão em `docs/glossario.md`; o código usa `RegistroErro` e `correlacao`. Proposta de inclusão no glossário, a aprovar. |
| ADR-004 | Continua "Proposto, aguardando aprovação" (DV-13), embora esta spec o implemente. |
| DV-05 | Tratada: a verificação de vencimento aceita usuário vazio, e o registro identifica a operação automática e a rotina (OPEN-30). |
| Nome dos testes | Python não aceita hífen em identificador: `CA-07` vira `test_CA_07_...`. |
