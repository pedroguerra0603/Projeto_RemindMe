# Plano da Spec 010 — Calendário de obrigações

> **Para agentes:** executar tarefa a tarefa, com TDD (teste falhando → código mínimo → suíte verde → commit). Os passos usam caixas (`- [ ]`) para acompanhar o andamento. Commits com autor e committer `Renan Ribeiro <gandolpho.renan@gmail.com>`, sem rodapé de coautoria nem assinatura do agente (pedido de Renan Gandolpho em 2026-11-20).

**Objetivo:** calendário único de obrigações, com aviso antes do prazo, cumprimento com evidência anexada, recorrência, atraso e escalonamento ao Dono pelo agendador.

**Arquitetura:** abordagem A da spec. Cada ocorrência é uma `Obrigacao`, ligada às outras pela `serie`, com uma lista de `EventoObrigacao` como histórico (RF-50). As regras ficam todas em `dominio/obrigacao.py`. O `ServicoObrigacoes` orquestra as operações do usuário e a verificação automática, que o `AgendadorDeVencimentos` chama. Os alertas saem pelo `CanalNotificacao` da Spec 005, com o texto de `modelos_de_mensagem.py`, e ficam na caixa de saída. A `Mensagem` passa a aceitar um usuário como destinatário. O conteúdo da evidência fica no banco, ao lado da obrigação e na mesma transação, como o hash da senha fica ao lado do usuário.

**Tecnologia:** Python 3.11+, só a biblioteca padrão, `unittest`, SQLite, WSGI (ADR-006, ADR-007). Sem `cgi` (removido no 3.13): o formulário multipart é lido por um módulo próprio.

**Spec:** [`../specs/010-calendario-de-obrigacoes.md`](../specs/010-calendario-de-obrigacoes.md)

## Restrições globais

- Termos do glossário em código e telas: Obrigação, Evidência, Pendente, Aguardando Evidência, Atrasada, Cumprida, Responsável, Periodicidade, Ocorrência, Escalonamento, Caixa de saída.
- Tipo: `Fiscal`, `Trabalhista`, `Contratual`, `Outra`. Periodicidade: `Única`, `Mensal`, `Trimestral`, `Semestral`, `Anual` (1, 3, 6 e 12 meses). OPEN-70, OPEN-71.
- `ANTECEDENCIA_DO_AVISO_DIAS = 7` e `TOLERANCIA_DO_ESCALONAMENTO_DIAS = 0`, só em `dominio/obrigacao.py` (INV-9).
- Atrasada quando `prazo < hoje`. Aviso quando Pendente e `hoje <= prazo <= hoje + 7`. Escalonamento quando Atrasada e `hoje >= prazo + 1 + tolerância`.
- Evidência: 1 byte a `5 * 1024 * 1024` bytes. Extensão `.pdf`, `.png`, `.jpg` ou `.jpeg`, com conteúdo que começa com `%PDF-`, `\x89PNG\r\n\x1a\n` ou `\xff\xd8\xff`, coerente com a extensão. Descrição obrigatória, até 200 caracteres. Nome da obrigação: até 120 caracteres.
- O responsável é um usuário ativo Dono ou Operador Financeiro. Qualquer perfil com `Operacao.GERENCIAR_OBRIGACOES` registra o cumprimento (OPEN-69). A operação já está na matriz (Dono e Operador; o Administrador pela OPEN-53), então não há linha nova de permissão.
- Auditoria: as referências são `obrigacao <id>` e `obrigacao <id>, evidencia <id>`. A mudança de estado usa `operacao="mudar estado"`. A rotina automática se chama `"verificação de obrigações"`.
- O texto dos alertas sai só de `modelos_de_mensagem.py` (RB-27, INV-6). O domínio não importa o canal (INV-7). `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas` continua passando.
- Testes nomeados pelo critério ou pela regra: `test_CA_nn_...`, `test_RB_nn_...`, `test_OPEN_6n_...`, `test_foco_n_...`.
- Pirâmide (`docs/testes.md`, lacuna 1): toda regra é testada primeiro no domínio. O aceite tem um teste por critério. A interface testa só o que depende da tela: sessão, formulário, upload, erro por campo, escape de HTML e download.
- Nenhuma dependência nova. A migração 6 não usa `DROP` nem `TRUNCATE`. Toda conexão aberta num teste é fechada (`closing`).

## Foco de revisão

1. **Nome de arquivo com caminho ou caracteres especiais** (`..\..\boleto".pdf`, `C:\fakepath\DAS março.pdf`). Guarda-se só o nome-base, sem barras nem aspas. O download manda `Content-Disposition: attachment` com `filename*` em UTF-8 e `X-Content-Type-Options: nosniff`. Testes: `test_foco_1_nome_do_arquivo_fica_so_com_o_nome_base` (tarefa 1) e `test_foco_1_download_e_anexo_com_nome_seguro` (tarefa 6).
2. **Formulário enviado sem escolher arquivo.** O navegador manda a parte com `filename=""` e conteúdo vazio, o que vale como "sem anexo", e não como "arquivo vazio". Teste web: `test_foco_2_campo_de_arquivo_vazio_vale_como_sem_anexo` (tarefa 6).
3. **Corpo grande ou multipart fora do lugar.** Multipart só é aceito nas rotas de cumprimento e de evidência, até `LIMITE_DO_UPLOAD = 6 * 1024 * 1024`; fora delas vale o limite de 64 KB. Multipart sem o campo `protecao` é recusado, como qualquer POST. Teste web: `test_foco_3_multipart_fora_da_rota_ou_grande_demais_e_recusado` (tarefa 6).
4. **Dono que também é o responsável.** Ele recebe um único aviso antes do prazo e um único escalonamento: nenhum alerta duplicado para o mesmo usuário. Teste de domínio: `test_foco_4_dono_responsavel_nao_recebe_alerta_duplicado` (tarefa 2).
5. **Dia-base 29, 30 ou 31 em periodicidades longas.** Anual com prazo 29/02/2028 → 28/02/2029 → … → 29/02/2032. Trimestral com 31/01 → 30/04 → 31/07. Teste de domínio: `test_foco_5_dia_base_volta_quando_o_mes_permite` (tarefa 2).

