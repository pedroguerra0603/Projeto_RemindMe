# Plano da Spec 005 — Envio, decisão do cliente e conversão em título

> **Para agentes:** executar tarefa a tarefa, com TDD (teste falhando → código mínimo → suíte verde → commit). Os passos usam caixas (`- [ ]`) para acompanhar o andamento. Commits com autor e committer `Renan Ribeiro <gandolpho.renan@gmail.com>`, sem rodapé de coautoria (pedido de Renan Gandolpho em 2026-11-07).

**Objetivo:** levar o orçamento pronto ao cliente pelo canal simulado, registrar a decisão dele e, na aprovação, gerar o título e converter o orçamento na mesma operação.

**Arquitetura:** abordagem A da spec. As transições ficam nos objetos: `Orcamento.marcar_enviado`, `Orcamento.registrar_decisao` e `Orcamento.converter`, além da fábrica `Titulo.gerar_de_orcamento`. O `ServicoOrcamentos` orquestra tudo numa única `Execucao.operacao`. O canal de notificação é uma porta da aplicação (`CanalNotificacao`), com o `CanalSimulado` na infraestrutura. Toda tentativa de envio vira uma `Mensagem` gravada pelo serviço em `uow.mensagens`, na mesma transação. A persistência ganha a migração 5, e a interface ganha o envio e a decisão na página do orçamento, além da tela `/mensagens`.

**Tecnologia:** Python 3.11+, só a biblioteca padrão, `unittest`, SQLite, WSGI (ADR-006, ADR-007).

**Spec:** [`../specs/005-envio-decisao-e-conversao-em-titulo.md`](../specs/005-envio-decisao-e-conversao-em-titulo.md)

## Restrições globais

- Termos do glossário em código e telas: Orçamento, Enviado, Aprovado, Rejeitado, Convertido, Título, Prazo para pagamento, Caixa de saída, Canal de notificação.
- Prazo para pagamento: inteiro de 0 a 365 dias (OPEN-61), guardado em `prazo_pagamento_dias`. Vencimento do título = `decidido_em + timedelta(days=prazo_pagamento_dias)`.
- Um título por orçamento (OPEN-15). A origem do título gerado é `"orcamento"`, ao lado do `"manual"` que já existe.
- O texto ao cliente sai só de `mensagem_de_orcamento` (RB-27). A aplicação não importa nada da apresentação, então os valores são formatados ali mesmo, em reais ("R$ 1.234,56") e com datas "dd/mm/aaaa".
- O domínio não importa o canal (ADR-001, INV-5). O teste `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas` continua passando.
- Auditoria: as referências são `orcamento <id>` e `titulo <id>`, como nos serviços que já existem. As mudanças de estado usam `operacao="mudar estado"`.
- Testes nomeados pelo critério ou pela regra: `test_CA_nn_...`, `test_RB_nn_...`, `test_OPEN_61_...`.
- Nenhuma dependência nova. A migração 5 não usa `DROP` nem `TRUNCATE`. Toda conexão aberta num teste é fechada (`closing`), como manda a lição do commit `bc6cbcd`.
- Pirâmide (`docs/testes.md`, lacuna 1): a regra é testada primeiro no domínio, há um teste de aceite por critério, e na interface só o que depende da tela.

## Foco de revisão

