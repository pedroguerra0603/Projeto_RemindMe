# Revisão de Qualidade do Código — RemindMe

Issue #71. Checklist de revisão aplicado a `src/remindme/` em `c3bd6ca`, depois da correção de defeitos (#70). O mesmo checklist serve para a revisão de todo PR com código (`docs/combinados.md`: "Todo PR é revisado por um colega").

Legenda: **Sim** atende; **Parcial** atende com ressalva; **Não** não atende.

## 1. Checklist

### Conformidade com a spec e a baseline

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-01 | O código implementa a spec aprovada, sem comportamento além dela? | Sim | Matriz: 24 de 24 critérios passam. A correção de #70 só transforma erro interno em recusa, como a spec já exigia |
| R-02 | Cada regra de negócio está em um único ponto do domínio? (RNF-19, regra 8) | Sim | RB-21, RB-22 e RB-23 em `dominio/titulo.py`; RB-02 e OPEN-16 em `dominio/regras.py`; `test_RNF_19_*` |
| R-03 | Toda regra tem teste nomeado pelo identificador? | Sim | `test_RB_02_*`, `test_RB_21_*`, `test_RB_22_*`, `test_RB_23_*`, `test_OPEN_16_*` |
| R-04 | O domínio não depende de framework, banco, canal nem IA? (ADR-001, regra 9) | Sim | `test_ADR_001_*` |
| R-05 | Usa somente os termos do glossário? (regra 6) | Sim | Nenhuma ocorrência de "fatura", "boleto", "proposta", "lembrete", "conta" ou "RN". Uma docstring de teste usava "pedido" no sentido de "solicitado" e foi reescrita para evitar ambiguidade com o termo proibido |
| R-06 | Decisão ausente foi registrada em vez de preenchida? (regra 2) | Sim | OPEN-17, OPEN-18, OPEN-19 e OPEN-20 citadas no código e nos testes que dependem delas |
| R-07 | Spec e código mudaram juntos? (regra 5) | Sim | A correção de #70 atualizou a seção 8 da Spec 006 no mesmo commit |

### Organização e responsabilidades

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-08 | Cada camada faz só o que lhe cabe? | Sim | Domínio: regras e transições. Aplicação: permissão, transação, auditoria. Infraestrutura: memória |
| R-09 | Permissão é verificada antes de tocar nos dados? (DT-06) | Sim | `regras.exigir_permissao_*` é a primeira linha de `estornar_pagamento` e `cancelar_titulo` |
| R-10 | Toda alteração é atômica e auditada na mesma transação? (DT-04, DT-05) | Sim | Todo método de alteração usa `with self._uow`; [confiabilidade](confiabilidade.md) F-01 a F-03 |
| R-11 | As invariantes do título são protegidas pelo próprio código? | Parcial | `Titulo` é `dataclass` mutável: `estado` e `valor` podem ser atribuídos de fora (M-01 em [manutenibilidade](manutenibilidade.md)) |

### Duplicação

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-12 | Há lógica de negócio duplicada? | Não há | O cálculo do saldo existe só em `Titulo.saldo`; a regra de motivo, só em `_exigir_motivo`; a validação de valor, só em `_exigir_decimal` |
| R-13 | Há código estrutural repetido? | Parcial | Os métodos de alteração do serviço repetem a sequência transação → obter → domínio → salvar → auditar (M-02). Aceitável com quatro operações |
| R-14 | Os testes duplicam montagem de cenário? | Parcial | Cada arquivo de teste monta o próprio `ServicoTitulos` em `setUp`. Uma função de apoio comum reduziria repetição; não é urgente |

### Legibilidade

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-15 | Nomes dizem o que a coisa é? | Sim | `registrar_pagamento`, `estornar_pagamento`, `ESTADOS_QUE_ACEITAM_PAGAMENTO`, `proximo_do_vencimento` |
| R-16 | Funções curtas e simples? | Sim | Maior função com 22 linhas; maior complexidade ciclomática 8 |
| R-17 | Comentários explicam o porquê, e não o quê? | Sim | Ex.: "Comportamento provisório: OPEN-18"; "RB-22: Baixado se, e somente se, o saldo é zero" |
| R-18 | Estilo consistente? | Parcial | O serviço usa ora `uow.titulos`, ora `self._uow.titulos` (M-03). Não há formatador nem verificador de tipos configurado (M-07) |
| R-19 | Restos de depuração (`print`, `TODO`, código comentado)? | Não há | Busca sem ocorrências |

### Robustez e segurança

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-20 | Entradas inválidas são recusadas com motivo? | Sim, após #70 | [Defeitos](defeitos.md) D-01 a D-05 |
| R-21 | Valores monetários sem `float`? | Sim | `Decimal` em todo o código; `float` é recusado desde #70 |
| R-22 | Recusa por perfil não revela dados? | Sim | A permissão é verificada antes de buscar o título |
| R-23 | Há segredo, senha ou token no código? (`docs/seguranca.md`) | Não há | Busca sem ocorrências; `.gitignore` cobre `.env`, `mcp.env`, `*.pem`, `*.key` |
| R-24 | A suíte roda sem credencial externa? (RNF-23) | Sim | [Portabilidade](portabilidade.md) P-04 |

### Facilidade de manutenção e testes

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| R-25 | É fácil trocar a persistência? | Sim | Interfaces em `aplicacao/portas.py`; contrato do repositório em `tests/integracao/` |
| R-26 | Dependências de tempo são injetáveis? | Sim | `Relogio` e `data_referencia` |
| R-27 | Identificadores são injetáveis? | Não | `uuid4` dentro do serviço (M-04) |
| R-28 | Os testes falham quando a regra quebra? | Sim | Mutações aplicadas na revisão: desligar a restauração da unidade de trabalho (7 falhas), baixar com saldo de R$ 0,01 (6 falhas), trocar `>=` por `>` no estorno (1 falha), permitir estorno em título Cancelado (1 falha), importar a infraestrutura no domínio (1 falha) |

## 2. Resultado

| Situação | Itens |
|---|---|
| Sim / não há | 23 (R-20 só depois da correção de #70) |
| Parcial | 4 (R-11, R-13, R-14, R-18) |
| Não | 1 (R-27) |

Nenhum item bloqueia o merge. As ressalvas estão em [manutenibilidade](manutenibilidade.md) (M-01 a M-07), com recomendação e lugar para tratar. A principal é R-11: proteger estado e valor do título contra atribuição direta, o que precisa de proposta à equipe porque muda a forma do domínio.

A mutação de `>=` para `>` (estorno no dia do vencimento) só foi detectada por `test_A4_estorno_com_vencimento_igual_a_data_de_referencia_volta_a_aberto`, criado em #64. A suíte original não cobria esse limite.