---

### Tarefa 1: domínio — obrigação, estados, cumprimento e evidência

**Arquivos:**
- Criar: `src/remindme/dominio/obrigacao.py`
- Testes: `tests/dominio/test_obrigacao.py`

**Interfaces:**
- Produz, em `dominio/obrigacao.py`:
  - `class TipoObrigacao(Enum)`: `FISCAL="Fiscal"`, `TRABALHISTA="Trabalhista"`, `CONTRATUAL="Contratual"`, `OUTRA="Outra"`.
  - `class Periodicidade(Enum)`: `UNICA="Única"`, `MENSAL="Mensal"`, `TRIMESTRAL="Trimestral"`, `SEMESTRAL="Semestral"`, `ANUAL="Anual"`, e a propriedade `meses -> int` (0, 1, 3, 6, 12).
  - `class EstadoObrigacao(Enum)`: `PENDENTE="Pendente"`, `AGUARDANDO_EVIDENCIA="Aguardando Evidência"`, `ATRASADA="Atrasada"`, `CUMPRIDA="Cumprida"`.
  - `@dataclass(frozen=True) class ArquivoDeEvidencia: nome: str; conteudo: bytes`.
  - `@dataclass(frozen=True) class Evidencia: id, descricao, nome_arquivo, tipo_arquivo, tamanho: int, anexada_em: datetime, usuario_id: str`, e `Evidencia.conferir(id: str, arquivo: ArquivoDeEvidencia, descricao: object, anexada_em: datetime, usuario_id: str) -> Evidencia`. O `tipo_arquivo` é `"application/pdf"`, `"image/png"` ou `"image/jpeg"`.
  - `@dataclass(frozen=True) class EventoObrigacao: quando: datetime; tipo: str; usuario_id: Optional[str]; detalhe: str = ""; destinatario_id: Optional[str] = None; prazo: Optional[date] = None`.
  - As constantes de tipo de evento, em `TipoEvento` (Enum de `str`): `CADASTRADA`, `GERADA`, `PRAZO_ALTERADO`, `RESPONSAVEL_ALTERADO`, `AVISO_ENVIADO`, `AVISO_FALHOU`, `ATRASADA`, `ESCALADA`, `ESCALONAMENTO_FALHOU`, `CUMPRIMENTO_REGISTRADO`, `EVIDENCIA_ANEXADA`, `CUMPRIDA`. Os valores são o texto do histórico ("cadastrada", "gerada a partir de outra ocorrência", "prazo alterado", "responsável alterado", "aviso enviado", "aviso não entregue", "atrasada", "escalada ao Dono", "escalonamento não entregue", "cumprimento registrado", "evidência anexada", "cumprida").
  - `@dataclass class Obrigacao`: `id, nome, tipo, periodicidade, prazo: date, prazo_referencia: date, dia_base: int, responsavel_id: str, exige_evidencia: bool, serie: str, estado: EstadoObrigacao, cumprimento_em: Optional[date] = None, cumprimento_por: Optional[str] = None, proxima_id: Optional[str] = None, evidencias: List[Evidencia] = [], historico: List[EventoObrigacao] = []`.
  - `Obrigacao.cadastrar(cls, id: str, nome: object, tipo: object, periodicidade: object, prazo: object, responsavel: Optional[Usuario], exige_evidencia: bool, hoje: date, usuario_id: str, quando: datetime) -> Obrigacao`. A série nasce igual ao `id`. Tipo e periodicidade aceitam o enum ou o seu `value` em texto.
  - `responsavel_valido(usuario: Optional[Usuario]) -> bool`: ativo e com perfil Dono ou Operador Financeiro.
  - Propriedade `aguarda_evidencia -> bool`: cumprimento registrado e estado diferente de Cumprida.
  - `alterar_prazo(self, prazo: object, hoje: date, usuario_id: str, quando: datetime) -> date`, que devolve o prazo anterior.
  - `alterar_responsavel(self, responsavel: Optional[Usuario], usuario_id: str, quando: datetime) -> str`, que devolve o anterior.
  - `registrar_cumprimento(self, data: object, hoje: date, usuario_id: str, quando: datetime, evidencia: Optional[Evidencia] = None) -> None`.
  - `anexar_evidencia(self, evidencia: Evidencia, quando: datetime) -> None`.
  - `marcar_atrasada(self, hoje: date, quando: datetime) -> bool`.