1. **Orçamento com 100% de desconto (valor líquido zero).** O título não aceita valor zero. O esperado é que o envio seja recusado antes de chegar ao cliente, com "O valor líquido é zero: não há o que cobrar.". Teste de domínio: `test_foco_1_valor_liquido_zero_nao_e_enviado` (tarefa 1). *Decisão nova, a confirmar na revisão deste plano.*
2. **Empresa sem cadastro (tela Empresa nunca preenchida).** O envio funciona, e a mensagem usa "Nossa empresa" no lugar do nome. Teste de unidade: `test_foco_2_sem_empresa_cadastrada_usa_nossa_empresa` (tarefa 2). *Decisão nova, a confirmar na revisão deste plano.*
3. **Duplo clique em "Registrar aprovação".** O primeiro pedido converte. O segundo é recusado pelo E3 (orçamento Convertido), e continua existindo um único título. Teste web: `test_foco_3_aprovacao_enviada_duas_vezes_gera_um_titulo` (tarefa 5).
4. **Canal que lança exceção em vez de devolver falha.** Conta como falha do E2: a mensagem fica com o resultado "falhou", o orçamento continua em Rascunho e não aparece erro 500. Teste: `test_foco_4_canal_que_lanca_excecao_conta_como_falha` (tarefa 3).
5. **Prazo digitado com espaços ou zeros à esquerda ("030", " 30 ").** É aceito como 30. Campo vazio limpa o prazo. "2,5" e "1e2" são recusados. Teste de domínio: `test_foco_5_prazo_aceita_espacos_e_zeros_a_esquerda` (tarefa 1).

---

### Tarefa 1: domínio — prazo, envio, decisão e conversão

**Arquivos:**
- Modificar: `src/remindme/dominio/orcamento.py`
- Modificar: `src/remindme/dominio/titulo.py`
- Testes: `tests/dominio/test_orcamento.py`, `tests/dominio/test_titulo.py`

**Interfaces:**
- Produz, em `Orcamento`:
  - campos novos, com padrão `None`: `prazo_pagamento_dias: Optional[int]`, `enviado_em: Optional[date]`, `decidido_em: Optional[date]`, `motivo_rejeicao: Optional[str]`, `titulo_id: Optional[str]`;
  - a constante `PRAZO_MAXIMO_DIAS = 365`;
  - `alterar_prazo(self, dias: object) -> None`;
  - `marcar_enviado(self, data: date) -> None`;
  - `registrar_decisao(self, aprovado: bool, data: object, hoje: date, motivo: object = None) -> None`;
  - `converter(self, titulo_id: str) -> None`;
  - a propriedade `vencimento_do_titulo -> date`.
- Produz, em `Titulo`:
  - o campo `orcamento_id: Optional[str] = None`, como último campo;
  - `Titulo.gerar_de_orcamento(cls, id: str, orcamento: Orcamento) -> Titulo`.
- Mensagens exatas:
  - campo `prazo`: "O prazo para pagamento é um número inteiro de dias, de 0 a 365.";
  - motivo de não envio, na ordem de `motivo_para_nao_enviar`, depois do item: "Informe o prazo para pagamento antes de enviar o orçamento (OPEN-61)." e "O valor líquido é zero: não há o que cobrar.";
  - decisão fora de Enviado: `f"Orçamento {estado.value} não aceita decisão do cliente (RF-12)."`;
  - campo `data`: "Informe a data da decisão do cliente.", "A data da decisão não pode ser posterior a hoje." ou `f"A data da decisão não pode ser anterior ao envio ({dd/mm/aaaa})."`;
  - conversão fora de Aprovado, também em `gerar_de_orcamento`: `f"Só orçamento Aprovado vira título; este está {estado.value} (RF-12)."`.

- [ ] **Passo 1: testes de domínio** em `test_orcamento.py`:
  - `test_OPEN_61_prazo_aceita_0_e_365_e_recusa_fora_da_faixa`: 0, 30 e 365 gravam. -1, 366, "2,5", `True` e "abc" lançam `OperacaoRecusada` com `campos == {"prazo": ...}`.
  - `test_foco_5_prazo_aceita_espacos_e_zeros_a_esquerda`: "030" e " 30 " gravam 30; "" grava `None`.
  - `test_INV_7_prazo_so_muda_em_rascunho`: em Pendente de Alçada, a mudança é recusada.
  - `test_OPEN_61_sem_prazo_nao_e_enviado` e `test_foco_1_valor_liquido_zero_nao_e_enviado`, ambos pelo `motivo_para_nao_enviar`.
  - `test_RF_08_marcar_enviado_guarda_a_data`.
  - `test_RF_09_aprovacao_e_rejeicao`: aprovar leva a `APROVADO`; rejeitar leva a `REJEITADO` com o motivo aparado, e motivo em branco vira `None`.
  - `test_E3_decisao_fora_de_enviado_e_recusada`: um caso para cada estado diferente de Enviado.
  - `test_E4_data_da_decisao`: ausente, amanhã e véspera do envio são recusadas no campo `data`; o próprio dia do envio é aceito.
  - `test_OPEN_61_vencimento_e_decisao_mais_prazo`: casos 31/01 + 30 = 02/03 (2026); 20/12 + 15 = 04/01/2027; prazo 0 = o mesmo dia.
  - `test_RF_12_converter_exige_aprovado`.
