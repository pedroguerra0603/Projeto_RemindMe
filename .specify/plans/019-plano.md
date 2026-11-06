# Plano da Spec 019 — Troca da própria senha

> **Para agentes:** executar tarefa a tarefa, com TDD (teste falhando → código mínimo → suíte verde → commit). Os passos usam caixas (`- [ ]`) para acompanhar o andamento. Commits com autor e committer `besanchess`, sem rodapé de coautoria (pedido de Bernardo Sanches em 2026-11-06).

**Objetivo:** permitir que cada usuário ativo troque a própria senha, informando a atual, com o encerramento das outras sessões dele.

**Arquitetura:** um caso de uso novo, `ServicoAcesso.trocar_senha`, passa pela `Execucao.do_usuario`, como entrar e sair. Ele identifica o usuário pela sessão, sem permissão da matriz, e grava o hash, as sessões e a auditoria numa só transação. A interface ganha as rotas `/trocar-senha` e um link no topo de todas as páginas. Não há tabela nova nem migração: `guardar_hash`, `remover_do_usuario` e `salvar` já existem nos repositórios em memória e no SQLite.

**Tecnologia:** Python 3.11+, só a biblioteca padrão, `unittest`, SQLite, WSGI (ADR-006, ADR-007). Playwright só para o teste opcional de navegador (OPEN-29), instalado no ambiente e fora do repositório.

**Spec:** [`../specs/019-troca-da-propria-senha.md`](../specs/019-troca-da-propria-senha.md)

## Restrições globais

- Nomes dos campos, iguais no serviço (`OperacaoRecusada.campos`) e no formulário: `senha_atual`, `nova_senha`, `confirmacao`.
- Nova senha: de 8 a 256 caracteres, sem regra de composição (OPEN-44), pela função `motivo_da_senha`, que continua sendo o único ponto dessa regra.
- A senha nunca é registrada na auditoria nem no log e nunca volta à página. O formulário lê as senhas com `req.formulario.get(nome, "")`, nunca com `req.campo`, que apara os espaços.
- Auditoria: operação `"trocar senha"`, registro `usuario <id>`, campo `senha`, anterior `None`, novo `"alterada"`.
- Testes nomeados pelo critério: `test_CA_nn_...`.
- Nenhuma dependência nova no repositório; nenhuma migração.

## Foco de revisão

1. Topo da página num celular de 360 px: o link novo não pode criar rolagem horizontal. Teste e2e: `test_RNF_16_topo_com_o_link_nao_estoura_360px` (tarefa 3).
2. Senha com espaços nas pontas, acentos e emoji: precisa ser guardada exatamente como digitada e entrar depois. Teste web: `test_senha_com_espacos_e_acentos_e_guardada_como_digitada` (tarefa 2).
3. Formulário enviado duas vezes (duplo clique): o primeiro troca; o segundo é recusado com "A senha atual não confere.", e a sessão continua válida. Teste web: `test_envio_repetido_nao_derruba_a_sessao` (tarefa 2).
4. Tela de Auditoria do Administrador: mostra a troca como "senha: — → alterada", sem a senha. Teste web: `test_auditoria_mostra_a_troca_sem_a_senha` (tarefa 2).
5. Gerenciador de senhas do navegador: o campo da senha atual usa `autocomplete="current-password"`, e os outros dois usam `autocomplete="new-password"`. Teste web: `test_campos_de_senha_orientam_o_gerenciador_de_senhas` (tarefa 2).

---

### Tarefa 1: caso de uso `trocar_senha` (CA-01 a CA-12, CA-19)

**Arquivos:**
- Modificar: `src/remindme/aplicacao/senhas.py` (`motivo_da_senha`)
- Modificar: `src/remindme/aplicacao/servico_acesso.py` (novo método)
- Criar: `tests/aplicacao/test_senhas.py` (unidade)
- Criar: `tests/aplicacao/test_spec_019_aceite.py` (aceite, em memória)
- Criar: `tests/integracao/test_spec_019_sqlite.py` (integração com SQLite real)

**Interfaces:**
- Produz: `motivo_da_senha(senha: object, ausente: str = "Informe a senha provisória.") -> str`.
- Produz: `ServicoAcesso.trocar_senha(self, sessao: Optional[str], senha_atual: object, nova_senha: object, confirmacao: object) -> None`. Lança `SessaoInvalida` (sessão inválida) ou `OperacaoRecusada` com `campos`.
- Produz as mensagens exatas por campo:
  - `senha_atual`: "Informe a senha atual." ou "A senha atual não confere."
  - `nova_senha`: "Informe a nova senha.", as de `motivo_da_senha` para o tamanho, ou "A nova senha deve ser diferente da atual."
  - `confirmacao`: "Repita a nova senha." ou "A confirmação não é igual à nova senha."