- Mensagens exatas:
  - campo `nome`: "Informe o nome da obrigação." ou "O nome tem no máximo 120 caracteres.";
  - campo `tipo`: "Escolha o tipo: Fiscal, Trabalhista, Contratual ou Outra.";
  - campo `periodicidade`: "Escolha a periodicidade: Única, Mensal, Trimestral, Semestral ou Anual.";
  - campo `prazo`: "Informe o prazo." ou, na alteração, "O novo prazo não pode ser anterior a hoje.";
  - campo `responsavel`: "Escolha um usuário ativo, Dono ou Operador Financeiro (OPEN-69).";
  - campo `arquivo`: "O arquivo está vazio.", "O arquivo tem no máximo 5 MB." ou "Anexe um PDF, PNG ou JPG (OPEN-68).";
  - campo `descricao`: "Descreva a evidência." ou "A descrição tem no máximo 200 caracteres.";
  - campo `data`: "Informe a data do cumprimento." ou "A data do cumprimento não pode ser posterior a hoje.";
  - fora do estado: `f"Obrigação {estado.value} não aceita {acao}."`, com `acao` igual a "cumprimento", "evidência", "alteração de prazo" ou "alteração de responsável".

- [ ] **Passo 1: testes de domínio** em `tests/dominio/test_obrigacao.py`, com `HOJE = date(2026, 11, 20)`:
  - `test_RF_40_cadastro_nasce_pendente_com_os_dados_e_o_evento`: confere estado `PENDENTE`, `dia_base == 20`, `prazo_referencia == prazo`, `serie == id` e `historico[0].tipo is TipoEvento.CADASTRADA`.
  - `test_E1_cadastro_recusa_todos_os_campos_de_uma_vez`: com nome vazio, tipo "Imposto", periodicidade "Semanal", prazo `None` e responsável Contador, `set(ctx.exception.campos) == {"nome","tipo","periodicidade","prazo","responsavel"}`. Também recusa responsável inativo e nome com 121 caracteres.
  - `test_A7_cadastro_com_prazo_passado_nasce_atrasada`.
  - `test_RF_45_A1_cumprimento_sem_exigencia_fica_cumprida` e `test_RF_47_cumprida_guarda_data_e_usuario` (INV-3).
  - `test_RB_29_cumprimento_com_evidencia_fica_cumprida`.
  - `test_A2_RB_13_cumprimento_sem_a_evidencia_exigida_aguarda`: estado `AGUARDANDO_EVIDENCIA` e `aguarda_evidencia` verdadeiro. `anexar_evidencia` leva a `CUMPRIDA`.
  - `test_A4_atrasada_sem_evidencia_continua_atrasada_ate_o_anexo`.
  - `test_A5_aguardando_evidencia_que_estoura_vira_atrasada_mantendo_o_cumprimento`.
  - `test_RF_48_marcar_atrasada_so_depois_do_prazo`: prazo 19/11 marca; prazo 20/11 não; Cumprida não; a segunda chamada devolve `False` (idempotente).
  - `test_E3_operacoes_fora_do_estado`: cumprir ou anexar em Cumprida; alterar o prazo de Atrasada ou de Cumprida; alterar o responsável de Cumprida.
  - `test_A3_RF_41_alteracoes_entram_no_historico_com_anterior_e_novo`: o `detalhe` traz as datas "dd/mm/aaaa → dd/mm/aaaa" ou o id do responsável anterior e o do novo. `prazo_referencia` e `dia_base` não mudam. Prazo de ontem é recusado no campo `prazo`.
  - `test_E4_data_do_cumprimento`: ausente e amanhã são recusadas no campo `data`.
  - `test_OPEN_63_evidencia_conferida_pelo_conteudo`: PDF, PNG e JPG válidos são aceitos, inclusive `.JPEG` em maiúsculas. São recusados no campo `arquivo`: vazio, `5*1024*1024 + 1` bytes, `.txt`, texto renomeado para `.pdf` e PNG renomeado para `.pdf`. Descrição vazia ou com 201 caracteres é recusada no campo `descricao`.
  - `test_foco_1_nome_do_arquivo_fica_so_com_o_nome_base`: `C:\fakepath\DAS março.pdf` → `DAS março.pdf`; `../../a"b.pdf` → `ab.pdf`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.dominio.test_obrigacao -v`. Esperado: `ModuleNotFoundError: remindme.dominio.obrigacao`.
- [ ] **Passo 3: implementar** `dominio/obrigacao.py` com as interfaces acima.
  - Cada método que muda algo acrescenta o seu `EventoObrigacao`.
  - `registrar_cumprimento` com evidência chama `anexar_evidencia`.
  - Sem a evidência exigida, Pendente passa a Aguardando Evidência, e Atrasada continua Atrasada.
  - O nome-base fica com o que vem depois da última `/` ou `\`, sem `"` e sem caracteres de controle, cortado em 120 caracteres.
  - Os erros de campo do cadastro são juntados com `recusar_campos` (RNF-14).
- [ ] **Passo 4: rodar** o mesmo comando. Esperado: OK.
- [ ] **Passo 5: commit** `feat: obrigação, estados, cumprimento e evidência no domínio (Spec 010)`.

### Tarefa 2: domínio — recorrência, aviso e escalonamento

**Arquivos:**
- Modificar: `src/remindme/dominio/obrigacao.py`
- Testes: `tests/dominio/test_obrigacao.py`