- [ ] **Passo 2: testes de domínio** em `test_titulo.py`:
  - `test_RF_19_gerar_de_orcamento_copia_cliente_valor_liquido_condicao_e_vencimento`: confere `origem == "orcamento"`, `orcamento_id` e o estado `ABERTO`.
  - `test_RF_12_gerar_de_orcamento_nao_aprovado_e_recusado`.
- [ ] **Passo 3: rodar** `python3 -m unittest tests.dominio.test_orcamento tests.dominio.test_titulo -v`. Esperado: falha com `AttributeError` nos métodos novos.
- [ ] **Passo 4: implementar.**
  - O prazo aceita `int` (exceto `bool`) ou `str` de dígitos depois do `strip()`.
  - `marcar_enviado` chama `exigir_envio()`.
  - A data da decisão é conferida antes do estado só quando o estado é Enviado.
  - `gerar_de_orcamento` usa `orcamento.valor_liquido`, `orcamento.vencimento_do_titulo` e `orcamento.condicao_pagamento`.
- [ ] **Passo 5: rodar** os dois módulos (esperado: passam) e a suíte inteira `python3 -m unittest discover -s tests -t .` (esperado: OK; os 478 anteriores continuam passando).
- [ ] **Passo 6: commit** `feat: prazo, envio, decisão do cliente e conversão no domínio (Spec 005)`.

### Tarefa 2: mensagem ao cliente e canal simulado

**Arquivos:**
- Modificar: `src/remindme/aplicacao/portas.py`
- Criar: `src/remindme/aplicacao/modelos_de_mensagem.py`
- Criar: `src/remindme/infraestrutura/canal.py`
- Modificar: `src/remindme/infraestrutura/memoria.py`, com `RepositorioMensagensEmMemoria` e `uow.mensagens`, incluído em `_repositorios()`
- Modificar: `tests/apoio.py`, com `CanalQueFalha` e `CanalQueLanca`
- Testes: `tests/aplicacao/test_modelos_de_mensagem.py`, `tests/infraestrutura/test_memoria.py`

**Interfaces:**
- Produz, em `portas.py`:
  - `@dataclass(frozen=True) class Mensagem`, com `id: str`, `cliente_id: str`, `contato: str`, `assunto: str`, `texto: str`, `enviada_em: datetime`, `resultado: str` (`"enviada"` ou `"falhou"`) e `origem: str` (`"orcamento <id>"`);
  - `class CanalNotificacao(Protocol)`, com `entregar(self, contato: str, assunto: str, texto: str) -> bool`;
  - `class RepositorioMensagens(Protocol)`, com `registrar(self, mensagem: Mensagem) -> None` e `listar(self) -> List[Mensagem]`.
- Produz `numero_do_orcamento(orcamento_id: str) -> str`, que devolve `orcamento_id[:8].upper()`.
- Produz `mensagem_de_orcamento(empresa: Optional[Empresa], cliente: Cliente, orcamento: Orcamento) -> Tuple[str, str]`, que devolve o assunto e o texto.
- Produz `CanalSimulado.entregar(...) -> bool`, que devolve sempre `True` e não guarda nada: quem grava a `Mensagem` é o serviço.
- Texto exato do modelo. Linhas entre colchetes só aparecem quando a condição vale. "Nossa empresa" é usado quando `empresa` é `None`; quando há empresa, usa-se o nome fantasia ou, se ele estiver vazio, a razão social.

