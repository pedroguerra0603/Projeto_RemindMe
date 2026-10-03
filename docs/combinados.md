# Combinados da Equipe — RemindMe

Regras simples e explícitas para o grupo não travar em discussões repetidas.

> **Rascunho para aprovação.** Os itens marcados com *(a confirmar)* são sugestões. A equipe deve ajustar e aprovar este documento em um PR revisado pelos três integrantes.

## Equipe e papéis

| Integrante | GitHub | Papel |
|---|---|---|
| João Pedro Silva Guerra | [@pedroguerra0603](https://github.com/pedroguerra0603) | Repositório e configurações *(a confirmar)* |
| Bernardo Sanches | [@besanchess](https://github.com/besanchess) | Documentação *(a confirmar)* |
| Renan Ribeiro Gandolpho | *(a informar)* | Backlog e Kanban *(a confirmar)* |

## Comunicação

- Canal oficial: *(a confirmar — por exemplo, grupo de WhatsApp da equipe)*.
- Tempo máximo de resposta: 24 horas em dias úteis *(a confirmar)*.
- Reunião semanal: *(a confirmar dia e horário)*. A pauta é o Kanban.
- Decisão tomada em conversa só vale depois de registrada em issue, PR ou ADR.

## Fluxo de trabalho

1. Todo trabalho nasce em uma **issue** com critério de aceite e responsável.
2. A issue referencia os identificadores que atende: `RF-nn`, `RB-nn`, `UC-nn` ou o número da spec.
3. Cada issue é resolvida em uma **branch** própria: `feature/<número-da-issue>-descricao-curta`. Para documentação, `docs/<número-da-issue>-descricao-curta`.
4. A branch vira um **PR** para `main`, pequeno, que fecha a issue com `Closes #N`.
5. Todo PR é **revisado por um colega** antes do merge. Ninguém aprova o próprio PR.
6. Spec e código mudam no mesmo PR.

## Kanban

Colunas: A fazer, Em andamento, Em revisão, Concluído.

- Uma issue só vai para Em andamento com responsável atribuído.
- Uma issue só vai para Concluído com o PR mesclado.

## Commits

- Mensagem curta, no imperativo, com prefixo: `docs:`, `feat:`, `fix:`, `test:`, `refactor:`, `chore:`.
- Exemplo: `docs: corrige multiplicidade entre Usuario e Perfil (RB-15)`.
- Evitar mensagens como "Atualiza" ou "ajustes".

## Qualidade

- A branch `main` está sempre íntegra: documentos coerentes entre si e, quando houver código, build e testes passando.
- Identificadores não são reaproveitados. Requisito retirado fica marcado como retirado.
- Mudança em requisito, regra ou modelo atualiza os documentos que dependem dele no mesmo PR.

## Decisões

- Escolha importante e cara de reverter vira um ADR curto em [`adr/`](adr/README.md).
- Decisão ainda não tomada vira `OPEN-nn` em [`.specify/open.md`](../.specify/open.md).
- Quando não houver consenso, decide a maioria; o resultado é registrado.

## Uso de agentes de codificação

- Usar o agente é esperado. Esconder o uso é que é problema: o PR declara o que foi feito com o agente.
- Quem abre o PR responde pelo conteúdo, tenha sido escrito por pessoa ou por agente.
- O agente segue o [`CLAUDE.md`](../CLAUDE.md) e a política de [segurança](seguranca.md).
- Cada integrante precisa ter participação própria visível em commits, issues fechadas e revisões.

## Divisão de trabalho

- Cada integrante assume ao menos uma issue por semana e a fecha com evidência.
- Quem não conseguir cumprir avisa no canal oficial antes do prazo, para a issue ser redistribuída.