**Interfaces:**
- Consome: a tarefa 1.
- Produz:
  - `ANTECEDENCIA_DO_AVISO_DIAS = 7` e `TOLERANCIA_DO_ESCALONAMENTO_DIAS = 0`.
  - `avancar_meses(data: date, meses: int, dia_base: int) -> date`: o dia é `min(dia_base, último dia do mês)`, pelo `calendar.monthrange`.
  - `Obrigacao.gerar_proxima_ocorrencia(self, novo_id: str, hoje: date, quando: datetime) -> Optional[Obrigacao]`. Devolve `None` para Única. Recusa (`OperacaoRecusada`) se a obrigação não está Cumprida ou se `proxima_id` já existe (INV-4). O prazo é `avancar_meses(prazo_referencia, meses, dia_base)`. A nova ocorrência copia os dados e a série, nasce com o evento `GERADA` (detalhe com o id de origem) e é marcada Atrasada se o prazo já passou. A obrigação de origem guarda `proxima_id`.
  - `class TipoAlerta(Enum)`: `AVISO`, `ESCALONAMENTO`.
  - `Obrigacao.destinatarios_do_aviso(self, hoje: date, responsavel: Optional[Usuario], donos_ativos: List[str]) -> List[str]`. Quando a obrigação está Pendente e `hoje <= prazo <= hoje + 7`, os destinatários são o responsável, se ele for válido, ou senão os Donos ativos (A6). Saem da lista os que já têm `AVISO_ENVIADO` para o prazo atual.
  - `Obrigacao.destinatarios_do_escalonamento(self, hoje: date, donos_ativos: List[str]) -> List[str]`. Quando a obrigação está Atrasada e `hoje >= prazo + 1 + 0`, os destinatários são os Donos ativos que ainda não têm `ESCALADA` para o prazo atual.
  - `Obrigacao.registrar_alerta(self, tipo: TipoAlerta, destinatario_id: str, entregue: bool, quando: datetime) -> None`. Grava o evento entregue ou o de falha, com `destinatario_id` e `prazo=self.prazo`.

