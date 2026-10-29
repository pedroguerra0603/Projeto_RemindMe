# Spec 004 — Orçamento: itens, valores e alçada de desconto

## 1. Identificação

| | |
|---|---|
| **ID** | 004 |
| **Nome** | Orçamento: itens, valores e alçada de desconto |
| **Objetivo** | Montar o orçamento de um cliente, com itens, valores calculados e desconto controlado pela alçada de cada perfil, até ele ficar pronto para envio. |
| **Valor entregue** | O Operador Financeiro monta o orçamento e vê o valor líquido na hora. A Dona sabe que nenhum desconto acima da alçada passa sem a decisão dela, e vê no painel o que espera por ela. |
| **Situação** | **Proposta** — implementada e verificada em 2026-10-29 a pedido de Renan Gandolpho; aguarda a aprovação da equipe na revisão do PR (seção 8). |
| **Aprovada por** | *(aguardando)* |

## 2. Rastreabilidade

| Tipo | Itens |
|---|---|
| RF | RF-06, RF-07, RF-10, RF-13, RF-15, RF-16, RF-17, RF-18; RF-14 só com a alçada padrão (configuração na Spec 014) |
| RB | RB-15, RB-24; preserva RB-01 e RB-03 |
| RNF | RNF-03, RNF-09, RNF-14 |
| UC | [UC-04](../../docs/casos-de-uso/UC-04-conduzir-orcamento-ate-o-titulo.md) (passos 1 a 4, A1, A3), [UC-05](../../docs/casos-de-uso/UC-05-aprovar-desconto-fora-de-alcada.md) |
| Entidades | `Orcamento`, `ItemOrcamento`, `AlcadaDesconto`, `AprovacaoDesconto` |
| Drivers e ADRs | DA-01, DA-02, DA-03, DA-04, DA-09; ADR-001, ADR-004 |
| Depende de | Specs 001, 002 e 003. Questões OPEN-49 a OPEN-52, abertas nesta spec. |

## 3. Escopo

### Incluído

- Criação do orçamento para um cliente cadastrado, em Rascunho (RF-06).
- Inclusão, alteração e remoção de itens, com recálculo do valor bruto, do desconto e do valor líquido (RF-07).
- Desconto em percentual, comparado com a alçada do perfil de quem o informa (RF-15). Acima dela, o orçamento fica Pendente de Alçada (RF-16).
- Decisão do Dono: aprovar o solicitado, aprovar um percentual menor ou rejeitar (RF-17, UC-05).
- Registro do valor anterior e do novo valor do desconto e do orçamento (RF-18).
- Cancelamento com motivo (RF-13).
- Consulta com filtro por cliente, período e estado (RF-10).
- Verificação de que o orçamento pode sair de Rascunho: ao menos um item (RB-24) e nenhum desconto pendente (RB-15).
- Interface web: lista, criação, página do orçamento e quadro "Descontos aguardando sua decisão" no painel do Dono.

### Fora do escopo

| Item | Onde é tratado |
|---|---|
| Envio ao cliente, decisão do cliente e conversão em título (RF-08, RF-09, RF-11, RF-12, RF-19) | Spec 005 |
| Configuração da alçada por perfil (RF-14) | Spec 014; até lá, a alçada padrão de OPEN-49 |
| Acesso do Cliente ao orçamento | Specs 005 e 009 |

## 4. Comportamento

### Pré-condições

- O usuário está autenticado com um perfil que tem "Conduzir orçamento" (Dono e Operador Financeiro, na matriz inicial).
- O cliente está cadastrado (Spec 003).

### Fluxo principal

1. O Operador Financeiro cria o orçamento para o cliente, com a condição de pagamento opcional. O orçamento nasce em Rascunho, sem itens e sem desconto.
2. O Operador inclui os itens, com descrição, quantidade e valor unitário. Cada inclusão recalcula os valores.
3. O Operador informa o desconto em percentual.
4. O sistema compara o percentual com a alçada do perfil do Operador. Dentro dela, o desconto é aplicado.
5. Com ao menos um item e sem desconto pendente, o orçamento está pronto para o envio da Spec 005.

### Valores

- Total do item = quantidade × valor unitário, arredondado ao centavo, metade para cima (OPEN-51).
- Valor bruto = soma dos totais dos itens.
- Valor do desconto = valor bruto × percentual ÷ 100, arredondado ao centavo, metade para cima.
- Valor líquido = valor bruto − valor do desconto.

### Fluxos alternativos

