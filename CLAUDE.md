# CLAUDE.md — Constituição do projeto RemindMe

Instruções permanentes para agentes de codificação neste repositório. Valem para qualquer agente; quem usa outra ferramenta deve apontar seu arquivo de instruções para este.

## O projeto

RemindMe é um sistema web de gestão do ciclo de recebíveis e das obrigações de micro e pequenas empresas. É o projeto da disciplina Modelagem de Software (Mackenzie, 2026-2), desenvolvido por Spec-Driven Development.

Situação atual: baseline de modelagem escrita; mapa de specs proposto; Spec 006 aprovada, implementada e verificada (Python 3.11, biblioteca padrão); demais specs a escrever.

## Fonte de verdade

Leia antes de propor qualquer coisa, nesta ordem:

1. [`docs/visao.md`](docs/visao.md) e [`docs/personas.md`](docs/personas.md) — que valor o sistema entrega e para quem.
2. [`docs/requisitos.md`](docs/requisitos.md) — RF, RNF e RB.
3. [`docs/glossario.md`](docs/glossario.md) — vocabulário obrigatório.
4. [`docs/modelo-dominio.md`](docs/modelo-dominio.md) e [`docs/uml/estados.md`](docs/uml/estados.md) — entidades, relações e transições.
5. [`docs/casos-de-uso/`](docs/casos-de-uso/README.md) — fluxos, alternativas e exceções.
6. [`docs/arquitetura.md`](docs/arquitetura.md) e [`docs/adr/`](docs/adr/README.md) — decisões que restringem a solução.
7. [`.specify/open.md`](.specify/open.md) — o que ainda não foi decidido.

## Fluxo de trabalho obrigatório

1. **Mapa de specs.** Propor a decomposição em [`.specify/specs/mapa-de-specs.md`](.specify/specs/mapa-de-specs.md) e parar.
2. **Revisão humana** do mapa.
3. **Uma spec por vez**, pelo [modelo](.specify/specs/modelo-de-spec.md). Escrever somente a spec pedida e parar.
4. **Aprovação humana** da spec, registrada na própria spec.
5. **Implementação** em novo contexto, com a spec aprovada e este arquivo. Código mínimo para atender aos critérios de aceite.
6. **Verificação**: testes, invariantes e RNF aplicáveis. Registrar o resultado na seção 8 da spec.

## Regras não negociáveis

1. Não gerar código sem uma spec com situação Aprovada.
2. Não preencher lacunas. Decisão ausente vira `OPEN-nn` em `.specify/open.md`, e a pergunta volta para a equipe.
3. Não escolher linguagem, framework, banco, biblioteca ou provedor que esteja em aberto.
4. Não alterar a baseline (`docs/`) para acomodar o código. Se a spec ou a baseline parecer errada, propor a alteração e aguardar aprovação.
5. Spec e código mudam no mesmo PR.
6. Usar somente os termos do glossário, em documentos e em código.
7. Não reaproveitar identificadores. Requisito retirado fica marcado como retirado.
8. Toda regra de negócio é implementada no domínio, em um único ponto, com teste nomeado pelo identificador (`RB-nn_...`).
9. O domínio não depende de framework, banco, canal de notificação nem serviço de IA (ADR-001).
10. A IA do produto extrai e classifica; o sistema decide (ADR-003).
11. A suíte de testes roda sem credencial externa (RNF-23).
12. Uma spec não é "implementar backend" nem "criar banco": termina em comportamento verificável.

## Durante a implementação

| Situação | O que fazer |
|---|---|
| O código viola a spec | Corrigir o código |
| A spec parece errada | Parar e propor a alteração para aprovação |
| Falta decisão técnica | Registrar `OPEN-nn` e perguntar |
| A spec conflita com a baseline | Registrar o conflito e perguntar; não escolher um lado |

## Ações do agente

| Veredito | Ações |
|---|---|
| Permitido | Ler arquivos do repositório, rodar testes e lint, `git status`, `git diff`, `git log` |
| Perguntar antes | `git commit`, `git push`, instalar ou atualizar dependência, criar ou alterar migração de banco, apagar arquivo |
| Proibido | Ler `.env`, `mcp.env` ou qualquer arquivo de segredo; `git push --force`; reescrever histórico; `DROP` ou `TRUNCATE`; colocar senha, chave ou token em arquivo versionado |

Detalhes em [`docs/seguranca.md`](docs/seguranca.md).

## Convenções

- Idioma: português, em documentos, issues, PRs e mensagens de commit.
- Identificadores: `RF-nn`, `RNF-nn`, `RB-nn`, `UC-nn`, `DA-nn`, `DT-nn`, `ADR-nnn`, `OPEN-nn`, spec `NNN`.
- Branch: `feature/<número-da-issue>-descricao` ou `docs/<número-da-issue>-descricao`.
- Commit: prefixo `docs:`, `feat:`, `fix:`, `test:`, `refactor:` ou `chore:`, seguido de frase curta no imperativo.
- PR: pequeno, referencia a issue com `Closes #N`, cita os identificadores atendidos e declara o uso de agente.
- Diagramas: fonte Mermaid em `docs/uml/*.mmd`, com a imagem exportada ao lado. O texto é a fonte; o diagrama é uma vista.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `docs/` | Baseline de modelagem e arquitetura |
| `.specify/specs/` | Mapa de specs e specs |
| `.specify/plans/` | Plano técnico de cada spec aprovada |
| `.specify/tasks/` | Tarefas derivadas de cada plano |
| `.specify/open.md` | Questões em aberto |
| `src/remindme/` | Código, em camadas: `dominio`, `aplicacao`, `infraestrutura` |
| `tests/` | Testes `unittest`: `python3 -m unittest discover -s tests -t .` |