- [ ] **Passo 1: testes** em `test_obrigacao.py`:
  - `test_RF_42_OPEN_65_mensal_no_fim_do_mes`: 31/01/2027 → 28/02/2027 → 31/03/2027, na mesma série, Pendentes.
  - `test_RF_42_prazo_conta_do_anterior_e_nao_do_cumprimento`: Atrasada com prazo 20/10/2026, cumprida em 20/11/2026, gera uma próxima com prazo 20/11/2026 Pendente.
  - `test_A3_OPEN_65_alteracao_de_prazo_vale_so_para_a_ocorrencia`: prazo 20/12/2026, alterado para 05/01/2027 e cumprido, gera uma próxima com prazo 20/01/2027.
  - `test_RF_42_unica_nao_gera_e_INV_4_segunda_geracao_e_recusada`.
  - `test_RF_42_proxima_ja_vencida_nasce_atrasada`.
  - `test_foco_5_dia_base_volta_quando_o_mes_permite`: os casos Anual e Trimestral da seção Foco de revisão.
  - `test_RB_07_aviso_na_janela_de_7_dias_uma_vez_por_prazo`:
    - prazo 27/11 tem destinatário, e 28/11 não;
    - depois de `registrar_alerta(AVISO, ..., True)`, a lista fica vazia;
    - depois de `alterar_prazo` para 25/11, ela volta a ter o responsável;
    - depois de uma falha (`entregue=False`), o responsável continua na lista.
  - `test_RB_07_aguardando_evidencia_nao_recebe_aviso`.
  - `test_A6_responsavel_inativo_avisa_os_donos`.
  - `test_RB_16_escalonamento_aos_donos_ativos_uma_vez_por_prazo`: depois de entregar a um dos dois Donos, só o outro continua na lista.
  - `test_INV_9_valores_padrao`: `ANTECEDENCIA_DO_AVISO_DIAS == 7` e `TOLERANCIA_DO_ESCALONAMENTO_DIAS == 0`.
  - `test_foco_4_dono_responsavel_nao_recebe_alerta_duplicado`: com o Dono como responsável, o aviso vai uma vez só a ele, e o escalonamento também.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.dominio.test_obrigacao -v`. Esperado: falha com `AttributeError` nos métodos novos.
- [ ] **Passo 3: implementar.** A lista de destinatários não pode ter repetidos e mantém a ordem de `donos_ativos`.
- [ ] **Passo 4: rodar.** Esperado: OK.
- [ ] **Passo 5: commit** `feat: recorrência, aviso e escalonamento da obrigação no domínio (Spec 010)`.

### Tarefa 3: portas, memória, mensagem a usuário e modelos dos alertas

**Arquivos:**
- Modificar: `src/remindme/aplicacao/portas.py`, `src/remindme/infraestrutura/memoria.py`, `src/remindme/aplicacao/modelos_de_mensagem.py`
- Testes: `tests/aplicacao/test_modelos_de_mensagem.py`, `tests/infraestrutura/test_memoria.py`

**Interfaces:**
- Produz, em `portas.py`:
  - `Mensagem.cliente_id: Optional[str]` e o campo novo `usuario_id: Optional[str] = None`, por último. As chamadas que já existem não mudam.
  - `class RepositorioObrigacoes(Protocol)`:
    - `obter(obrigacao_id) -> Optional[Obrigacao]`;
    - `salvar(obrigacao) -> None`;
    - `listar() -> List[Obrigacao]`;
    - `guardar_conteudo(evidencia_id: str, conteudo: bytes) -> None`;
    - `conteudo_de(evidencia_id: str) -> Optional[bytes]`.
  - `UnidadeDeTrabalho.obrigacoes: RepositorioObrigacoes`.
- Produz, em `memoria.py`: `RepositorioObrigacoesEmMemoria`, com `_estado` e `_restaurar` como os outros, incluído em `_repositorios()`.
- Produz, em `modelos_de_mensagem.py`:
  - `mensagem_de_aviso_de_obrigacao(empresa: Optional[Empresa], usuario: Usuario, obrigacao: Obrigacao, hoje: date) -> Tuple[str, str]`;
  - `mensagem_de_escalonamento(empresa: Optional[Empresa], usuario: Usuario, obrigacao: Obrigacao, responsavel: Optional[Usuario], hoje: date) -> Tuple[str, str]`.
  - Texto exato do aviso:
    - assunto: `f"Obrigação a vencer: {nome} em {dd/mm/aaaa}"`;
    - texto, linha a linha: `f"Olá, {usuario.nome}."`, `""`, `f"A obrigação {nome} ({tipo}) vence em {dd/mm/aaaa}, {quando}."`, em que `quando` é "hoje", "amanhã" ou `f"daqui a {n} dias"`;
    - se exige evidência, mais a linha `"Ao registrar o cumprimento, anexe a evidência."`;
    - por fim, `""` e `f"{empresa} · RemindMe"`.
  - Texto exato do escalonamento:
    - assunto: `f"Obrigação atrasada: {nome}"`;
    - texto, linha a linha: `f"Olá, {usuario.nome}."`, `""`, `f"A obrigação {nome} ({tipo}) venceu em {dd/mm/aaaa} e está Atrasada há {n} {'dia' if n == 1 else 'dias'}."`, `f"Responsável: {responsavel.nome if responsavel else 'não definido'}."`, `""`, `f"{empresa} · RemindMe"`.
  - O nome da empresa usa o `_nome_da_empresa` que já existe.

- [ ] **Passo 1: testes.**
  - `test_RB_27_aviso_de_obrigacao_tem_o_texto_do_modelo` e `test_RB_27_escalonamento_tem_o_texto_do_modelo`: o texto exato, para hoje, amanhã e 5 dias, e para 1 e 3 dias de atraso.
  - `test_mensagem_aceita_usuario_como_destinatario`: `Mensagem(..., cliente_id=None, usuario_id="u1")` grava e lista.
  - `test_RNF_09_obrigacoes_em_memoria_desfazem_com_a_transacao`: uma obrigação e um conteúdo gravados dentro de um bloco que falha não ficam gravados.
- [ ] **Passo 2: rodar** os dois módulos. Esperado: falha com `ImportError`.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar** a suíte inteira, `python3 -m unittest discover -s tests -t .`. Esperado: OK.
- [ ] **Passo 5: commit** `feat: repositório de obrigações, mensagem a usuário e modelos dos alertas (Spec 010)`.

### Tarefa 4: casos de uso e agendador (CA-01 a CA-21, CA-23, CA-24)

**Arquivos:**
- Criar: `src/remindme/aplicacao/servico_obrigacoes.py`
- Modificar: `src/remindme/entradas/agendador.py`
- Testes: `tests/aplicacao/test_spec_010_aceite.py`

**Interfaces:**
- Consome: as tarefas 1 a 3, mais `Execucao`, `OperacaoAuditada`, `CanalNotificacao` e `data_local`.
- Produz, em `servico_obrigacoes.py`:
  - `@dataclass(frozen=True) class VisaoObrigacao`, com os campos `id, nome, tipo, periodicidade, prazo, estado, responsavel_id, responsavel_nome, responsavel_ativo: bool, exige_evidencia, aguarda_evidencia`.
  - `class ServicoObrigacoes(uow, relogio, erros=None, autorizacao=None, canal: Optional[CanalNotificacao] = None)`. Todos os métodos de usuário exigem `Operacao.GERENCIAR_OBRIGACOES`:
    - `cadastrar_obrigacao(sessao, nome, tipo, periodicidade, prazo: Optional[date], responsavel_id: str, exige_evidencia: bool) -> Obrigacao`;
    - `alterar_prazo(sessao, obrigacao_id, prazo: Optional[date]) -> Obrigacao`;
    - `alterar_responsavel(sessao, obrigacao_id, responsavel_id) -> Obrigacao`;
    - `registrar_cumprimento(sessao, obrigacao_id, data: Optional[date], arquivo: Optional[ArquivoDeEvidencia] = None, descricao: object = None) -> Obrigacao`, que gera a próxima ocorrência na mesma operação;
    - `anexar_evidencia(sessao, obrigacao_id, arquivo: ArquivoDeEvidencia, descricao: object) -> Obrigacao`, que também gera a próxima quando a obrigação fica Cumprida;
    - `consultar_calendario(sessao, estado: Optional[EstadoObrigacao] = None) -> List[VisaoObrigacao]`, ordenado por `(prazo, nome, id)` (RF-43);
    - `aguardando_evidencia(sessao) -> List[VisaoObrigacao]` (RF-77);
    - `obter_obrigacao(sessao, obrigacao_id) -> Obrigacao`;
    - `ocorrencias_da_serie(sessao, serie: str) -> List[Obrigacao]`, por prazo;
    - `conteudo_da_evidencia(sessao, obrigacao_id, evidencia_id) -> Tuple[Evidencia, bytes]`;
    - `responsaveis_possiveis(sessao) -> List[Usuario]`: ativos, Dono ou Operador, por nome.
  - `verificar_obrigacoes_automaticamente(self, hoje: date) -> List[str]`, sem sessão. Usa `Execucao.automatica("verificar obrigações", "verificação de obrigações")`, numa operação por obrigação, para que a falha de uma não desfaça as outras. Em cada uma:
    1. `marcar_atrasada`;
    2. para cada destinatário do escalonamento e do aviso: monta o texto, chama `canal.entregar(usuario.email, assunto, texto)` (exceção conta como falha), grava a `Mensagem` com `usuario_id`, `cliente_id=None` e `origem=f"obrigacao {id}"`, e chama `registrar_alerta`;
    3. salva e audita a mudança de estado.

    Devolve os ids que mudaram de estado ou receberam algum alerta.
- Auditoria das operações do usuário:
  - cadastro: um registro por campo (`nome`, `tipo`, `periodicidade`, `prazo`, `responsavel`, `exige_evidencia`, `estado`), com o valor anterior `None`;
  - alteração: o campo com o anterior e o novo;
  - cumprimento: `cumprimento_em`, o estado (se mudou) e, na evidência, `obrigacao <id>, evidencia <eid>` no campo `arquivo`, com o nome e o tamanho;
  - próxima ocorrência: os mesmos registros de um cadastro, na sua própria referência.
- Em `agendador.py`, `AgendadorDeVencimentos(..., obrigacoes: Optional[ServicoObrigacoes] = None)`, e `executar_uma_vez` soma `obrigacoes.verificar_obrigacoes_automaticamente(hoje)`.

- [ ] **Passo 1: testes de aceite** em `test_spec_010_aceite.py`.
  - Montagem, no padrão de `test_spec_005_aceite.py` e `test_spec_018_aceite.py`:
    - `RelogioFixo(datetime(2026, 11, 20, 9, 0))`;
    - os usuários Dono (com e-mail), Operador, Contador e um segundo Dono;
    - `CanalSimulado()` e, nos casos de falha, `CanalQueFalha` de `tests/apoio.py`;
    - o PDF de teste é `b"%PDF-1.4\n%teste\n"`.
  - Um teste por critério, com os dados exatos da seção 6 da spec, de `test_CA_01_RF_40_...` a `test_CA_21_E6_...`, `test_CA_23_ADR_002_...` e `test_CA_24_A3_...`. O CA-22 fica com a tarefa 6.
  - O CA-20 injeta a falha como o CA-12 da Spec 005: substitui `self.uow.auditoria.registrar` e falha no registro de `estado` → `Cumprida`.
  - O CA-04, o CA-14 e o CA-23 chamam `AgendadorDeVencimentos(..., obrigacoes=...).executar_uma_vez()` duas vezes e contam as mensagens em `uow.mensagens.listar()` com `resultado == "enviada"`, por `usuario_id`.
  - Também: `test_ADR_001_servico_sem_canal_nao_envia_alertas_mas_marca_atrasada`.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.aplicacao.test_spec_010_aceite -v`. Esperado: `ModuleNotFoundError`.
