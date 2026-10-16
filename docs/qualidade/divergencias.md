# Registro de Divergências — RemindMe

Issue #57. Comparação entre o código, a Spec 006 e a baseline (`docs/`), com as inconsistências encontradas e o tratamento de cada uma.

- **Data:** 2026-10-16.
- **Base:** `main` em `4b4ef09`.
- **Comparado:** `src/remindme/` × [Spec 006](../../.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) e [plano](../../.specify/plans/006-plano.md) × [requisitos](../requisitos.md), [estados](../uml/estados.md), [modelo de domínio](../modelo-dominio.md), [UC-06](../casos-de-uso/UC-06-registrar-pagamento-e-baixar-titulo.md), [sequência do UC-06](../uml/seq-UC-06.mmd), [arquitetura](../arquitetura.md), [mapa de specs](../../.specify/specs/mapa-de-specs.md) e demais documentos que descrevem a situação do projeto.
- **Regra seguida:** o [`CLAUDE.md`](../../CLAUDE.md), na seção "Durante a implementação". Onde código, spec e baseline discordam e a decisão é da equipe, a divergência virou `OPEN-nn` ou proposta. Nada foi alterado na baseline para acomodar o código. Só foram corrigidos documentos que contradiziam uma decisão já tomada e registrada.

## 1. Divergências

| ID | Artefatos | Divergência | Evidência | Tratamento |
|---|---|---|---|---|
| DV-01 | Spec 006 (A4) × `estados.md` × código | A4 diz que, depois do estorno, o título vai para Aberto ou Vencido conforme o vencimento, sem restringir o estado de partida. A tabela de estados só prevê essa transição a partir de Baixado. O código segue a tabela: um título Aberto com vencimento passado continua Aberto depois de um estorno parcial | Cenário C-09 em [funcionalidade](funcionalidade.md): título de R$ 100,00 vencido há 3 dias, ainda não verificado, pagamento de R$ 40,00 estornado → saldo R$ 100,00, estado Aberto | **OPEN-23.** Comportamento mantido até a decisão |
| DV-02 | `requisitos.md` (RF-31) × Spec 006 (INV-5) | RF-31, na seção de títulos, exige motivo para "alteração de valor". Nenhum RF descreve essa alteração, e a Spec 006 diz que o valor do título não muda depois de criado | — | **OPEN-22** |
| DV-03 | `requisitos.md` (RF-23) × mapa × UC-13 × código | RF-23 usa uma antecedência "configurada". Nenhum RF, caso de uso ou spec a configura. O UC-13 lista só a antecedência de aviso das obrigações. `ServicoTitulos.consultar_titulos` recebe o valor como parâmetro, e a docstring atribui a configuração à Spec 014, que não a inclui | `aplicacao/servico_titulos.py`, docstring de `consultar_titulos`; linha 014 do mapa | **OPEN-21** |
| DV-04 | Código e glossário × personas, visão e README | `Perfil` tem cinco valores, com Administrador, e o glossário também lista cinco. As personas, a visão e o README falam em quatro perfis | `dominio/usuario.py`; `test_perfis_sao_os_cinco_da_baseline` | Já coberta por **OPEN-10**. Nenhuma regra da Spec 006 depende do Administrador. Nada alterado |
| DV-05 | Modelo de domínio × código | O modelo diz que um registro de auditoria tem zero ou um usuário, porque "operações automáticas do sistema não têm usuário". `verificar_vencimentos` exige um `Usuario`, e `RegistroAuditoria.usuario_id` é obrigatório | Modelo de domínio, relação 18; `ServicoTitulos.verificar_vencimentos` | Pendente. A Spec 008, que cria o disparo automático, e a Spec 001, da auditoria, devem definir o responsável da operação automática |
| DV-06 | Sequência do UC-06 × DA-01 × código | No diagrama, o serviço de aplicação muda o estado do título para Baixado (`App->>Tit: estado Baixado`). Pelo DA-01, a transição é do domínio, e o código faz assim: `Titulo.registrar_pagamento` baixa o título | `docs/uml/seq-UC-06.mmd`; `dominio/titulo.py` | **Proposta à equipe:** mostrar a baixa como resultado de `Titulo.registrarPagamento`. O diagrama não foi alterado (regra 4) |
| DV-07 | Modelo de domínio × DT-06 × código | A seção 3 do modelo põe o estorno em `Pagamento.estornar()`, com "só o Dono executa (RB-02)" dentro da operação. O DT-06 manda verificar a autorização na aplicação. O código tem `Titulo.estornar_pagamento`, e RB-02 fica em `dominio/regras.py`, chamada pelo serviço antes do domínio | `docs/modelo-dominio.md`, seção 3; `dominio/regras.py` | **Proposta à equipe:** registrar a operação em `Titulo` e a verificação de RB-02 na aplicação. O modelo não foi alterado (regra 4) |
| DV-08 | Plano da Spec 006 × código | O plano diz "valores monetários em `Decimal`, com duas casas". O código aceita R$ 0,001, e o saldo passa a ter três casas | `test_E1_valor_com_mais_de_duas_casas_e_aceito_ate_decisao_de_OPEN_20` | Já registrada como **OPEN-20** |
| DV-09 | Mapa de specs × Spec 006 | A linha da Spec 006 no mapa não listava RB-01, que a spec cobre (seção 2, INV-6, INV-7, CA-22) | Mapa, linha 006 | **Corrigido** neste PR: RB-01 incluída na linha |
| DV-10 | UC-06 × Spec 006 | O UC-06 aceita pagamento em título Em Renegociação, cancela os envios da régua (RF-37) e gera o lançamento (RF-51). A Spec 006 não faz nada disso | Seção 3 da Spec 006, "Fora do escopo" | Escopo declarado na spec: Specs 008, 009 e 011. Nada a fazer |
| DV-11 | RF-20, RF-25 e RB-03 × código | Os RF exigem "usuário autorizado", e RB-03 proíbe o Contador de criar ou alterar registros. Hoje o Contador cadastra título e registra pagamento | Cenários C-07 e C-08 em [funcionalidade](funcionalidade.md) | Já registrada na seção 8 da Spec 006. Depende da Spec 002 |
| DV-12 | README, `testes.md` e `arquitetura.md` × OPEN-01 e Spec 006 | Esses documentos diziam que não há código e que nenhuma tecnologia foi escolhida. OPEN-01 foi decidida em 2026-10-03, e a Spec 006 está implementada e verificada | README: "sem código"; `testes.md`: "O projeto ainda não tem código"; `arquitetura.md`, seção 5: OPEN-01 "ainda não decidida" | **Corrigido** em #59 (seção 4) |
| DV-13 | ADR-001 a ADR-004 e mapa × Spec 006 e `CLAUDE.md` | Os quatro ADRs e o mapa estão "Proposto, aguardando aprovação". Mesmo assim, a Spec 006 foi aprovada e implementada sobre o ADR-001, e o `CLAUDE.md` (regras 9 e 10) trata ADR-001 e ADR-003 como regra | `docs/adr/README.md`; mapa, "Situação do mapa" | **Decisão da equipe:** aprovar ou revisar os ADRs e o mapa, e registrar a aprovação. Nada alterado |
| DV-14 | `testes.md` (princípio 2) × `tests/` | 20 dos 132 testes não levam identificador no nome: 7 de `infraestrutura/`, 8 de `integracao/`, 4 de `dominio/test_unidades.py` e 1 de `aplicacao/test_excecoes.py`. Testam infraestrutura, contrato do repositório e objetos auxiliares, e não uma regra | `grep -rhoE "def test_[a-z]" tests` | **Proposta à equipe:** aceitar a exceção para testes que não verificam regra nem critério, e registrá-la em `testes.md`; ou renomear os testes |
| DV-15 | RF-24 × código | RF-24 diz que o título passa a Vencido quando o vencimento passa. O código só muda o estado quando `verificar_vencimentos` é chamada. Até lá, a consulta mostra Aberto um título já vencido, sem a sinalização de próximo do vencimento | `ServicoTitulos.verificar_vencimentos`; docstring "O disparo periódico é da Spec 008" | Escopo declarado: o disparo periódico é da Spec 008 (OPEN-13). Nada a fazer agora; a Spec 008 deve cobrir este caso |