```
Assunto: Orçamento nº {numero} — {empresa}

Olá, {cliente.nome}.

{empresa} envia o orçamento nº {numero}:

- {descricao}: {quantidade} × {valor_unitario} = {total}     (uma linha por item)

Valor bruto: {bruto}
[Desconto: {percentual}% ({valor_desconto})]                  (se o percentual > 0)
Valor líquido: {liquido}
Prazo para pagamento: {prazo} dias a partir da aprovação      ("à vista, na aprovação" se 0)
[Condição de pagamento: {condicao}]                           (se informada)

Para aprovar ou recusar, responda a esta mensagem.
```

- [ ] **Passo 1: testes** em `test_modelos_de_mensagem.py`:
  - `test_RB_27_texto_tem_empresa_numero_itens_valores_e_prazo`: um orçamento de 2 × R$ 1.234,50 com 10% de desconto e prazo de 30 dias. As asserções conferem as linhas exatas: "- Revisão: 2 × R$ 1.234,50 = R$ 2.469,00", "Desconto: 10% (R$ 246,90)", "Valor líquido: R$ 2.222,10" e "Prazo para pagamento: 30 dias a partir da aprovação".
  - `test_RB_27_prazo_zero_e_sem_desconto_nem_condicao`: o texto tem "à vista, na aprovação" e não tem as linhas "Desconto" nem "Condição".
  - `test_foco_2_sem_empresa_cadastrada_usa_nossa_empresa`.
  - `test_nome_fantasia_vazio_usa_razao_social`.
- [ ] **Passo 2: teste** em `test_memoria.py`: `test_mensagens_sao_desfeitas_com_a_transacao`. Uma mensagem registrada dentro de `with uow:` que lança exceção não aparece depois.
- [ ] **Passo 3: rodar** os módulos novos. Esperado: falha com `ModuleNotFoundError`.
- [ ] **Passo 4: implementar.**
  - Quantidade sem zeros à direita e com vírgula: "1,5" e "2".
  - Reais com ponto de milhar e vírgula decimal.
- [ ] **Passo 5: rodar** os módulos e a suíte inteira. Esperado: OK.
- [ ] **Passo 6: commit** `feat: modelo da mensagem do orçamento e canal simulado (Spec 005)`.

### Tarefa 3: casos de uso — prazo, envio, decisão e caixa de saída (CA-01 a CA-14)

**Arquivos:**
- Modificar: `src/remindme/dominio/operacoes.py`, com `CONSULTAR_MENSAGENS = "Consultar mensagens enviadas"`
- Modificar: `src/remindme/dominio/permissoes.py`, com `Operacao.CONSULTAR_MENSAGENS: frozenset({_D, _O})` na `MATRIZ_INICIAL`
- Modificar: `src/remindme/aplicacao/servico_orcamentos.py`
- Criar: `src/remindme/aplicacao/servico_mensagens.py`
- Testes: `tests/aplicacao/test_spec_005_aceite.py`

**Interfaces:**
- Consome: tudo o que as tarefas 1 e 2 produzem.
- Produz:
  - `ServicoOrcamentos.__init__(self, uow, relogio, erros=None, autorizacao=None, canal: Optional[CanalNotificacao] = None)`. Sem canal, usa `CanalSimulado()`.
  - `ServicoOrcamentos.alterar_prazo(self, sessao, orcamento_id: str, dias: object) -> Orcamento`. Operação "alterar orçamento", `CONDUZIR_ORCAMENTO`. Audita o campo "prazo para pagamento", com o anterior e o novo como texto, ou `None`.
  - `ServicoOrcamentos.enviar_orcamento(self, sessao, orcamento_id: str) -> Orcamento`. Operação "enviar orçamento".
  - `ServicoOrcamentos.registrar_decisao_do_cliente(self, sessao, orcamento_id: str, aprovado: bool, data: object, motivo: object = None) -> Orcamento`. Operação "registrar decisão do cliente".
  - `ServicoMensagens(uow, relogio, erros=None, autorizacao=None).consultar(self, sessao) -> List[Mensagem]`, das mais recentes para as mais antigas, com a operação `CONSULTAR_MENSAGENS`.
  - Mensagem da falha de envio, lançada **depois** que a transação grava a tentativa: `OperacaoRecusada("O canal de notificação não entregou o orçamento. Ele continua em Rascunho; tente enviar de novo.")`.

