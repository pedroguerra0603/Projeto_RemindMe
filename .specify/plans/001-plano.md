# Plano técnico — Spec 001

Spec: [001 — Fundação: estrutura em camadas e auditoria de operações](../specs/001-fundacao-camadas-e-auditoria.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão (OPEN-01, decidida em 2026-10-03), como na Spec 006. `BaseException.add_note`, usado para anexar o identificador de correlação ao erro, existe a partir do Python 3.11.
- Testes com `unittest`. Nenhuma dependência a instalar.
- Persistência em memória: o banco depende de OPEN-02. Os testes de contrato serão repetidos sobre o banco.

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Domínio | `src/remindme/dominio/auditoria.py` | `RegistroAuditoria`, imutável (RB-30), com campo, valor anterior, novo valor, motivo, indicação de operação automática e rotina; valida INV-3 e OPEN-30 ao ser criado |
| Aplicação | `src/remindme/aplicacao/auditoria.py` | `OperacaoAuditada`: abre a transação, oferece à operação a função `auditar`, único ponto que cria e grava `RegistroAuditoria` (INV-5); trata recusa (E1) e erro não tratado (E5). `Alteracao`: um campo alterado de um registro afetado (A5) |
| Aplicação | `src/remindme/aplicacao/portas.py` | Novas: `RegistroErro` e a porta `RegistroErros` (RNF-21). `RepositorioAuditoria` continua só com `registrar` |
| Aplicação | `src/remindme/aplicacao/servico_titulos.py` | As operações da Spec 006 passam por `OperacaoAuditada`; `verificar_vencimentos` aceita usuário vazio (A4) |
| Infraestrutura | `src/remindme/infraestrutura/memoria.py` | `AuditoriaEmMemoria` sem lista pública: leitura por propriedade, com cópias; `RegistroErrosEmMemoria`; unidade de trabalho desfaz a auditoria da transação que falhou |

O domínio não importa aplicação nem infraestrutura, e a aplicação não importa infraestrutura (ADR-001, CA-12).

## Decisões locais

- **Um único ponto de gravação (INV-5).** Cada serviço chama `OperacaoAuditada.executar(usuario, operacao, acao, rotina)`. A `acao` recebe a unidade de trabalho e a função `auditar(Alteracao)`. Só `aplicacao/auditoria.py` cria `RegistroAuditoria`; um teste de arquitetura verifica isso.
- **Ordem dentro da transação.** Mantida a ordem já verificada da Spec 006: o domínio altera, o registro é gravado no repositório, e a auditoria vem logo depois, registro por registro. Na verificação de vencimentos, cada título é gravado e auditado antes do próximo; é esse o caso em que a gravação de um título falha depois de uma auditoria já gravada (CA-06).
- **Data e hora.** Lidas do relógio uma vez por operação; todos os registros da mesma operação têm a mesma data e hora.
- **Formato dos registros.**
  - Cadastro (A1): operação "cadastrar título", registro afetado o título, campo `estado`, sem valor anterior, novo valor "Aberto".
  - Pagamento: operação "registrar pagamento", registro afetado o título (Spec 006, CA-22), campo `pagamento`, novo valor com o identificador e o valor do pagamento.
  - Mudança de estado (A2): operação "mudar estado", campo `estado`, estado anterior e novo, como na Spec 006, cujos testes filtram por essa operação.
  - Estorno (A3, A5): operação "estornar pagamento", registro afetado o pagamento, campo `estornado`, de "não" para "sim", com o motivo; e o registro da mudança de estado do título, quando houver.
- **Operação automática (A4, OPEN-30).** Sem usuário, o registro tem usuário vazio, `automatica` verdadeiro e o nome da rotina. `verificar_vencimentos(None, data)` usa a rotina "verificação de vencimento". Com usuário, a mesma operação não é automática.
- **INV-3 no domínio.** Um `RegistroAuditoria` sem data e hora, operação, registro afetado ou usuário (fora de operação automática) não é criado: levanta `ValueError`, que é erro de programação e não recusa de regra de negócio.
- **Imutabilidade (CA-07, CA-08).** `RegistroAuditoria` é `frozen`. `AuditoriaEmMemoria` guarda uma cópia do registro recebido e devolve, a cada leitura, uma lista nova com cópias. Assim, nem a lista lida nem o objeto lido, mesmo com a imutabilidade contornada, alteram o armazenado. Isso resolve a fragilidade S-01 de `docs/qualidade/seguranca-de-acesso.md`.
- **Desfazer não é excluir.** A unidade de trabalho em memória restaura a lista de auditoria anterior à transação que falhou (E2, E3). Nenhum registro de transação confirmada é removido.
- **Erro não tratado (E5).** Qualquer exceção que não seja `OperacaoRecusada` desfaz a transação, gera um `RegistroErro` com data e hora, operação, usuário e identificador de correlação, e é propagada sem troca. O identificador é anexado ao erro como nota. Se o próprio registro do erro falhar, o erro original continua sendo o que chega a quem chamou.
- **Identificador de correlação e destino do registro de erro.** Ficam atrás da porta `RegistroErros`, com implementação em memória para os testes; o identificador é gerado pela aplicação (`uuid4`). O destino real e a origem do identificador estão em aberto: **OPEN-36**.
- **Porta de erros opcional no serviço.** `ServicoTitulos` recebe `erros` como parâmetro opcional, para não mudar a criação do serviço nos testes da Spec 006. Sem a porta, o erro é desfeito e propagado, mas não registrado. A composição real deve sempre fornecê-la (OPEN-36).
- **Consulta.** `consultar_titulos` não altera dados, não é auditada e não recebe usuário; por isso não passa por `OperacaoAuditada`.
- **CA-13.** Um teste roda a suíte inteira em outro processo, com o ambiente reduzido a `PATH` e às variáveis mínimas do sistema; o processo filho não repete esse teste. Outro teste verifica que `src/remindme/` não lê variável de ambiente.

## Tarefas

1. Domínio: `RegistroAuditoria` com os campos novos e a validação de INV-3 e OPEN-30, com testes.
2. Aplicação: `OperacaoAuditada`, `Alteracao`, `RegistroErro` e a porta `RegistroErros`.
3. Aplicação: as operações da Spec 006 passam a usar `OperacaoAuditada`; `verificar_vencimentos` sem usuário.
4. Infraestrutura: `AuditoriaEmMemoria` sem lista pública e com cópias; `RegistroErrosEmMemoria`.
5. Testes de aceite CA-01 a CA-13 em `tests/aplicacao/test_spec_001_aceite.py`; ajustes nos testes da Spec 006 que dependem do formato da auditoria.
6. Verificação de sensibilidade: erros introduzidos de propósito e desfeitos.
7. Registrar o resultado na seção 8 da spec.
