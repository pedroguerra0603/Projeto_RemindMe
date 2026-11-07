# Rastreabilidade — RemindMe

Issue #40. Este documento liga os requisitos aos drivers arquiteturais, às decisões técnicas, à implementação e aos testes. Ele mostra, para cada requisito, de onde ele vem e onde está a evidência de que foi atendido.

- **Data:** 2026-11-07.
- **Base:** `main` em `f9f2a01`, depois do PR #103, com as aprovações de 2026-11-07. A suíte tem 478 testes, todos passando, com 9 pulados (4 de navegador sem o Playwright, opcional, e 5 marcadores de testes ainda não escritos).
- **Fontes:** [requisitos](requisitos.md), [arquitetura](arquitetura.md), [ADRs](adr/README.md), [mapa de specs](../.specify/specs/mapa-de-specs.md), as [specs](../.specify/specs/) verificadas, [`src/`](../src/README.md), [`tests/`](../tests/README.md).
- **Complementa:** a [matriz de critérios de aceite](qualidade/matriz-criterios-de-aceite.md), que parte de cada critério da Spec 006 e chega ao teste, e a seção 8 de cada spec, que registra o teste de cada critério. Este documento parte do requisito e passa pelo driver e pela decisão.

## 1. Cadeia

```
Requisito (RF, RNF, RB) → Driver (DA) → Decisão (DT, ADR) → Spec → Código → Teste
```

O identificador é o elo da cadeia. Ele aparece no requisito, na spec, na docstring do código e no nome do teste. Por exemplo, a regra `RB-23` vira o teste `test_RB_23_recusa_pagamento_maior_que_o_saldo`. Os caminhos de código são relativos a `src/remindme/`.

### Como as tabelas foram montadas

1. Os requisitos ativos vêm de [`requisitos.md`](requisitos.md); os retirados (RF-60, RF-63, RF-69, RNF-10, RB-26) ficam de fora.
2. As specs de cada requisito vêm das colunas RF, RB e RNF do mapa. Um requisito está **Implementado** quando todas as specs que o citam estão Verificadas; **Parcial** quando só parte delas está; **Sem implementação** quando nenhuma está.
3. O código é a lista de módulos que citam o identificador; os testes são as funções cujo nome contém o identificador (`test_*RF_24*`) e os arquivos de teste das specs verificadas (`test_spec_NNN_*`).
4. A situação foi corrigida à mão quando a regra do item 2 não refletia o código, com o motivo na própria linha: RB-01, RB-21, RF-61, RNF-23 (parciais), RNF-11, RNF-25 (parciais, ver lacuna 4) e RF-28, RF-29 (sem implementação, ver lacuna 3).

## 2. Drivers → decisões → implementação → testes

