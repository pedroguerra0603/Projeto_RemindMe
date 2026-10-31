# Plano da Spec 018 — Contas a pagar, fornecedores e retirada do perfil Cliente

> **Para agentes:** executar tarefa a tarefa, com TDD (teste falhando → código mínimo → suíte verde → commit). Execução escolhida: o próprio agente, nesta sessão (autorizada por Renan Gandolpho em 2026-10-31).

**Objetivo:** registrar contas a pagar a fornecedores ao lado dos títulos a receber, e tirar o perfil Cliente do controle de acesso.

**Arquitetura:** `ContaPagar` é um agregado próprio que espelha o `Titulo` (Spec 006), reaproveitando `Pagamento` e as validações monetárias, que passam a um módulo comum. `Fornecedor` reaproveita a validação de nome, documento e contato do `Cliente`. Novos serviços de aplicação passam pela `Execucao` (transação, permissão, auditoria). A persistência ganha a migração 4. A interface ganha rotas e páginas no mesmo estilo de títulos e clientes.

**Tecnologia:** Python 3.11+, só a biblioteca padrão, `unittest`, SQLite, WSGI (ADR-006, ADR-007).

**Spec:** [`../specs/018-contas-a-pagar-e-fornecedores.md`](../specs/018-contas-a-pagar-e-fornecedores.md)

## Restrições globais

- Termos do glossário em código e telas: Fornecedor, Conta a pagar, Aberta, Vencida, Paga, Cancelada, Pagamento, Saldo, Estorno.
- Valores: `Decimal`, até duas casas e 15 dígitos inteiros, sem arredondamento (OPEN-20, OPEN-24). Data de pagamento futura é recusada (OPEN-17).
- Toda regra no domínio, em um único ponto; testes de regra levam o identificador no nome (`test_RB_31_...`).
- Nenhuma dependência nova. A migração não usa `DROP` nem `TRUNCATE`.

## Foco de revisão

1. Banco antigo (versão 3) aberto pela versão nova: a migração 4 precisa criar as tabelas e dar as permissões novas a Dono e Operador, como na matriz inicial. Teste: `test_CA_17_banco_antigo_ganha_tabelas_e_permissoes`.
2. Estorno de pagamento de conta Cancelada e cancelamento de conta Paga: recusados (como OPEN-18 e E6 da Spec 006). Teste: `test_E5_*`.
3. Pedido de pagamento repetido pela tela (duplo clique): ignorado pelo `pedido_id` (OPEN-25). Teste web: `test_pagamento_de_conta_enviado_duas_vezes_registra_um`.
4. Fornecedor e cliente com o mesmo CNPJ: permitido (são cadastros diferentes; a mesma empresa pode comprar e vender). Teste: `test_fornecedor_pode_ter_o_documento_de_um_cliente`.
5. Contador abrindo os formulários de cadastro pela URL: negado com 403 (RB-03). Teste no CA-13.

---

### Tarefa 1: retirar o perfil Cliente

**Arquivos:** `dominio/usuario.py`, `dominio/regras.py`, `apresentacao/web/paginas.py`, `infraestrutura/sqlite.py` (migração 4 apaga linhas de permissão do perfil `CLIENTE`, se houver); testes em `tests/dominio`, `tests/aplicacao/test_seguranca_de_acesso.py`, `tests/integracao`.

- [ ] Teste: `Perfil` tem exatamente Dono, Operador Financeiro, Contador e Administrador; a página de Permissões não tem "Cliente" (CA-16, INV-7).
- [ ] Ver falhar; remover `Perfil.CLIENTE`, a regra fixada RB-26 e o tratamento de `perfil_recusado`; ajustar os testes que citavam o Cliente.
- [ ] Suíte verde; commit `refactor: retira o perfil Cliente do controle de acesso (OPEN-57)`.

### Tarefa 2: validações comuns e Fornecedor

**Arquivos:** criar `dominio/valores.py` (`recusar_campo`, `exigir_valor_monetario(valor, sujeito)`, `exigir_motivo(motivo, operacao)`), usado por `titulo.py`; em `dominio/cliente.py`, `validar_pessoa(nome, documento, contato, sujeito) -> Tuple[str, str, str]`; criar `dominio/fornecedor.py` (`Fornecedor(id, nome, documento, contato)`, `cadastrar`, `alterado`); `aplicacao/servico_fornecedores.py` (`cadastrar_fornecedor`, `alterar_fornecedor`, `consultar_fornecedores(termo)`, `obter_fornecedor`); `RepositorioFornecedores` em `portas.py`, `memoria.py` e `sqlite.py`; operações `MANTER_FORNECEDORES` e `CONSULTAR_FORNECEDORES`.