- **A1 — Desconto acima da alçada.** No passo 4, o orçamento passa a Pendente de Alçada. O desconto vigente não muda até a decisão. Enquanto pendente, itens, desconto e condição não mudam (RF-07).
- **A2 — Dono aprova.** O orçamento volta a Rascunho com o percentual solicitado. A decisão guarda o responsável, a data, o solicitado e o aprovado (RF-17).
- **A3 — Dono aprova menos.** O Dono informa um percentual menor que o solicitado; vale esse (UC-05, A2; RF-18).
- **A4 — Dono rejeita.** O orçamento volta a Rascunho com o desconto anterior (UC-05, A1).
- **A5 — Dono informa o desconto.** O Dono não tem limite (RB-15): o desconto que ele informa é aplicado sem pendência.
- **A6 — Cancelamento.** Em Rascunho, Pendente de Alçada ou Enviado, com motivo (RF-13). O estado é final.

### Exceções

- **E1 — Cliente inexistente.** A criação é recusada no campo cliente.
- **E2 — Item inválido.** Descrição vazia, quantidade ou valor unitário ausente, menor ou igual a zero ou com mais de duas casas: a recusa indica todos os campos de uma vez (RNF-14).
- **E3 — Percentual inválido.** Fora de 0 a 100, ou com mais de duas casas: recusado no campo percentual.
- **E4 — Valor acima do limite.** Valor bruto com 15 dígitos inteiros ou mais é recusado (OPEN-24).
- **E5 — Decisão sem pendência.** Decidir um orçamento que não está Pendente de Alçada é recusado, com o estado atual (UC-05, E2).
- **E6 — Aprovado maior que o solicitado.** Recusado.
- **E7 — Perfil sem permissão.** Quem não é Dono não decide desconto, nem chamando o serviço direto (UC-05, E1; RNF-03). O Contador não cria nem conduz orçamento (RB-03).

Toda recusa informa o motivo e não altera nenhum dado.

## 5. Invariantes

