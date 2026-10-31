# Segurança de Acesso e Isolamento de Dados — RemindMe

Issue #75. Subcaracterística **Segurança de acesso** (Adequação funcional, ISO/IEC 25010): dados e funções protegidos contra acesso não autorizado. Casos do Banco Inter (2020), do Yahoo! (2013-2014) e do bot do McDonald's (2025) mostram o custo de expor dados de outro usuário. O foco aqui é só autorização, isolamento e exposição de dados; as regras de negócio estão em outras avaliações.

- **Data:** 2026-10-16.
- **Objeto:** Spec 006 (operações do Dono, OPEN-16).
- **Requisitos e regras:** RNF-01, RNF-02, RNF-03, RNF-06, RNF-22, RNF-25, RB-02, RB-03, RB-30; ADR-004; [`seguranca.md`](../seguranca.md).
- **Testes:** [`tests/aplicacao/test_seguranca_de_acesso.py`](../../tests/aplicacao/test_seguranca_de_acesso.py) (20 testes: 15 passam, 5 pulados).

## 1. Matriz perfil × operação

Resultado esperado de cada célula, como registrado antes da Spec 002. *Nota de 2026-10-31: a coluna Cliente é histórica; o perfil foi retirado (OPEN-57, Spec 018), e a linha da RB-26 abaixo também.* Os perfis eram os cinco de `dominio/usuario.py`. "Sem restrição" é o que a Spec 006 define (seção 7: "a autorização geral, inclusive RB-03, é da Spec 002"); a célula está registrada e **não é a regra final**.

| Operação | Dono | Operador Financeiro | Contador | Cliente | Administrador | Regra |
|---|---|---|---|---|---|---|
| Estornar pagamento | Permitido | **Negado** | **Negado** | **Negado** | **Negado** | RB-02, RF-30 |
| Cancelar título | Permitido | **Negado** | **Negado** | **Negado** | **Negado** | OPEN-16 (2026-10-03) |
| Cadastrar título | sem restrição | sem restrição | sem restrição (deveria ser negado, RB-03) | sem restrição (deveria ser negado) | sem restrição | Spec 002 |
| Registrar pagamento | sem restrição | sem restrição | sem restrição (deveria ser negado, RB-03) | sem restrição (deveria ser negado) | sem restrição | Spec 002 |
| Verificar vencimentos | sem restrição | sem restrição | sem restrição | sem restrição | sem restrição | Spec 008 (agendador) |

A matriz também está no código do teste (`MATRIZ`), e um teste confere que ela cobre os cinco perfis para toda operação. A matriz de operações futuras (aprovar desconto, configurar regras, consultar auditoria) será acrescentada quando as Specs 004, 013 e 014 forem aprovadas.

**Achado (G-01).** Hoje, um Contador ou um Cliente que chame o serviço consegue cadastrar título e registrar pagamento, porque a Spec 006 deixou a autorização geral para a Spec 002. Não é defeito da Spec 006, mas **precisa estar resolvido antes de existir interface** (RB-03, RNF-02: negar por padrão). A Spec 002 deve fechar essas células.

## 2. Casos de teste

| Critério da issue | Teste | Resultado |
|---|---|---|
| Matriz montada, com resultado por célula | `MATRIZ` e `test_RNF_02_a_matriz_cobre_todos_os_perfis_...` | Feito |
| Um teste por célula negada, chamando a operação direto, sem interface (RNF-03); a recusa não altera o título nem a auditoria | `test_RNF_02_cada_celula_negada_recusa_a_operacao_...` (8 células) | Passou |
| Negar por padrão: um perfil que não existe no enum também é negado (RNF-02) | `test_RNF_02_negar_por_padrao_...` | Passou |
| Células permitidas executam | `test_RNF_02_cada_celula_permitida_executa_a_operacao` | Passou |
| A recusa informa o motivo (RF-67) | `test_RF_67_a_recusa_informa_o_motivo` | Passou |
| A permissão é verificada antes do estado e do motivo (quem não pode não descobre mais nada) | `test_RNF_02_a_permissao_e_verificada_antes_...` | Passou |
| Recusa por perfil não revela se o título existe (mesma mensagem para título real e inexistente) | `test_RNF_25_recusa_por_perfil_nao_revela_...` | Passou |
| A mensagem de recusa não contém id do título, id do pagamento, valor nem cliente | `test_RNF_25_a_mensagem_de_recusa_nao_contem_dados_do_titulo` | Passou |
| Tentativa de alterar registro de auditoria: o registro é imutável (`dataclass` congelada) | `test_RNF_06_registro_de_auditoria_nao_pode_ser_alterado` | Passou |
| Tentativa de excluir ou alterar pela porta: ela só oferece `registrar` (ADR-004, RB-30) | `test_RB_30_a_porta_de_auditoria_so_oferece_incluir`, `..._a_auditoria_em_memoria_...`, `..._o_servico_nao_oferece_...` | Passou |
| Recusa não apaga nem reescreve a auditoria anterior | `test_RB_01_recusa_nao_apaga_...` | Passou |

## 3. Fragilidade registrada: S-01

A lista `AuditoriaEmMemoria.registros` é pública e mutável. Ela é um dublê de teste, não o adaptador real, mas quem tiver o objeto pode apagá-la. O que impede alteração e exclusão é a **interface da porta** (só `registrar`) e a imutabilidade do registro. Para o armazenamento real, a garantia (por exemplo, permissão de banco só de inclusão) é da persistência escolhida em OPEN-02. O teste `test_ADR_004_provisorio_...` apenas documenta o fato.

## 4. Pendente, sem código antecipado (regra 1 do CLAUDE.md)

| Caso | Depende de | Teste registrado como pulado |
|---|---|---|
| Contador não cria nem altera registro; perfil sem permissão explícita é negado em cadastro e pagamento (RB-03, RNF-02) | Spec 002 | `test_RB_03_contador_nao_cadastra_...` |
| Cliente tenta acessar título de outro cliente e é recusado (RNF-25, RB-26) | Specs 002 e 009 (hoje o serviço não conhece o vínculo usuário–cliente) | `test_RNF_25_cliente_nao_acessa_...` |
| Acesso sem sessão é recusado (RNF-01) | Spec 002, OPEN-03 | `test_RNF_01_acesso_sem_sessao_...` |
| Payload enviado à IA simulada não contém nome, documento nem contato (RNF-22) | Specs 009 e 011; simulador de IA ([`testes.md`](../testes.md), #79) | `test_RNF_22_payload_da_ia_...` |
| Nenhum perfil exclui registro de auditoria no armazenamento real (RNF-06) | Spec 013, OPEN-02 | `test_RNF_06_perfil_nenhum_exclui_...` |