Os dez drivers de [`arquitetura.md`](arquitetura.md#2-drivers-arquiteturais), com a decisão que responde a cada um e a evidência no código.

| Driver | Requisitos de origem | Decisão | Specs | Implementação | Testes | Situação |
|---|---|---|---|---|---|---|
| DA-01 — Transições de estado são invariantes de domínio | RB-21, RB-05, RB-22, RF-12, RF-24 | DT-01, ADR-001 | 004, 006, 018; 005, 009, 010 | `dominio/titulo.py`, `dominio/orcamento.py`, `dominio/conta_pagar.py`: estados e transições nos próprios objetos | `test_RB_21_*`, `test_RB_31_*`, `tests/dominio/test_orcamento.py`, `test_INV_*` | Parcial: título (sem Em Renegociação), orçamento até o envio e conta a pagar. Conversão em título (005) e obrigação (010) pendentes |
| DA-02 — Toda mudança de estado é auditada, e a auditoria é imutável | RB-01, RB-30, RNF-06 | DT-04, ADR-004 | 001, 013 e todas as que alteram dados | `dominio/auditoria.py` (`RegistroAuditoria` imutável); `aplicacao/auditoria.py`; `infraestrutura/sqlite.py` (triggers que recusam alterar e excluir) | `test_RB_01_*`, `test_RB_30_*`, aceite das Specs 001 e 013 | Implementado para as entidades que existem |
| DA-03 — Operações financeiras são atômicas | RNF-09, RB-19 | DT-05 | 001, 006, 018, 019; 005, 015 | `infraestrutura/sqlite.py`: uma transação por operação, com `BEGIN IMMEDIATE`; `infraestrutura/memoria.py` para os testes | `test_RNF_09_*`, `test_CA_23_falha_na_auditoria_desfaz_o_pagamento`, `tests/integracao/` | Implementado; o teste de concorrência real continua como marcador (lacuna 5) |
| DA-04 — Acesso negado por padrão; o cliente não acessa o sistema (OPEN-57) | RNF-02, RNF-03, RNF-25, RB-03 | DT-06 | 002, 017, 018 | `dominio/permissoes.py` (matriz perfil × operação); `aplicacao/acesso.py`, chamado pelo serviço antes do domínio | `test_RNF_02_*`, `test_RNF_03_*`, `test_RB_03_*`, aceite da Spec 002 | Implementado |
| DA-05 — Processamento por tempo não degrada o uso interativo | RF-24, RF-33, RF-34, RF-44, RF-48, RNF-12, RNF-13 | DT-07 | 006, 017, 018; 008, 010 | `entradas/agendador.py` (`AgendadorDeVencimentos`, na inicialização e a cada hora, OPEN-48) | `test_RF_24_*`, `test_RF_90_*`; lote de vencimentos medido em [eficiência](qualidade/eficiencia.md) | Parcial: vencimento de títulos e contas a pagar. Régua (008) e obrigações (010) pendentes |
| DA-06 — A IA é falível e nunca decide | RB-08, RB-14, RB-17, RB-27, RNF-24 | DT-03, ADR-003 | 009, 011 | — | — | Pendente |
| DA-07 — A suíte roda sem credencial externa | RNF-23, RB-18 | DT-02, ADR-002 | 001; 005, 008 | Somente a biblioteca padrão; nenhuma variável de credencial | `test_OPEN_01_codigo_usa_somente_a_biblioteca_padrao`; a suíte inteira | Parcial: os simuladores de canal e de IA vêm com as Specs 008, 009 e 011 |
| DA-08 — A régua não repete etapa para o mesmo título | UC-08, RF-35 | DT-08 | 008 | — | `test_DA_08_*` (marcador pulado) | Pendente |
| DA-09 — Cada regra em um único ponto, com teste nomeado | RNF-19 | DT-01 | Todas | Regras em `dominio/`; a apresentação não as reimplementa | `test_RNF_19_regras_do_titulo_ficam_somente_no_dominio`, `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas`, `test_INV_1_a_apresentacao_nao_usa_regras_do_dominio_diretamente` | Implementado |
| DA-10 — Configuração alterada não reescreve o passado | RNF-18, RF-36 | DT-09 | 007, 014 | — | — | Pendente |

## 3. Requisitos implementados → código → testes

Requisitos com situação Implementado ou Parcial. "Specs" lista só as verificadas.

| Requisito | Specs | Código | Testes | Situação |
|---|---|---|---|---|
| RF-01 | 003, 017 | `aplicacao/servico_clientes.py`; `dominio/cliente.py` | testes da Spec 003, Spec 017 | Implementado |
| RF-02 | 002, 017 | `aplicacao/servico_acesso.py`; `dominio/usuario.py` | `test_*RF_02*` (1); testes da Spec 002, Spec 017 | Implementado |
| RF-03 | 002, 017 | `aplicacao/acesso.py`; `aplicacao/servico_acesso.py`; `dominio/permissoes.py` | `test_*RF_03*` (2); testes da Spec 002, Spec 017 | Parcial. Falta a parte da Spec 014 |
| RF-04 | 001 | — | testes da Spec 001 | Implementado |
| RF-05 | 001 | `aplicacao/auditoria.py`; `aplicacao/servico_acesso.py`; `aplicacao/servico_clientes.py` … | `test_*RF_05*` (2); testes da Spec 001 | Implementado |
| RF-65 | 002, 017 | `aplicacao/servico_acesso.py`; `apresentacao/web/aplicacao_web.py`; `dominio/permissoes.py` | `test_*RF_65*` (2); testes da Spec 002, Spec 017 | Implementado |
| RF-66 | 002, 017 | `aplicacao/servico_acesso.py`; `apresentacao/web/aplicacao_web.py` | `test_*RF_66*` (2); testes da Spec 002, Spec 017 | Implementado |
| RF-67 | 002, 017 | `aplicacao/servico_acesso.py`; `dominio/erros.py`; `dominio/permissoes.py` | `test_*RF_67*` (3); testes da Spec 002, Spec 017 | Implementado |
| RF-95 | 019 | `aplicacao/servico_acesso.py`; `apresentacao/web/aplicacao_web.py`; `apresentacao/web/paginas.py` | testes da Spec 019 | Implementado |
| RF-96 | 019 | `aplicacao/servico_acesso.py` | testes da Spec 019 | Implementado |
| RF-06 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_06*` (2); testes da Spec 004 | Implementado |
| RF-07 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_07*` (4); testes da Spec 004 | Implementado |
| RF-10 | 004 | `aplicacao/servico_orcamentos.py` | `test_*RF_10*` (1); testes da Spec 004 | Implementado |
| RF-13 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_13*` (3); testes da Spec 004 | Implementado |
| RF-14 | 004 | `dominio/orcamento.py` | testes da Spec 004 | Parcial. Falta a parte da Spec 014 |
| RF-15 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_15*` (1); testes da Spec 004 | Implementado |
| RF-16 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_16*` (2); testes da Spec 004 | Implementado |
| RF-17 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_17*` (2); testes da Spec 004 | Implementado |
| RF-18 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py` | `test_*RF_18*` (1); testes da Spec 004 | Implementado |
| RF-20 | 006, 017 | `dominio/titulo.py` | `test_*RF_20*` (2); testes da Spec 006, Spec 017 | Implementado |
| RF-21 | 006, 017 | `dominio/titulo.py` | `test_*RF_21*` (1); testes da Spec 006, Spec 017 | Implementado |
| RF-22 | 006, 017 | `aplicacao/servico_titulos.py` | `test_*RF_22*` (1); testes da Spec 006, Spec 017 | Implementado |
| RF-23 | 006, 017 | `dominio/titulo.py` | `test_*RF_23*` (4); testes da Spec 006, Spec 017 | Parcial. Falta a parte da Spec 014 |
| RF-24 | 006, 017 | `dominio/titulo.py`; `entradas/agendador.py` | `test_*RF_24*` (14); testes da Spec 006, Spec 017 | Implementado |
| RF-25 | 006, 017 | `apresentacao/web/graficos.py`; `dominio/titulo.py` | `test_*RF_25*` (6); testes da Spec 006, Spec 017 | Implementado |
| RF-26 | 006, 017 | `dominio/titulo.py` | testes da Spec 006, Spec 017 | Implementado |
| RF-27 | 006, 017 | `dominio/titulo.py` | `test_*RF_27*` (2); testes da Spec 006, Spec 017 | Implementado |
| RF-30 | 006, 017 | `dominio/titulo.py` | `test_*RF_30*` (6); testes da Spec 006, Spec 017 | Implementado |
| RF-31 | 006, 017 | `dominio/titulo.py` | `test_*RF_31*` (1); testes da Spec 006, Spec 017 | Implementado |
| RF-68 | 006 | — | testes da Spec 006 | Implementado |
| RF-61 | 001 | — | testes da Spec 001 | Parcial. Orçamento, título e pagamento; obrigação e lançamento dependem das Specs 010 e 011 |
| RF-62 | 001 | `dominio/auditoria.py` | `test_*RF_62*` (1); testes da Spec 001 | Implementado |
| RF-64 | 013, 017 | `aplicacao/servico_auditoria.py` | testes da Spec 013, Spec 017 | Implementado |
| RF-87 | 018 | `aplicacao/servico_fornecedores.py`; `dominio/fornecedor.py` | testes da Spec 018 | Implementado |
| RF-88 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py` | `test_*RF_88*` (1); testes da Spec 018 | Implementado |
| RF-89 | 018 | `aplicacao/servico_contas_pagar.py` | `test_*RF_89*` (1); testes da Spec 018 | Implementado |
| RF-90 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py`; `entradas/agendador.py` | `test_*RF_90*` (1); testes da Spec 018 | Implementado |
| RF-91 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py` | testes da Spec 018 | Implementado |
| RF-92 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py` | `test_*RF_92*` (1); testes da Spec 018 | Implementado |
| RF-93 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py` | `test_*RF_93*` (1); testes da Spec 018 | Implementado |
| RF-94 | 018 | `apresentacao/web/paginas.py` | testes da Spec 018 | Implementado |
| RNF-01 | 002, 017, 019 | `aplicacao/acesso.py`; `apresentacao/web/aplicacao_web.py` | `test_*RNF_01*` (3); testes da Spec 002, Spec 017, Spec 019 | Implementado |
| RNF-02 | 002, 017, 018 | `aplicacao/acesso.py`; `dominio/erros.py`; `dominio/permissoes.py` | `test_*RNF_02*` (8); testes da Spec 002, Spec 017, Spec 018 | Implementado |
| RNF-03 | 002, 004, 017 | — | `test_*RNF_03*` (4); testes da Spec 002, Spec 004, Spec 017 | Implementado |
| RNF-04 | 002, 019 | `aplicacao/portas.py`; `aplicacao/senhas.py`; `aplicacao/servico_acesso.py` | `test_*RNF_04*` (1); testes da Spec 002, Spec 019 | Implementado |
| RNF-05 | 002, 017 | `inicializacao.py` | `test_*RNF_05*` (2); testes da Spec 002, Spec 017 | Implementado |
| RNF-06 | 001, 013, 017 | `aplicacao/portas.py`; `infraestrutura/sqlite.py` | `test_*RNF_06*` (3); testes da Spec 001, Spec 013, Spec 017 | Implementado |
| RNF-25 | — | — | `test_*RNF_25*` (2) | Parcial. A recusa por perfil não revela dados do título; a resposta a mensagens de cliente é da Spec 009 |
| RNF-09 | 001, 006, 017, 018, 019 | `aplicacao/portas.py`; `aplicacao/servico_acesso.py`; `infraestrutura/memoria.py` … | `test_*RNF_09*` (14); testes da Spec 001, Spec 006, Spec 017, Spec 018, Spec 019 | Parcial. Falta a parte das Specs 005, 015 |
| RNF-11 | — | — | `test_*RNF_11*` (3) | Parcial. Medido para cadastro, consulta, pagamento e cancelamento; o mapa o atribui só à Spec 012 |
| RNF-14 | 003, 017, 018, 019 | `apresentacao/web/aplicacao_web.py`; `dominio/cliente.py`; `dominio/empresa.py` … | `test_*RNF_14*` (10); testes da Spec 003, Spec 017, Spec 018, Spec 019 | Implementado |
| RNF-15 | 018 | — | `test_*RNF_15*` (1); testes da Spec 018 | Parcial. Falta a parte das Specs 010, 016 |
| RNF-16 | 017 | `aplicacao/servico_titulos.py` | testes da Spec 017 | Parcial. Falta a parte da Spec 016 |
| RNF-19 | 001, 006 | `dominio/regras.py` | `test_*RNF_19*` (1); testes da Spec 001, Spec 006 | Implementado |
| RNF-21 | 001, 017 | `__init__.py`; `aplicacao/auditoria.py`; `aplicacao/portas.py` … | `test_*RNF_21*` (1); testes da Spec 001, Spec 017 | Implementado |
| RNF-23 | 001 | — | testes da Spec 001 | Parcial. A suíte roda sem credencial; os simuladores de canal e de IA vêm com as Specs 008, 009 e 011 |
| RB-01 | 001, 006 | — | `test_*RB_01*` (4); testes da Spec 001, Spec 006 | Parcial. Orçamento, título e pagamento; obrigação e lançamento dependem das Specs 010 e 011 |
| RB-02 | 006 | `dominio/regras.py`; `dominio/titulo.py` | `test_*RB_02*` (4); testes da Spec 006 | Implementado |
| RB-03 | 002 | `dominio/regras.py` | `test_*RB_03*` (7); testes da Spec 002 | Implementado |
| RB-15 | 004 | `aplicacao/servico_orcamentos.py`; `dominio/orcamento.py`; `dominio/regras.py` | `test_*RB_15*` (7); testes da Spec 004 | Implementado |
| RB-21 | 006 | `dominio/titulo.py` | `test_*RB_21*` (11); testes da Spec 006 | Parcial. Sem o estado Em Renegociação (Spec 009) |
| RB-22 | 006 | `dominio/titulo.py` | `test_*RB_22*` (5); testes da Spec 006 | Implementado |
| RB-23 | 006 | `dominio/titulo.py` | `test_*RB_23*` (12); testes da Spec 006 | Implementado |
| RB-24 | 004 | `apresentacao/web/paginas.py`; `dominio/orcamento.py` | `test_*RB_24*` (2); testes da Spec 004 | Implementado |
| RB-30 | 001, 013 | `aplicacao/portas.py`; `aplicacao/servico_auditoria.py`; `dominio/auditoria.py` … | `test_*RB_30*` (6); testes da Spec 001, Spec 013 | Implementado |
| RB-31 | 018 | `dominio/conta_pagar.py` | `test_*RB_31*` (3); testes da Spec 018 | Implementado |
| RB-32 | 018 | `dominio/conta_pagar.py` | `test_*RB_32*` (1); testes da Spec 018 | Implementado |
| RB-33 | 018 | `aplicacao/servico_contas_pagar.py`; `dominio/conta_pagar.py`; `dominio/permissoes.py` … | `test_*RB_33*` (1); testes da Spec 018 | Implementado |

## 4. Requisitos ainda sem implementação

Todo requisito ativo aparece em ao menos uma spec do mapa, exceto RNF-07 e RNF-08, que são operacionais. Os requisitos abaixo seguem pela spec indicada; um requisito pode aparecer em mais de uma.

| Spec | Requisitos | Situação da spec |
|---|---|---|
| 005 | RF-08, RF-09, RF-11, RF-12, RF-19, RB-05, RB-18 | A escrever |
| 007 | RF-32, RF-36, RNF-18, RNF-20, RB-10 | A escrever |
| 008 | RF-33, RF-34, RF-35, RF-37, RF-38, RF-39, RF-70, RF-71, RNF-12, RNF-13, RB-10, RB-11, RB-18 | A escrever |
| 009 | RF-28, RF-29, RF-72, RF-73, RF-74, RF-75, RF-76, RNF-22, RNF-24, RB-11, RB-17, RB-20, RB-27, RB-28 | A escrever |
| 010 | RF-40, RF-41, RF-42, RF-43, RF-44, RF-45, RF-46, RF-47, RF-48, RF-49, RF-50, RF-77, RB-04, RB-07, RB-13, RB-16, RB-29 | A escrever |
| 011 | RF-51, RF-52, RF-58, RF-59, RF-78, RF-79, RF-80, RF-81, RF-86, RNF-22, RNF-24, RNF-26, RB-08, RB-09, RB-12, RB-14, RB-27 | A escrever |
| 012 | RF-53, RF-54, RF-55, RF-56, RF-57, RF-82, RB-06, RB-12 | A escrever |
| 014 | RNF-18, RNF-20, RB-07, RB-08, RB-16, RB-28 | A escrever |
| 015 | RF-83, RF-84, RF-85, RB-19 | A escrever |
| 016 | RNF-17, RB-13 | A escrever |
| Operacionais | RNF-07, RNF-08 | Sem spec; na execução local da apresentação (OPEN-12) não há como medir disponibilidade mensal nem rotina de backup |

### Cobertura

| Tipo | Ativos | Implementados | Parciais | Sem implementação | Operacionais |
|---|---|---|---|---|---|
| RF | 93 | 37 | 4 | 52 | — |
| RB | 31 | 10 | 2 | 19 | — |
| RNF | 25 | 9 | 6 | 8 | 2 |
| **Total** | **149** | **56** | **12** | **79** | **2** |
| Drivers | 10 | 4 (DA-02, DA-03, DA-04, DA-09) | 3 (DA-01, DA-05, DA-07) | 3 (DA-06, DA-08, DA-10) | — |

DA-03 conta como implementado, embora o teste de concorrência real ainda seja um marcador (lacuna 5).

## 5. Lacunas encontradas

| # | Lacuna | Tratamento |
|---|---|---|
| 1 | RF-23 fala em "número de dias configurado", mas nenhuma spec verificada configura essa antecedência | Resolvida por OPEN-21 e OPEN-37: parâmetro da Spec 014, com padrão de 5 dias até lá. RF-23 segue Parcial |
| 2 | RF-31 exigia motivo para "alteração de valor", operação que não existe | Resolvida por OPEN-22: o valor do título não muda depois de criado |
| 3 | A linha da Spec 017 no mapa cita "Telas de … RF-20 a RF-31", o que inclui RF-28 e RF-29 (renegociação). A renegociação não existe; eles seguem pela Spec 009 | Proposta: corrigir a linha da 017 no mapa para RF-20 a RF-27, RF-30 e RF-31 |
| 4 | RNF-11 e RNF-25 têm testes que passam, mas o mapa os atribui só a specs futuras (012 e 009) | Proposta: incluir RNF-11 nas linhas 006 e 017, e RNF-25 na linha 002 do mapa |
| 5 | Dois marcadores pulados já podiam ser testes: `test_RB_15_desconto_percentual_nao_perde_centavos` ("pendente da Spec 004", verificada) e `test_RNF_09_duas_transacoes_simultaneas_no_mesmo_titulo_nao_estouram_o_saldo` ("pendente de OPEN-02", decidida; o SQLite existe) | Escrever os dois testes |
| 6 | RB-02 diz "somente o Dono estorna", mas o Administrador também estorna (OPEN-53); RB-33 já cita a exceção | Proposta: reescrever RB-02 e RB-15 com a exceção do Administrador |
| 7 | 70 das 474 funções de teste não levam identificador no nome, contra o princípio 2 de [`testes.md`](testes.md). São, em geral, testes de infraestrutura, de integração, de contrato e de interface | Registrado em [divergências](qualidade/divergencias.md), DV-14, ainda em proposta |

As divergências entre código, spec e baseline estão em [`qualidade/divergencias.md`](qualidade/divergencias.md).

## 6. Como manter

1. Requisito novo ou alterado: atualizar a linha da spec no mapa e, se ele pesar na estrutura, a tabela de drivers da arquitetura.
2. Spec aprovada e implementada: mover seus requisitos da seção 4 para a seção 3, com código e testes.
3. Teste novo de regra: nomear pelo identificador (`test_RB_nn_...`, `test_CA_nn_...`), para que o elo apareça numa busca por texto.
4. Para refazer as seções 3 e 4, aplicar o método da seção 1 sobre o mapa, `src/` e `tests/`, e revisar à mão as linhas com ajuste.