| ID | Invariante | Origem |
|---|---|---|
| INV-1 | Um orçamento está em exatamente um estado; as transições são as do [diagrama de estados](../../docs/uml/estados.md#orçamento). | RB-05, estados |
| INV-2 | Itens, desconto e condição só mudam em Rascunho. | RF-07 |
| INV-3 | O desconto vigente nunca passa da alçada de quem o informou, salvo com aprovação do Dono registrada. | RB-15 |
| INV-4 | Valor líquido = valor bruto − desconto, sempre recalculado dos itens; nenhum valor é guardado à parte. | RF-07 |
| INV-5 | As decisões do Dono só se acrescentam; uma decisão gravada não muda. | RF-17, RB-01 |
| INV-6 | Toda mudança de estado, de item, de desconto e de valor é auditada, com valor anterior e novo. | RB-01, RF-18 |

## 6. Critérios de aceitação

| ID | Dado | Quando | Então | Cobre |
|---|---|---|---|---|
| CA-01 | um Operador autenticado e um cliente cadastrado | ele cria um orçamento | o orçamento fica em Rascunho, elaborado por ele, com a data de hoje, e a criação é auditada | RF-06 |
| CA-02 | um Operador | ele cria um orçamento para um cliente inexistente | a criação é recusada no campo cliente | E1 |
| CA-03 | um orçamento em Rascunho | um item é incluído, alterado e removido | os valores são recalculados, e cada mudança de valor tem o anterior e o novo na auditoria | RF-07, RF-18 |
| CA-04 | um orçamento de R$ 1.000,00 e alçada de 10% | o Operador informa 10% | o desconto é aplicado, o valor líquido é R$ 900,00, e a auditoria guarda 0 → 10 | RF-15, RF-18 |
| CA-05 | o mesmo orçamento | o Operador informa 15% | o orçamento fica Pendente de Alçada, o desconto vigente não muda e o Dono o vê entre os pendentes | RF-16 |
| CA-06 | um orçamento Pendente de Alçada com 15% | o Dono aprova | volta a Rascunho com 15%, e a decisão guarda o Dono e a data | RF-17 |
| CA-07 | um pedido de 20% | o Dono aprova 12% | vale 12%, e a auditoria guarda o solicitado e o aprovado | UC-05 A2, RF-18 |
| CA-08 | um desconto vigente de 8% e um pedido de 30% | o Dono rejeita | volta a Rascunho com 8% | UC-05 A1 |
| CA-09 | um orçamento Pendente de Alçada | o Operador chama o serviço de decisão | a operação é negada com RB-15 no motivo, e nada muda | UC-05 E1, RNF-03 |
| CA-10 | um orçamento em Rascunho | o Dono informa 40% | o desconto é aplicado sem pendência | RB-15 |
| CA-11 | um Contador | ele tenta criar, incluir item ou consultar orçamentos | as três operações são negadas, e nada muda | RB-03 |
| CA-12 | um orçamento em Rascunho | ele é cancelado sem motivo e depois com motivo | a primeira tentativa é recusada; a segunda o leva a Cancelado, com o motivo na auditoria | RF-13 |
| CA-13 | orçamentos de dois clientes, um deles Cancelado | a consulta filtra por cliente, por estado e por período | cada filtro devolve só os orçamentos que atendem a ele | RF-10 |
| CA-14 | um orçamento Pendente de Alçada | um item é incluído | a inclusão é recusada, com o estado no motivo, e nada muda | RF-07, INV-2 |
| CA-15 | um orçamento sem itens | ele é verificado para envio | o motivo cita RB-24 | RB-24 |
| CA-16 | um orçamento | um item inválido e um percentual de 101% são enviados | as duas operações são recusadas, sem alterar dados nem gerar auditoria | Spec 001 E1 |

Os testes levam no nome o critério ou a regra, como `test_CA_09_RNF_03_...` e `test_RB_15_...`.

## 7. Questões em aberto

| ID | Questão | Bloqueia a implementação? |
|---|---|---|
| OPEN-49 | Qual a alçada de cada perfil até a Spec 014? | Não. Provisório: Operador Financeiro 10%; demais perfis 0%; Dono sem limite. |
| OPEN-50 | A alçada é a de quem elaborou (RB-15) ou a de quem informa o desconto (RF-15)? | Não. Provisório: a de quem informa, que é quem elaborou no fluxo normal. |
| OPEN-51 | Precisão da quantidade e do percentual, e arredondamento? | Não. Provisório: até duas casas; centavo arredondado metade para cima. |
| OPEN-52 | O filtro "período" do RF-10 é sobre a data de criação? | Não. Provisório: data de criação. |

## 8. Verificação

Implementada e verificada em 2026-10-29. Suíte completa: 383 testes, verdes em Python 3.11, 3.12 e 3.13.

| Critério | Teste (`tests/aplicacao/test_spec_004_aceite.py`) | Resultado |
|---|---|---|
| CA-01 | `test_CA_01_RF_06_cria_em_rascunho_para_cliente_cadastrado_e_audita` | Passou |
| CA-02 | `test_CA_02_cliente_inexistente_e_recusado_no_campo_cliente` | Passou |
| CA-03 | `test_CA_03_RF_07_RF_18_itens_recalculam_e_auditam_o_valor` | Passou |
| CA-04 | `test_CA_04_RF_15_desconto_dentro_da_alcada_e_aplicado_e_auditado` | Passou |
| CA-05 | `test_CA_05_RF_16_desconto_acima_da_alcada_fica_pendente_de_alcada` | Passou |
| CA-06 | `test_CA_06_RF_17_dono_aprova_e_a_decisao_fica_registrada` | Passou |
| CA-07 | `test_CA_07_UC_05_A2_aprovacao_menor_registra_solicitado_e_aprovado` | Passou |
| CA-08 | `test_CA_08_UC_05_A1_rejeicao_volta_a_rascunho_com_o_desconto_anterior` | Passou |
| CA-09 | `test_CA_09_RNF_03_operador_nao_decide_nem_chamando_o_servico` | Passou |
| CA-10 | `test_CA_10_RB_15_dono_concede_qualquer_desconto_sem_pendencia` | Passou |
| CA-11 | `test_CA_11_RB_03_contador_nao_cria_nem_conduz_orcamento` | Passou |
| CA-12 | `test_CA_12_RF_13_cancelamento_exige_motivo_e_fica_auditado` | Passou |
| CA-13 | `test_CA_13_RF_10_consulta_filtra_por_cliente_estado_e_periodo` | Passou |
| CA-14 | `test_CA_14_RF_07_pendente_de_alcada_nao_aceita_itens` | Passou |
| CA-15 | `test_CA_15_RB_24_orcamento_sem_item_nao_esta_pronto_para_envio` | Passou |
| CA-16 | `test_CA_16_recusa_nao_altera_dados_nem_deixa_auditoria` | Passou |

Também verificado:

- Regras do domínio, sem banco: `tests/dominio/test_orcamento.py` (23 testes, nomeados por RB, RF e OPEN).
- Interface web e SQLite: `tests/apresentacao/test_spec_004_web.py` (sessão obrigatória, fluxo completo Operador → Dona, erros por campo, escape de HTML, Contador sem acesso, Operador sem decisão).
- Migração: um banco criado antes desta spec ganha as tabelas novas sem perder dados (`test_ADR_007_banco_da_versao_1_e_atualizado_sem_perder_dados`).
- No navegador (Chromium), em tela de computador e de celular, com a demonstração.

### Onde está cada parte

| Parte | Arquivo |
|---|---|
| Regras, estados e cálculo | `src/remindme/dominio/orcamento.py` |
| Casos de uso, autorização e auditoria | `src/remindme/aplicacao/servico_orcamentos.py` |
| Persistência | `src/remindme/infraestrutura/sqlite.py` (migração 2) e `memoria.py` |
| Telas | `src/remindme/apresentacao/web/aplicacao_web.py` e `paginas.py` |

### Correção feita junto

No celular, todas as páginas ficavam mais largas que a tela, porque a coluna do conteúdo não encolhia (`1fr` em vez de `minmax(0, 1fr)`). Corrigido em `estilo.css`; agora as tabelas largas rolam dentro do próprio quadro.