- [ ] **Passo 1: testes de unidade de `motivo_da_senha`** em `tests/aplicacao/test_senhas.py`:
  - `test_OPEN_44_limites_de_tamanho`: 7 caracteres dão "A senha deve ter pelo menos 8 caracteres."; 8 e 256 dão `""`; 257 dão "A senha deve ter no máximo 256 caracteres.".
  - `test_senha_ausente_usa_a_mensagem_pedida`: `motivo_da_senha("", ausente="Informe a nova senha.") == "Informe a nova senha."`; `motivo_da_senha(None) == "Informe a senha provisória."`.
  - `test_CifradorScrypt_gera_salt_novo_e_confere`: dois `gerar("x" * 8)` diferem; `conferir` aceita a certa e recusa a errada.
- [ ] **Passo 2: testes de aceite** em `tests/aplicacao/test_spec_019_aceite.py`:
  - Base no molde de `test_spec_002_aceite.Base`: `UnidadeDeTrabalhoEmMemoria`, `RelogioFixo(datetime(2026, 11, 6, 10, 0))`, `CIFRADOR_DE_TESTE`, Administrador criado e um Operador `diego@exemplo.com` com a senha `"senha-antiga-1"`.
  - Um teste por critério, com os valores da spec:
    - `test_CA_01_troca_aceita_e_so_a_nova_entra`: após a troca para `"senha-nova-123"`, `entrar` com a nova devolve sessão e com a antiga lança `OperacaoRecusada(CREDENCIAIS_INVALIDAS)`.
    - `test_CA_02_senha_atual_errada_nao_muda_nada`: `campos` tem só `senha_atual` com "A senha atual não confere."; a antiga entra; as duas sessões continuam válidas (`sessao_ativa` não lança).
    - `test_CA_03_nova_senha_com_7_ou_257_caracteres`
    - `test_CA_04_confirmacao_diferente`
    - `test_CA_05_nova_igual_a_atual`
    - `test_CA_06_tres_campos_vazios_indicados_de_uma_vez`: `set(campos) == {"senha_atual", "nova_senha", "confirmacao"}`.
    - `test_CA_07_outras_sessoes_sao_encerradas`: com as sessões A, B e C, depois da troca por A, `sessao_ativa(A)` funciona e `sessao_ativa(B)` e `(C)` lançam `SessaoInvalida`.
    - `test_CA_08_sessoes_de_outro_usuario_continuam`
    - `test_CA_09_sem_sessao_valida_e_recusada`: com `None`, `"desconhecida"`, sessão vencida (avançar `relogio.momento` em `DURACAO_DA_SESSAO`) e sessão de usuário inativado, lança `SessaoInvalida`, e o hash fica igual.
    - `test_CA_10_hash_e_salt_novos_e_auditoria_sem_senha`: o hash começa com `"scrypt$"`; o salt (`split("$")[4]`) difere do anterior; há exatamente um registro com `campo == "senha"`, `valor_anterior is None`, `valor_novo == "alterada"`, `operacao == "trocar senha"` e `usuario_id` do Operador; nenhum registro contém as duas senhas.
    - `test_CA_11_falha_na_auditoria_desfaz_tudo`: `uow.auditoria.falhar = True` faz a troca lançar `RuntimeError`; a antiga entra e a outra sessão continua válida.
    - `test_CA_12_todos_os_perfis_trocam_sem_permissao_da_matriz`: Dono, Operador, Contador e Administrador trocam a senha. Também troca um Contador depois que o Administrador retira dele toda permissão permitida e não fixada de `acesso.matriz(admin)`.
  - `test_INV_5_trocar_senha_nao_recebe_usuario`: `inspect.signature(ServicoAcesso.trocar_senha)` tem exatamente `self, sessao, senha_atual, nova_senha, confirmacao`.
- [ ] **Passo 3: teste de integração** em `tests/integracao/test_spec_019_sqlite.py`:
  - Montar como `Spec017Persistencia.montar`, com `preparar_banco` num diretório temporário.
  - `test_CA_19_troca_persiste_depois_de_reabrir_o_banco`: depois de reabrir com uma nova `UnidadeDeTrabalhoSQLite`, a nova senha entra e a antiga não; `SELECT COUNT(*) FROM sessoes WHERE usuario_id = ?` é 1 (só a sessão da troca).
  - `test_RNF_09_INV_4_falha_na_auditoria_desfaz_no_banco`: `unittest.mock.patch.object(uow.auditoria, "registrar", side_effect=RuntimeError)` faz a troca falhar; o hash no banco fica igual, e a contagem de sessões não muda.
  - Fechar toda conexão aberta no teste (`with closing(sqlite3.connect(...))`): no Windows, a pasta temporária não é apagada com o arquivo aberto (lição do commit `bc6cbcd`).