- [ ] **Passo 1: testes de aceite** em `test_spec_005_aceite.py`.
  - A base segue o molde de `test_spec_004_aceite.Base`: `HOJE = date(2026, 11, 7)`, `RelogioFixo(datetime(2026, 11, 7, 12, 0))`, clientes c1 e c2, empresa "Menezes Serviços Ltda" com o nome fantasia "Menezes". O auxiliar `pronto()` cria um orçamento com o item ("Revisão do forno", 1, 1000.00), 10% de desconto e prazo de 30 dias, que dá R$ 900,00 líquidos.
  - Um teste por critério, com os valores da spec, de `test_CA_01_OPEN_61_prazo_gravado_e_auditado` a `test_CA_14_INV_1_segundo_titulo_e_recusado`. Detalhes de alguns:
    - **CA-05:** o serviço é montado com `canal=CanalQueFalha()`.
    - **CA-07:** confere `titulo.vencimento == date(2026, 12, 7)` e os registros de auditoria `orcamento <id>` "Enviado → Aprovado" e "Aprovado → Convertido", e `titulo <id>` "None → Aberto".
    - **CA-08:** o envio acontece com o relógio em 28/10. Depois o relógio vai para 07/11 e a aprovação é registrada com a data de 28/10, o que dá o título `VENCIDO`.
    - **CA-12:** usa `uow.auditoria.falhar = True`.
    - **CA-14:** chama `Titulo.gerar_de_orcamento` para um orçamento Convertido e espera `OperacaoRecusada`.
  - `test_foco_4_canal_que_lanca_excecao_conta_como_falha`: com `canal=CanalQueLanca()`, o resultado é o mesmo do CA-05.
  - `test_RB_03_contador_nao_ve_a_caixa_de_saida`, pelo `ServicoMensagens`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.aplicacao.test_spec_005_aceite -v`. Esperado: falha com `AttributeError`.
- [ ] **Passo 3: implementar.**
  - **`enviar_orcamento`:**
    - Dentro da operação: `exigir_envio()`; montar a mensagem com a empresa, o cliente e o orçamento; `entregar` dentro de `try` (exceção conta como `False`); `uow.mensagens.registrar(Mensagem(...))` com o resultado.
    - Se a entrega deu certo: `marcar_enviado(hoje)`, salvar e auditar o estado.
    - A recusa por falha do canal é lançada fora do `with`.
  - **`registrar_decisao_do_cliente`**, numa só operação:
    - `registrar_decisao(aprovado, data, hoje, motivo)`;
    - se aprovado: `Titulo.gerar_de_orcamento(_novo_id(), o)`, `titulo.marcar_vencido(hoje)` e `o.converter(titulo.id)`;
    - salvar o título e o orçamento;
    - auditar cada mudança de estado, inclusive Aberto → Vencido quando houver.
- [ ] **Passo 4: rodar** o módulo e a suíte inteira. Esperado: OK. Atenção a `test_permissoes` e à tela de Permissões: a operação nova aparece na matriz.
- [ ] **Passo 5: commit** `feat: envio, decisão do cliente e conversão em título nos casos de uso (Spec 005)`.

### Tarefa 4: persistência em SQLite (migração 5)

**Arquivos:**
- Modificar: `src/remindme/infraestrutura/sqlite.py`
- Testes: `tests/infraestrutura/test_sqlite.py`

**Interfaces:**
- Produz `_ESQUEMA_5`, incluído em `MIGRACOES`, com:
  - `ALTER TABLE orcamentos ADD COLUMN` para `prazo_pagamento_dias INTEGER`, `enviado_em TEXT`, `decidido_em TEXT`, `motivo_rejeicao TEXT` e `titulo_id TEXT`;
  - `ALTER TABLE titulos ADD COLUMN orcamento_id TEXT`;
  - `CREATE UNIQUE INDEX titulo_por_orcamento ON titulos (orcamento_id) WHERE orcamento_id IS NOT NULL`;
  - `CREATE TABLE mensagens (id TEXT PRIMARY KEY, cliente_id TEXT NOT NULL REFERENCES clientes (id), contato TEXT NOT NULL, assunto TEXT NOT NULL, texto TEXT NOT NULL, enviada_em TEXT NOT NULL, resultado TEXT NOT NULL, origem TEXT NOT NULL)`, com um índice em `enviada_em`.
- Produz, quando `numero == 5`: `INSERT OR IGNORE` das células de `CONSULTAR_MENSAGENS` da matriz inicial, no padrão da migração 4.
- Produz `RepositorioMensagensSQLite` (`registrar` e `listar`) e `uow.mensagens`. Os repositórios de orçamentos e de títulos passam a gravar e ler os campos novos, inclusive no `ON CONFLICT ... DO UPDATE`.

- [ ] **Passo 1: testes.**
  - `test_spec_005_orcamento_e_titulo_guardam_os_campos_novos`: ida e volta de prazo, datas, motivo e vínculos.
  - `test_INV_1_indice_unico_barra_segundo_titulo_do_orcamento`: um segundo `INSERT` com o mesmo `orcamento_id` lança `sqlite3.IntegrityError`.
  - `test_spec_005_mensagens_ida_e_volta`.
  - `test_spec_005_banco_da_versao_4_ganha_colunas_tabela_e_permissao`: no molde de `test_CA_17_banco_antigo_ganha_tabelas_e_permissoes`, com `MIGRACOES[:4]`. Um orçamento e um título antigos continuam legíveis, com os campos novos em `None`, e o Operador ganha `CONSULTAR_MENSAGENS`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.infraestrutura.test_sqlite -v`. Esperado: falha.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar** o módulo e a suíte inteira. Esperado: OK. O `test_ADR_007_migracao_e_idempotente_e_numerada` continua passando.