- [ ] **Passo 3: implementar** o serviço e o agendador.
- [ ] **Passo 4: rodar** a suíte inteira. Esperado: OK.
- [ ] **Passo 5: commit** `feat: casos de uso das obrigações e verificação pelo agendador (Spec 010)`.

### Tarefa 5: persistência em SQLite (migração 6)

**Arquivos:**
- Modificar: `src/remindme/infraestrutura/sqlite.py`
- Testes: `tests/infraestrutura/test_sqlite.py` (classe nova `Spec010NoSQLite`)

**Interfaces:**
- Consome: `RepositorioObrigacoes` e `Mensagem` da tarefa 3.
- Produz:
  - `_ESQUEMA_6`, acrescentado a `MIGRACOES`, com quatro tabelas:
    - `obrigacoes`: `id`, `nome`, `tipo`, `periodicidade`, `prazo`, `prazo_referencia`, `dia_base`, `responsavel_id REFERENCES usuarios`, `exige_evidencia`, `serie`, `estado`, `cumprimento_em`, `cumprimento_por`, `proxima_id`, com índices por `prazo` e por `serie`;
    - `eventos_obrigacao`: `obrigacao_id`, `ordem`, `quando`, `tipo`, `usuario_id`, `detalhe`, `destinatario_id`, `prazo`, com chave `(obrigacao_id, ordem)`;
    - `evidencias`: `id`, `obrigacao_id`, `descricao`, `nome_arquivo`, `tipo_arquivo`, `tamanho`, `anexada_em`, `usuario_id`, `conteudo BLOB`;
    - `mensagens_usuarios`: as mesmas colunas de `mensagens`, com `usuario_id REFERENCES usuarios` no lugar de `cliente_id`.
  - Separar as mensagens a usuários numa tabela própria evita reconstruir `mensagens`, cujo `cliente_id` é `NOT NULL`. Reconstruir exigiria `DROP`.
  - `RepositorioMensagensSQLite.registrar` grava na tabela do destinatário, e `listar` junta as duas por `enviada_em`.
  - `RepositorioObrigacoesSQLite`. O `salvar` substitui os eventos e as evidências da obrigação, mas não toca no `conteudo`. `obter` e `listar` não carregam o `conteudo`. `guardar_conteudo` e `conteudo_de` leem e gravam só a coluna `conteudo`.
  - `UnidadeDeTrabalhoSQLite.obrigacoes`.

