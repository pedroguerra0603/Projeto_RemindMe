# RemindMe

Sistema web de gestão do ciclo de recebíveis e das obrigações de micro e pequenas empresas.

Projeto final da disciplina Modelagem de Software · Universidade Presbiteriana Mackenzie · 2026-2 · Turma 04I

## Objetivo

Pequenas empresas raramente têm um back-office. Orçamento aprovado não vira cobrança, título vencido não é cobrado, prazo fiscal é perdido e o resultado do mês chega com meses de atraso. O problema não é falta de sistema contábil: é falta de rotina com regra.

O RemindMe garante que cada cobrança e cada obrigação avance no prazo, com registro de quem fez o quê e quando:

- **Ciclo de recebíveis.** O orçamento é criado, validado contra a alçada de desconto, enviado, aprovado, convertido em título, cobrado por uma régua automática, renegociado quando necessário e baixado.
- **Calendário de obrigações.** Compromissos fiscais e contratuais com aviso antecipado, evidência de cumprimento e escalonamento ao dono.
- **Apuração do resultado.** Derivada dos lançamentos que a própria operação gera.

O sistema tem quatro perfis: Dono, Operador Financeiro, Cliente e Contador. A inteligência artificial é usada em dois pontos, sob um princípio: **a IA extrai e classifica; o sistema decide.**

Detalhes em [visão do produto](docs/visao.md).

## Situação do projeto

| Fase | Entregáveis | Situação |
|---|---|---|
| 1. Problema e contexto | [Visão](docs/visao.md), [benchmark](docs/benchmark.md), [personas](docs/personas.md) | Escrito |
| 2. Requisitos e modelagem | [Requisitos](docs/requisitos.md), [glossário](docs/glossario.md), [modelo de domínio](docs/modelo-dominio.md), [casos de uso](docs/casos-de-uso/README.md) | Escrito |
| 3. Arquitetura e decisões | [Arquitetura](docs/arquitetura.md), [ADRs](docs/adr/README.md), [constituição](CLAUDE.md), [segurança](docs/seguranca.md) | Proposto; tecnologias em aberto |
| 4. Implementação e validação | [Mapa de specs](.specify/specs/mapa-de-specs.md), [Spec 006](.specify/specs/006-titulo-pagamento-baixa-e-estorno.md) | Mapa e primeira spec propostos; sem código |

As decisões que ainda dependem da equipe estão em [questões em aberto](.specify/open.md).

## Documentação

Toda a documentação está em [`/docs`](docs/README.md). O índice indica a ordem de leitura.

## Como executar

Ainda não há código executável. As instruções ficarão em [`docs/execucao.md`](docs/execucao.md).

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| [`docs/`](docs/README.md) | Visão, requisitos, modelagem, arquitetura e combinados |
| [`.specify/`](.specify/README.md) | Mapa de specs, specs, planos, tarefas e questões em aberto |
| [`CLAUDE.md`](CLAUDE.md) | Constituição: regras para agentes de codificação |
| [`src/`](src/README.md) | Código |
| [`tests/`](tests/README.md) | Testes |

## Como contribuir

O fluxo é issue → branch → PR revisado → merge. As regras estão em [combinados da equipe](docs/combinados.md).

## Equipe

| Integrante | GitHub |
|---|---|
| João Pedro Silva Guerra | [@pedroguerra0603](https://github.com/pedroguerra0603) |
| Bernardo Sanches | [@besanchess](https://github.com/besanchess) |
| Renan Ribeiro Gandolpho | |

Professor: Nilton Canto