- [ ] **Passo 5: commit** `feat: migração 5 com prazo, vínculo do título e caixa de saída (Spec 005)`.

### Tarefa 5: interface web, montagem e demonstração

**Arquivos:**
- Modificar: `src/remindme/inicializacao.py`. `montar(..., canal: Optional[CanalNotificacao] = None)` usa `CanalSimulado()` como padrão e passa o canal ao `ServicoOrcamentos`. `Servicos` ganha `mensagens`.
- Modificar: `src/remindme/apresentacao/web/aplicacao_web.py`. Rotas e handlers novos:
  - `POST /orcamentos/{id}/envio`;
  - `POST /orcamentos/{id}/resposta-do-cliente`, com os campos `decisao` (`aprovar` ou `rejeitar`), `data` (lida por `f.ler_data`; data inválida dá o erro "Informe uma data válida.") e `motivo`;
  - `GET /mensagens`.
  - O handler `/orcamentos/{id}/condicao` passa a ler também o campo `prazo` e a chamar `alterar_prazo`.
  - Avisos novos: `"orcamento-enviado"`: "Orçamento enviado ao cliente."; `"orcamento-convertido"`: "Aprovação registrada. O título foi gerado."; `"orcamento-rejeitado"`: "Rejeição registrada.".
- Modificar: `src/remindme/apresentacao/web/paginas.py`, na página do orçamento:
  - campo "Prazo para pagamento (dias)" no formulário da condição;
  - a frase "O envio ao cliente chega com a Spec 005." dá lugar ao botão "Enviar ao cliente";
  - em Enviado, o formulário "Registrar decisão do cliente", com a data padrão de hoje;
  - o quadro "Envio ao cliente", com as mensagens de origem `orcamento <id>`;
  - o link "Título gerado" quando há `titulo_id`.
  - Na página do título: "Gerado do orçamento nº {numero}" quando há `orcamento_id`.
  - No menu: `("mensagens", "/mensagens", "Mensagens enviadas", "✉", Operacao.CONSULTAR_MENSAGENS)`.