## 2. Divergências já registradas antes desta análise

Não foram repetidas na tabela acima.

| Item | Onde está |
|---|---|
| Data do pagamento sem restrição | OPEN-17 |
| Estorno em título Cancelado recusado provisoriamente | OPEN-18 |
| Filtro "período" aplicado ao vencimento | OPEN-19 |
| Auditoria por interface, antes da Spec 001; persistência em memória; Em Renegociação fora de `EstadoTitulo`; nome dos testes sem hífen | Seção 8 da Spec 006, "Divergências e limitações" |
| Defeitos D-01 a D-05, de validação de entrada | [Defeitos](defeitos.md) |
| Estado e valor do título alteráveis por atribuição direta (M-01) | [Manutenibilidade](manutenibilidade.md) |

## 3. Resumo

| Tratamento | Divergências |
|---|---|
| Nova questão em aberto | DV-01 (OPEN-23), DV-02 (OPEN-22), DV-03 (OPEN-21) |
| Questão em aberto já existente | DV-04 (OPEN-10), DV-08 (OPEN-20) |
| Proposta à equipe, sem alteração | DV-06, DV-07, DV-13, DV-14 |
| Pendente de spec futura | DV-05, DV-11, DV-15 |
| Escopo declarado, nada a fazer | DV-10 |
| Corrigido neste PR | DV-09, DV-12 |

Nenhuma divergência exigiu mudança de código. Em nenhum caso o código contraria a spec sem que a própria spec ou a baseline deixe a questão em aberto. O caso mais próximo é DV-01, em que a redação de A4 e a tabela de estados discordam entre si.