- [ ] **Passo 1: testes.**
  - `test_obrigacao_ida_e_volta_com_historico_e_evidencias`: todos os campos, incluindo o `prazo` e o `destinatario_id` dos eventos.
  - `test_conteudo_da_evidencia_ida_e_volta_e_fora_do_obter`.
  - `test_mensagem_a_usuario_e_a_cliente_listadas_juntas_em_ordem`.
  - `test_CA_20_RNF_09_falha_na_auditoria_do_cumprimento_nao_deixa_nada_no_banco`: com o serviço sobre `UnidadeDeTrabalhoSQLite`, nem a evidência, nem o conteúdo, nem a próxima ocorrência ficam gravados.
  - `test_migracao_6_sobre_banco_da_versao_5_sem_perder_dados`: no padrão do teste da migração 5.
- [ ] **Passo 2: rodar** `python3 -m unittest tests.infraestrutura.test_sqlite -v`. Esperado: falha nos testes novos.
- [ ] **Passo 3: implementar.**
- [ ] **Passo 4: rodar** a suíte inteira. Esperado: OK.
- [ ] **Passo 5: commit** `feat: migração 6 com obrigações, evidências e mensagens a usuários (Spec 010)`.

### Tarefa 6: interface web, upload, painel, montagem e demonstração

**Arquivos:**
- Criar: `src/remindme/apresentacao/web/multipart.py`, `src/remindme/apresentacao/web/paginas_obrigacoes.py`
- Modificar:
  - `src/remindme/apresentacao/web/aplicacao_web.py`: `Servicos.obrigacoes`, as rotas, `Requisicao.arquivos` e o painel;
  - `src/remindme/apresentacao/web/paginas.py`: o item de menu e os quadros do painel;
  - `src/remindme/inicializacao.py`;
  - `src/remindme/demonstracao.py`;
  - `src/remindme/apresentacao/web/estatico/estilo.css`, só se faltar classe.
- Testes: `tests/apresentacao/test_multipart.py`, `tests/apresentacao/test_spec_010_web.py`

**Interfaces:**
- Produz, em `multipart.py`:
  - `@dataclass(frozen=True) class ArquivoEnviado: nome: str; conteudo: bytes`;
  - `ler_multipart(corpo: bytes, tipo_de_conteudo: str) -> Tuple[Dict[str, str], Dict[str, ArquivoEnviado]]`. O `boundary` vem do cabeçalho `Content-Type`, e o nome do arquivo de `filename` ou `filename*`. Uma parte com `filename=""` e conteúdo vazio não entra em `arquivos`. Corpo mal formado devolve dicionários vazios, sem exceção.
- Em `aplicacao_web.py`:
  - `LIMITE_DO_UPLOAD = 6 * 1024 * 1024`.
  - `ROTAS_COM_UPLOAD = re.compile(rf"^/obrigacoes/{ID}/(cumprimento|evidencias)$")`.
  - `Requisicao.arquivos: Dict[str, ArquivoEnviado]`. Multipart só é lido nas rotas de `ROTAS_COM_UPLOAD` e até `LIMITE_DO_UPLOAD`. Fora delas, e acima dos limites, a requisição dá `CorpoGrandeDemais`, como hoje.
- Rotas novas, todas protegidas:

  | Método | Rota | Função |
  |---|---|---|
  | GET | `/obrigacoes` | calendário, com o filtro `?estado=` |
  | GET, POST | `/obrigacoes/nova` | cadastro |
  | GET | `/obrigacoes/<id>` | detalhe com histórico, evidências, ocorrências da série e formulários |
  | POST | `/obrigacoes/<id>/prazo` | alteração de prazo |
  | POST | `/obrigacoes/<id>/responsavel` | alteração de responsável |
  | POST | `/obrigacoes/<id>/cumprimento` | multipart: `data`, `arquivo`, `descricao` |
  | POST | `/obrigacoes/<id>/evidencias` | multipart: `arquivo`, `descricao` |
  | GET | `/obrigacoes/<id>/evidencias/<eid>` | download |

- O download responde com `Content-Type` igual ao `tipo_arquivo`, `Content-Disposition: attachment; filename*=UTF-8''<nome codificado>` e `X-Content-Type-Options: nosniff`.
- Menu: `("obrigacoes", "/obrigacoes", "Obrigações", "◷", Operacao.GERENCIAR_OBRIGACOES)`, depois de "Contas a pagar".
- Calendário, em `paginas_obrigacoes.py`:
  - tabela por prazo com nome, tipo, prazo, responsável e estado;
  - selo por estado: Pendente `aberto`, Aguardando Evidência `proximo`, Atrasada `vencido`, Cumprida `baixado`;
  - o aviso "responsável inativo" na linha;
  - Cumpridas fora da lista padrão, visíveis pelo filtro.
- Painel, para quem pode gerenciar obrigações:
  - um indicador "Obrigações atrasadas" em destaque, com a classe de vencido (RNF-15);
  - o quadro "Obrigações aguardando evidência", com link para cada uma (RF-77);
  - as próximas obrigações dos 15 dias seguintes.