- [ ] **Passo 4: rodar** `python3 -m unittest tests.aplicacao.test_senhas tests.aplicacao.test_spec_019_aceite tests.integracao.test_spec_019_sqlite -v`. Esperado: falha, com `AttributeError: 'ServicoAcesso' object has no attribute 'trocar_senha'` e `TypeError` no argumento `ausente`.
- [ ] **Passo 5: implementar.**
  - `motivo_da_senha` passa a receber `ausente`.
  - `trocar_senha` usa `self._execucao.do_usuario("trocar senha", identificar)`. `identificar` chama `self._autorizacao.sessao(uow, sessao)` e guarda a `Sessao` numa lista, como faz `sessao_ativa`.
  - Os campos com erro são juntados e recusados de uma vez com `recusar_campos`. Só se confere a diferença entre a nova e a atual quando a atual confere e a nova não tem outro erro.
  - Depois: `guardar_hash(usuario.id, self._cifrador.gerar(nova))`, `sessoes.remover_do_usuario(usuario.id)`, `sessoes.salvar(sessao_atual)` e `op.registrar(_ref(usuario), "senha", None, "alterada")`.
- [ ] **Passo 6: rodar** os três módulos (esperado: tudo passa) e depois a suíte inteira `python3 -m unittest discover -s tests -t .` (esperado: OK, os 447 anteriores continuam passando).
- [ ] **Passo 7: commit** `feat: troca da própria senha no serviço de acesso (Spec 019)`.

### Tarefa 2: tela "Trocar senha" (CA-13 a CA-17 e focos 2 a 5)

**Arquivos:**
- Modificar: `src/remindme/apresentacao/web/aplicacao_web.py` (rotas, manipuladores, `AVISOS["senha"]`)
- Modificar: `src/remindme/apresentacao/web/paginas.py` (`pagina_trocar_senha` e o link em `layout`)
- Modificar: `src/remindme/apresentacao/web/estatico/estilo.css` (`.botao.discreto`)
- Criar: `tests/apresentacao/test_spec_019_web.py`

**Interfaces:**
- Consome: `ServicoAcesso.trocar_senha` e as mensagens da tarefa 1.
- Produz:
  - as rotas `("GET", "/trocar-senha", self._trocar_senha_pagina, protegida)` e `("POST", "/trocar-senha", self._trocar_senha, protegida)`;
  - `paginas.pagina_trocar_senha(ctx: Contexto, erros: Erros) -> Html`, com os campos `#senha_atual`, `#nova_senha` e `#confirmacao`, todos `type="password"` e sem `value`, e o botão "Trocar senha";
  - no topo, `<a class="botao discreto" href="/trocar-senha">Trocar senha</a>`, entre o botão de tema e o "Sair";
  - o redirecionamento de sucesso para `/painel?aviso=senha`, com o aviso `("sucesso", "Senha alterada. As outras sessões abertas com o seu usuário foram encerradas.")`.