- Criar: `src/remindme/apresentacao/web/paginas_mensagens.py`, no molde de `paginas_pagar.py`, com uma tabela de data e hora, cliente, contato, assunto, resultado e o texto num `<details>`.
- Modificar: `src/remindme/demonstracao.py`. Prazos nos orçamentos existentes, mais um orçamento Enviado, um Convertido (gera título) e um Rejeitado, cada um com a sua mensagem.
- Testes: `tests/apresentacao/test_spec_005_web.py`, no molde de `test_spec_004_web.py`.

- [ ] **Passo 1: testes web.**
  - `test_fluxo_operador_envia_e_registra_aprovacao`: prazo → envio → aprovação. A página do título mostra o link para o orçamento, e a do orçamento mostra o link para o título.
  - `test_botoes_conforme_o_estado`: "Enviar ao cliente" só em Rascunho pronto, e "Registrar decisão do cliente" só em Enviado.
  - `test_erros_por_campo_em_prazo_e_data`: `id="erro-prazo"` e `id="erro-data"` com status 400.
  - `test_texto_da_mensagem_e_escapado`: um item com `<script>` aparece escapado em `/mensagens` e na página do orçamento.
  - `test_caixa_de_saida_exige_sessao_e_nega_o_contador`: sem sessão, redireciona para a entrada; o Contador recebe 403 e não vê o item de menu.
  - `test_falha_do_canal_aparece_na_pagina`: com `montar(canal=CanalQueFalha())`, a resposta mostra a recusa, e a caixa de saída mostra "falhou".
  - `test_foco_3_aprovacao_enviada_duas_vezes_gera_um_titulo`.
  - `test_demonstracao_tem_orcamentos_enviado_convertido_e_rejeitado`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.apresentacao.test_spec_005_web -v`. Esperado: falha.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar** a suíte inteira. Esperado: OK. Depois, `python3 iniciar.py demonstracao` e uma conferência no navegador, em tela de computador e de celular (360 px), da página do orçamento e de `/mensagens`.
- [ ] **Passo 5: commit** `feat: telas de envio, decisão do cliente e caixa de saída (Spec 005)`.

### Tarefa 6: baseline e verificação

**Arquivos:**
- Modificar: `docs/modelo-dominio.md` e `docs/uml/dominio-v2.mmd` (e o `.png`):
  - `Orcamento`: `prazoPagamentoDias`, `enviadoEm`, `decididoEm`, `motivoRejeicao` e `converter()`;
  - `Titulo`: `gerarDeOrcamento()`;
  - linha "v4" no histórico.
- Modificar: `docs/glossario.md`, com os termos "Prazo para pagamento" (`Orcamento`) e "Caixa de saída" (sem classe).
- Modificar: `docs/uml/seq-UC-04.mmd`, a cópia embutida no UC-04 e o `.png`. As transições Aprovado → título → Convertido passam a ser chamadas aos objetos (`Orc->>Orc: registrarDecisao`, `Tit: gerarDeOrcamento`, `Orc->>Orc: converter`), como na DV-06.
- Modificar: a seção 8 da spec, a situação **Verificada** no mapa, `docs/rastreabilidade.md` (seções 3 e 4 refeitas pelo método descrito na seção 1 do próprio documento), `docs/documentacao-final.md`, `README.md`, `SPECS.md` e a pirâmide de `docs/testes.md`.

- [ ] **Passo 1:** atualizar os documentos e regerar os PNG que mudaram. O `mermaid-cli` fica só fora do repositório, como no item 4.
- [ ] **Passo 2: verificar.**
  - Todos os `.mmd` renderizam.
  - As cópias embutidas são iguais às fontes.
  - Nenhum link relativo quebrado.
  - Suíte inteira OK.
  - Recontagem da pirâmide: a participação da unidade não pode cair abaixo dos 35,7% de 2026-11-07.
- [ ] **Passo 3:** preencher a seção 8 da spec. Uma linha por CA com o nome do teste e o resultado, mais "Também verificado" e "Onde está cada parte", no padrão da Spec 004.
- [ ] **Passo 4: commit** `docs: registra a verificação da Spec 005 e atualiza a baseline`.