- Montagem: `ServicoObrigacoes(uow, relogio, erros, autorizacao, canal or CanalSimulado())` em `Servicos.obrigacoes`, passado também ao `AgendadorDeVencimentos(obrigacoes=...)`.
- Demonstração, criada pelos serviços e pela verificação automática:
  - "DAS" Fiscal Mensal, prazo hoje + 5, avisado;
  - "FGTS" Trabalhista Mensal, prazo hoje − 3, Atrasada e escalada;
  - "Aluguel da loja" Contratual Mensal, que exige evidência, Aguardando Evidência;
  - "DEFIS" Fiscal Anual, Cumprida com um PDF pequeno, com a próxima ocorrência gerada;
  - "Licença de funcionamento" Outra Única, prazo hoje + 40.

- [ ] **Passo 1: testes de unidade** em `test_multipart.py`: dois campos e um arquivo; `filename*` em UTF-8; parte vazia sem arquivo; `boundary` ausente ou corpo truncado devolvem vazio.
- [ ] **Passo 2: testes web** em `test_spec_010_web.py`, com `tests/apresentacao/cliente_web.py`, que talvez precise de um `postar_multipart(caminho, campos, arquivos)`:
  - `test_fluxo_cadastro_cumprimento_com_pdf_e_proxima_ocorrencia`;
  - `test_erros_por_campo_no_cadastro_e_no_upload`;
  - `test_escape_de_html_no_nome_e_na_descricao`;
  - `test_contador_nao_ve_o_menu_nem_abre_as_rotas` (CA-21, pela tela);
  - `test_CA_22_RNF_15_painel_destaca_atrasadas` e `test_CA_08_RF_77_quadro_aguardando_evidencia_no_painel`;
  - `test_foco_1_download_e_anexo_com_nome_seguro`;
  - `test_foco_2_campo_de_arquivo_vazio_vale_como_sem_anexo`;
  - `test_foco_3_multipart_fora_da_rota_ou_grande_demais_e_recusado`;
  - `test_cumprimento_enviado_duas_vezes_gera_uma_proxima` (E3);
  - `test_demonstracao_tem_obrigacoes_em_todos_os_estados`.
- [ ] **Passo 3: rodar** `python3 -m unittest tests.apresentacao.test_multipart tests.apresentacao.test_spec_010_web -v`. Esperado: falha por `ModuleNotFoundError` e por 404.
- [ ] **Passo 4: implementar.**
- [ ] **Passo 5: rodar** a suíte inteira. Esperado: OK, com `test_ADR_001_cada_camada_importa_somente_as_camadas_permitidas` incluído.
- [ ] **Passo 6: no navegador** (Chromium), com `python3 iniciar.py demonstracao`, em 1280 px e 360 px:
  - calendário, detalhe, cumprimento com upload, download, painel do Dono e do Operador e Mensagens enviadas;
  - sem rolagem horizontal da página.
- [ ] **Passo 7: commit** `feat: telas do calendário de obrigações, upload da evidência e painel (Spec 010)`.

### Tarefa 7: baseline e verificação

**Arquivos:**
- Modificar:
  - `docs/modelo-dominio.md`, `docs/uml/dominio-v2.mmd` e o `.png`: `Obrigacao` ganha `nome`, `diaBase`, `prazoReferencia`, `serie`, `cumprimentoEm`, `alterarPrazo()`, `alterarResponsavel()`, `anexarEvidencia()` e `marcarAtrasada()`; `Evidencia` ganha `nomeArquivo`, `tipoArquivo` e `tamanho`; linha nova no histórico do modelo.
  - `docs/glossario.md`: "Tipo de obrigação", "Periodicidade", "Ocorrência", "Aviso de obrigação" e "Responsável".
  - `docs/uml/estados.md`: as cláusulas de A4, A5 e do prazo que não muda em Atrasada; as transições não mudam.
  - `docs/casos-de-uso/UC-09-gerenciar-obrigacoes.md`: o passo 4 e o A2 deixam de exigir que seja o responsável (OPEN-69).
  - `docs/requisitos.md`: RF-45 e RF-46 passam a "um usuário autorizado registrar"; RB-07 e RB-16 citam OPEN-71.
  - A seção 8 da spec e a situação **Verificada** no mapa.
  - `docs/rastreabilidade.md`, pelo método da sua seção 1.
  - `docs/documentacao-final.md`, `README.md` e `SPECS.md`, com a 010 na situação atual.
  - A pirâmide de `docs/testes.md`.

- [ ] **Passo 1:** atualizar os documentos e regerar os PNG que mudaram. O `mermaid-cli` fica só fora do repositório.
- [ ] **Passo 2: verificar.**
  - Todos os `.mmd` renderizam, e as cópias embutidas são iguais às fontes.
  - Nenhum link relativo está quebrado.
  - A suíte inteira passa.
  - Na recontagem da pirâmide, a unidade não pode cair abaixo dos 36,1% atuais.
- [ ] **Passo 3:** preencher a seção 8 da spec no padrão da Spec 005: uma linha por critério, com o teste e o resultado, mais "Também verificado" e "Onde está cada parte".
- [ ] **Passo 4:** pedir a revisão final da branch a um revisor independente e corrigir o que ele achar.
- [ ] **Passo 5: commit** `docs: registra a verificação da Spec 010 e atualiza a baseline`.
