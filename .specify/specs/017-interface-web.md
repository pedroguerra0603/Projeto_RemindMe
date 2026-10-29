# Spec 017 — Interface web e persistência

## 1. Identificação

| | |
|---|---|
| **ID** | 017 |
| **Nome** | Interface web e persistência |
| **Objetivo** | Tornar operáveis pelo navegador as Specs 001, 002, 003 e 006, com os dados guardados em banco. |
| **Valor entregue** | A Dona entra no sistema e vê no painel o que está vencido e o que vence nos próximos dias; o Operador cadastra clientes e títulos e registra pagamentos; o Contador consulta; o Administrador mantém usuários e permissões. |
| **Situação** | Proposta — implementada em 2026-10-29 por pedido de Renan Gandolpho; aguarda aprovação da equipe |
| **Aprovada por** | *(nomes e data)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-22, RF-23, RF-24 (agendador), RF-64, RF-65, RF-66, RF-67 |
| RNF | RNF-01, RNF-02, RNF-03, RNF-14, RNF-15, RNF-16, RNF-17 (parcial), RNF-21 |
| UC | UC-01, UC-02, UC-03, UC-06, UC-12 (consulta básica) |
| Drivers e ADRs | DA-02, DA-03, DA-04, DA-05; DT-05, DT-06, DT-07; ADR-001, ADR-004 |
| Depende de | 001, 002, 003, 006. Decisões OPEN-01 (framework), OPEN-02, OPEN-13, OPEN-26, tomadas em 2026-10-29 |

## 3. Escopo

### Incluído

- Persistência em SQLite (OPEN-02), com transação por caso de uso e auditoria protegida contra alteração e exclusão por gatilhos do banco.
- Servidor web WSGI da biblioteca padrão, sem framework externo (OPEN-01).
- Telas: login e saída; painel por perfil; títulos (lista com filtros, cadastro, detalhe, pagamento, estorno, cancelamento, verificação de vencimentos); clientes; auditoria com filtros; usuários; matriz de permissões.
- Verificação automática de vencimentos por tarefa periódica no próprio processo (OPEN-13), registrada como operação automática (OPEN-30).
- Linha de comando: `servir`, `criar-admin` e `demo`.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| HTTPS (RNF-05) | Hospedagem (OPEN-12): o servidor roda atrás de um proxy com TLS; `--https` marca os cookies como `Secure` |
| Painel com obrigações e cobranças (RNF-17 completo) | Specs 008, 010 e 016 |
| Orçamentos, régua, obrigações, lançamentos, CSV | Specs 004, 005, 007 a 012, 015 |

## 4. Comportamento

- Toda página, exceto o login, exige sessão; sem sessão, o navegador vai para o login (RNF-01).
- A interface não decide nada: converte a entrada, chama `Sistema`, que autoriza (Spec 002, INV-5) e executa, e apresenta o resultado ou o motivo da recusa (RF-67, RNF-14).
- O menu e os botões mostram só o que o perfil pode fazer (RF-65); a verificação real fica no servidor (RNF-03).
- Todo formulário que altera dados leva um token anti-CSRF ligado à sessão.
- Valores em reais aceitam `1.234,56`; com mais de duas casas ou mais de 15 dígitos inteiros, a interface recusa com o campo e o motivo (provisório, OPEN-20 e OPEN-24).
- O painel destaca títulos Vencidos e próximos do vencimento (RNF-15), e cada tela de título mostra o estado (RNF-16).

## 5. Invariantes

| ID | Invariante |
|---|---|
| INV-1 | Nenhuma regra de negócio na camada de apresentação (ADR-001). |
| INV-2 | Todo texto vindo de dado é escapado no HTML. |
| INV-3 | O código não lê variável de ambiente nem credencial (Spec 001, CA-13); a configuração vem da linha de comando. |

## 6. Critérios de aceitação

| ID | Critério | Teste (`tests/apresentacao/test_web.py`) |
|---|---|---|
| CA-01 | Toda rota protegida sem sessão redireciona para o login | `test_RNF_01_toda_rota_exige_sessao` |
| CA-02 | Login inválido não revela o campo; válido abre o painel | `test_login_valido_abre_o_painel_e_invalido_nao_diz_o_campo` |
| CA-03 | O menu do Contador não mostra Usuários nem "Novo título" | `test_RF_65_menu_mostra_somente_o_que_o_perfil_pode` |
| CA-04 | Página negada mostra o motivo, com status 403 | `test_RF_67_negacao_mostra_o_motivo` |
| CA-05 | Formulário sem token CSRF é recusado e nada muda | `test_post_sem_csrf_e_recusado` |
| CA-06 | Cadastro de título e pagamento integral levam o título a Baixado | `test_fluxo_titulo_pagamento_e_baixa` |
| CA-07 | Formulário inválido informa campo e motivo | `test_RNF_14_formulario_invalido_informa_campo_e_motivo` |
| CA-08 | Recusa de regra de negócio volta à página com o motivo | `test_recusa_de_negocio_volta_com_o_motivo` |
| CA-09 | Texto do usuário é escapado | `test_texto_do_usuario_e_escapado` |
| CA-10 | Cabeçalhos de segurança e cookie `HttpOnly`, `SameSite=Lax` | `test_cabecalhos_de_seguranca_e_cookie_httponly` |
| CA-11 | Auditoria não é alterada nem excluída no banco | `tests/infraestrutura/test_sqlite.py`, `test_RNF_06_*` |
| CA-12 | Repositório SQLite cumpre o contrato de `RepositorioTitulos` | `RepositorioSQLiteCumpreOContrato` |

## 7. Questões em aberto

OPEN-01 (framework), OPEN-02, OPEN-13, OPEN-21, OPEN-26 e OPEN-36 foram decididas ou adotadas provisoriamente em 2026-10-29 e aguardam a confirmação da equipe, em [`open.md`](../open.md). OPEN-12 (hospedagem) continua aberta.

## 8. Verificação

Todos os critérios passaram em 2026-10-29 (`python3 -m unittest discover -s tests -t .`: 268 testes). O fluxo completo também foi percorrido num navegador real (Chromium), em tela de computador e de celular, com os quatro perfis dos dados de demonstração.