- [ ] Testes `tests/aplicacao/test_spec_018_aceite.py`: CA-01, CA-02, foco 4, A6 (auditoria por campo).
- [ ] Ver falhar; implementar; suíte verde (a Spec 006 não pode regredir com o módulo `valores`); commit.

### Tarefa 3: ContaPagar e serviço

**Arquivos:** `dominio/conta_pagar.py` (`EstadoContaPagar` ABERTA/VENCIDA/PAGA/CANCELADA; `ContaPagar(id, fornecedor_id, descricao, valor, vencimento, condicao_pagamento, estado, pagamentos)` com `cadastrar`, `saldo`, `registrar_pagamento(pagamento_id, valor, data, hoje, pedido_id)`, `marcar_vencida(data_referencia)`, `estornar_pagamento(pagamento_id, motivo, data_referencia)`, `cancelar(motivo)`); `aplicacao/servico_contas_pagar.py` (`cadastrar_conta`, `registrar_pagamento`, `estornar_pagamento`, `cancelar_conta`, `consultar_contas(FiltroContas)`, `obter_conta`, `verificar_vencimentos_automaticamente`); operações `CADASTRAR_CONTA_PAGAR`, `PAGAR_CONTA`, `ESTORNAR_PAGAMENTO_CONTA`, `CANCELAR_CONTA_PAGAR`, `CONSULTAR_CONTAS_PAGAR`; RB-33 em `_SOMENTE_O_DONO`; RB-03 em `_CONTADOR_NAO_ALTERA`; matriz inicial: D,O nas de manter/cadastrar/pagar; D,O,C nas de consulta; D no estorno e no cancelamento.

- [ ] Testes de domínio `tests/dominio/test_conta_pagar.py` (RB-31, RB-32, INV-1 a INV-4) e de aceite CA-03 a CA-13, foco 2.
- [ ] Ver falhar; implementar; suíte verde; commit.

### Tarefa 4: persistência e agendador

**Arquivos:** `infraestrutura/sqlite.py` (migração 4: `fornecedores`, `contas_pagar`, `pagamentos_conta`; permissões novas para bancos antigos), `infraestrutura/memoria.py`, `entradas/agendador.py` (também vence contas), `inicializacao.py` (monta os serviços), `apresentacao/web/aplicacao_web.py` (`Servicos` com `fornecedores` e `contas_pagar`).

- [ ] Testes em `tests/infraestrutura/test_sqlite.py`: ida e volta de fornecedor e conta com pagamentos; CA-17 (foco 1); CA-08 pelo agendador.
- [ ] Ver falhar; implementar; suíte verde; commit.

### Tarefa 5: telas e painel

**Arquivos:** `apresentacao/web/aplicacao_web.py` (rotas `/fornecedores`, `/fornecedores/novo`, `/fornecedores/{id}`, `/fornecedores/{id}/editar`, `/contas-a-pagar`, `/contas-a-pagar/nova`, `/contas-a-pagar/{id}`, `/contas-a-pagar/{id}/pagamentos`, `/contas-a-pagar/{id}/pagamentos/{pid}/estorno`, `/contas-a-pagar/{id}/cancelamento`), `apresentacao/web/paginas.py` (menu "Contas a pagar" e "Fornecedores"; páginas; `_descrever` da auditoria reconhece `fornecedor` e `conta_pagar`; régua do caixa com a linha "A pagar" e o "Saldo previsto"), `demonstracao.py` (3 fornecedores; contas Aberta, Vencida, Paga, parcial, estornada e Cancelada).

- [ ] Testes `tests/apresentacao/test_spec_018_web.py`: CA-14, CA-15, CA-16, foco 3 e 5; demonstração com todos os estados de conta.
- [ ] Ver falhar; implementar; suíte verde; commit.

### Tarefa 6: verificação

- [ ] Suíte completa; navegador real (celular 360 px e computador) nas telas novas; Lighthouse nas páginas novas.
- [ ] Preencher a seção 8 da spec; atualizar `SPECS.md` (situação) e `docs/execucao.md` (demonstração); commit e push.
