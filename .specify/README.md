# .specify — Specs, planos e tarefas

Esta pasta guarda o que orienta a implementação. A baseline de modelagem fica em [`/docs`](../docs/README.md); aqui ela é decomposta em unidades implementáveis.

| Pasta ou arquivo | Conteúdo |
|---|---|
| [`specs/mapa-de-specs.md`](specs/mapa-de-specs.md) | Lista ordenada das specs, com rastreabilidade e dependências |
| `specs/NNN-nome.md` | Uma spec: contrato de implementação com critérios de aceite |
| [`specs/modelo-de-spec.md`](specs/modelo-de-spec.md) | Modelo para escrever uma nova spec |
| [`open.md`](open.md) | Questões em aberto (`OPEN-nn`) |
| `plans/` | Plano técnico de cada spec aprovada |
| `tasks/` | Tarefas das Specs 001, 002, 003, 013 e 017, em arquivo próprio (histórico; ver abaixo) |

## Fluxo

1. **Modelagem.** A baseline em `/docs` é revisada e aprovada.
2. **Mapa de specs.** O agente propõe a decomposição e para. A equipe revisa.
3. **Spec.** O agente escreve uma spec por vez. A equipe aprova.
4. **Implementação.** Em um novo contexto do agente, com apenas a spec aprovada e o `SPECS.md`. O código segue a spec.
5. **Verificação.** Testes e critérios de aceite. Divergências são registradas.

### Onde ficam as tarefas

Registrado em 2026-11-19 por Renan Gandolpho. Desde a Spec 018 (plano de 2026-10-31), as tarefas ficam na seção "Tarefas" do próprio plano, cada uma com o que cobre e como se verifica; o plano da Spec 006 já fazia assim. Não se cria mais `tasks/NNN-tarefas.md`. Os arquivos de `tasks/` (Specs 001, 002, 003, 013 e 017) ficam como registro histórico, e não foram criados arquivos retroativos para as Specs 004, 005, 006, 018 e 019.

A Spec 004 não tem plano: a spec e a implementação entraram no mesmo commit, em 2026-10-29, e a aprovação foi registrada depois, em 2026-11-07. A nota está na seção 8 da spec.

## Situações de uma spec

| Situação | Significado |
|---|---|
| Proposta | Escrita, aguardando revisão da equipe |
| Aprovada | Revisada; pode ser implementada |
| Em implementação | Há issue e branch abertas |
| Verificada | Todos os critérios de aceite passaram |

Nenhuma spec é implementada antes de estar Aprovada. A aprovação é registrada na própria spec, com data e nomes de quem aprovou.