- [ ] **Passo 1: testes web** em `tests/apresentacao/test_spec_019_web.py`, sobre `test_spec_017_web.Base`:
  - `test_CA_13_sem_sessao_get_e_post_levam_a_entrada`: GET e POST dão 303 para `/entrar`, e a senha não muda.
  - `test_CA_14_todos_os_perfis_veem_o_link`: `href="/trocar-senha"` no painel de Carla, Diego, Helena e Ana.
  - `test_CA_15_erros_voltam_com_400_por_campo_sem_as_senhas`: `id="erro-senha_atual"`, `id="erro-nova_senha"` e `id="erro-confirmacao"` presentes; as senhas digitadas ausentes do HTML.
  - `test_CA_16_sem_protecao_e_recusado`: 403, e a senha antiga continua entrando.
  - `test_CA_17_troca_leva_ao_painel_e_derruba_o_outro_navegador`: 303 para `/painel?aviso=senha`, e o painel mostra o aviso; o segundo `ClienteWeb` recebe 303 com destino começando por `/entrar?aviso=sessao-encerrada`.
  - Focos 2 a 5: `test_senha_com_espacos_e_acentos_e_guardada_como_digitada` (nova `"  pão de açúcar 🙂  "`, depois `entrar` com ela exata dá 303 para `/painel`), `test_envio_repetido_nao_derruba_a_sessao`, `test_auditoria_mostra_a_troca_sem_a_senha` e `test_campos_de_senha_orientam_o_gerenciador_de_senhas`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.apresentacao.test_spec_019_web -v`. Esperado: falha, com 404 em `/trocar-senha` e o link ausente.
- [ ] **Passo 3: implementar.**
  - `_trocar_senha` lê as três senhas com `req.formulario.get`. Se o serviço recusar, devolve `_trocar_senha_pagina(req, sessao, ctx, _erros(recusa))` com status 400.
  - A página usa `campo(..., valores={}, tipo="password", extra='autocomplete="..."')`; a nova senha tem a ajuda "Pelo menos 8 caracteres.". `layout(..., secao="")`.
  - CSS: `.botao.discreto` com o mesmo visual de `button.discreto`, inclusive no `:hover`.
- [ ] **Passo 4: rodar** o módulo (esperado: tudo passa) e a suíte inteira (esperado: OK).
- [ ] **Passo 5: commit** `feat: tela de troca de senha e link no topo (Spec 019)`.

### Tarefa 3: ponta a ponta no navegador (CA-18 e foco 1)

**Arquivos:**
- Modificar: `tests/ponta_a_ponta/test_navegador.py`

**Interfaces:**
- Consome: as rotas, os seletores (`#senha_atual`, `#nova_senha`, `#confirmacao`, `a[href="/trocar-senha"]`) e o aviso da tarefa 2; os dados de demonstração (`diego@demo.example`, `SENHA`).

- [ ] **Passo 1: instalar o Playwright só neste ambiente**, na versão do Chromium já disponível: `pip install playwright==1.63.0`. `PLAYWRIGHT_BROWSERS_PATH` já aponta para `/opt/pw-browsers`; não rodar `playwright install`.
- [ ] **Passo 2: testes**, na mesma classe `FluxoCriticoNoNavegador`:
  - `test_CA_18_trocar_senha_sair_e_entrar_com_a_nova`:
    - Contexto B entra como Diego.
    - Contexto A entra como Diego, clica em "Trocar senha", preenche os três campos e envia. Espera `/painel` com "Senha alterada.".
    - A clica em "Sair". Entrar com a senha antiga mostra "E-mail ou senha incorretos."; com a nova, chega ao `/painel`.
    - B abre `/painel` e cai em `/entrar` com "Sua sessão terminou".
  - `test_RNF_16_topo_com_o_link_nao_estoura_360px`: página com `viewport={"width": 360, "height": 740}`, logada. Em `/painel` e em `/trocar-senha`, `document.documentElement.scrollWidth <= window.innerWidth`.
- [ ] **Passo 3: rodar** `python3 -m unittest tests.ponta_a_ponta.test_navegador -v`. Esperado: o CA-23 antigo e os dois novos passam. Se o 360 px estourar, ajustar o CSS do topo (`.quem` com espaçamento menor no `@media (max-width: 860px)`) até passar.
- [ ] **Passo 4: commit** `test: troca de senha de ponta a ponta no navegador (Spec 019, CA-18)`.

### Tarefa 4: verificação e documentação

**Arquivos:**
- Modificar: `.specify/specs/019-troca-da-propria-senha.md` (seção 8 e situação)
- Modificar: `.specify/specs/mapa-de-specs.md` (situação Verificada)
- Modificar: `SPECS.md` e `README.md` (situação do projeto)
- Modificar: `docs/rastreabilidade.md` (RF-95 e RF-96 na seção 3)

- [ ] **Passo 1: suíte inteira** `python3 -m unittest discover -s tests -t . -v`: anotar o total, todos passando e os pulados. Também `python3 -m unittest tests.ponta_a_ponta.test_navegador -v`, com o Playwright.
- [ ] **Passo 2: preencher a seção 8 da spec.** Data, comando e total; tabela "critério → teste → resultado" de CA-01 a CA-19; invariantes INV-1 a INV-5; divergências e limitações.
- [ ] **Passo 3: atualizar o restante.** Mapa e situação da spec como **Verificada**; `SPECS.md` e `README.md` citando a Spec 019; linhas de RF-95 e RF-96 em `rastreabilidade.md`, com código e testes.
- [ ] **Passo 4: commit** `docs: registra a verificação da Spec 019` e `git push -u origin feature/troca-de-senha`.
