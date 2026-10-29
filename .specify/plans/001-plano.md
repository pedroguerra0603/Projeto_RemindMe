# Plano técnico — Spec 001

Spec: [001 — Fundação: estrutura em camadas e auditoria de operações](../specs/001-fundacao-camadas-e-auditoria.md).

## Tecnologia

- Python 3.11, somente a biblioteca padrão, como na Spec 006 (OPEN-01).
- Testes com `unittest`. Nenhuma dependência a instalar.
- Persistência em memória. O banco continua em aberto (OPEN-02); os testes de aceite serão repetidos sobre o adaptador real.
- Registro de erro no `logging` da biblioteca padrão, por padrão. O pacote `remindme` registra um `NullHandler`; quem executa a aplicação configura a saída do log.

## Organização

| Camada | Módulo | Conteúdo |
|---|---|---|
| Domínio | `src/remindme/dominio/auditoria.py` | `RegistroAuditoria` imutável, com `campo`, `automatica` e `rotina`; valida INV-3 na criação |
| Aplicação | `src/remindme/aplicacao/auditoria.py` | Ponto único de gravação (INV-5): `OperacaoAuditada` grava os registros; `RegistroErrosNoLog` |
| Aplicação | `src/remindme/aplicacao/execucao.py` | Desde a Spec 002: `Execucao` abre a transação, verifica o acesso, entrega a `OperacaoAuditada` e trata recusa e erro não tratado (no início desta spec, isso ficava na classe `Auditoria`) |
| Aplicação | `src/remindme/aplicacao/portas.py` | `RegistroErro` e a porta `RegistroErros`, fora da transação |
| Aplicação | `src/remindme/aplicacao/servico_titulos.py` | Operações da Spec 006 passam pelo ponto único (hoje, `Execucao`) |
| Infraestrutura | `src/remindme/infraestrutura/memoria.py` | `AuditoriaEmMemoria` com leitura somente por cópia; `RegistroErrosEmMemoria` |

## Decisões locais

- **Um registro por registro afetado e por campo alterado.** O modelo de domínio dá ao `RegistroAuditoria` um único valor anterior e um único novo valor. Uma operação que altere dois campos do mesmo registro gera dois registros. Nenhuma operação atual altera mais de um campo do mesmo registro.
- **Referência ao registro afetado.** Texto `titulo <id>` para o título e `titulo <id>, pagamento <id>` para o pagamento: o pagamento existe dentro do título, e a Spec 006 (CA-22) pede o título afetado no registro do pagamento.
- **Campos auditados.** Criação de título: `estado`, de vazio para Aberto (A1). Pagamento: `valor`, de vazio para o valor pago. Estorno: `estornado`, de "não" para "sim", com o motivo (A3). Mudança de estado do título: `estado`, com a operação "mudar estado" (A2).
- **Ordem dentro da transação.** O domínio executa, a auditoria é gravada e o título é gravado por último. Assim, uma falha na gravação do título acontece depois de a auditoria ser gravada e desfaz os dois (E3, CA-06).
- **Operação automática.** `verificar_vencimentos_automaticamente(data)` é a rotina "verificação de vencimento" (A4, OPEN-30). Chamada por um usuário, `verificar_vencimentos(sessao, data)` registra o usuário. Operação sem usuário e sem rotina é recusada pela própria aplicação. (Antes da Spec 002, a rotina automática era `verificar_vencimentos(None, data)`.)
- **Recusa e erro.** `OperacaoRecusada` desfaz a transação e não deixa registro algum (E1). Qualquer outra exceção desfaz a transação, grava um `RegistroErro` com data e hora, operação, usuário e identificador de correlação, acrescenta o identificador às notas da exceção e a repassa a quem chamou (E2, E3, E5).
- **Imutabilidade.** `RegistroAuditoria` é `dataclass` congelada. `AuditoriaEmMemoria.registros` é uma propriedade sem atribuição que devolve uma cópia da lista: apagar itens da cópia não altera o armazenado (CA-07, CA-08). A garantia no armazenamento real é da persistência escolhida em OPEN-02.
- **CA-13.** Verificado de duas formas: teste que confirma que `src/` não lê variável de ambiente e que o fluxo de CI não usa segredo; e execução da suíte com o ambiente vazio (`env -i`).

## Tarefas

Em [`../tasks/001-tarefas.md`](../tasks/001-tarefas.md).
