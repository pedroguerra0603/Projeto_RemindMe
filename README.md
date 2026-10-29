# RemindMe

Sistema web de gestão do ciclo de recebíveis e das obrigações de micro e pequenas empresas.

Projeto final da disciplina Modelagem de Software · Universidade Presbiteriana Mackenzie · 2026-2 · Turma 04I

## Objetivo

Pequenas empresas raramente têm um back-office. Orçamento aprovado não vira cobrança, título vencido não é cobrado, prazo fiscal é perdido e o resultado do mês chega com meses de atraso. O problema não é falta de sistema contábil: é falta de rotina com regra.

O RemindMe garante que cada cobrança e cada obrigação avance no prazo, com registro de quem fez o quê e quando:

- **Ciclo de recebíveis.** O orçamento é criado, validado contra a alçada de desconto, enviado, aprovado, convertido em título, cobrado por uma régua automática, renegociado quando necessário e baixado.
- **Calendário de obrigações.** Compromissos fiscais e contratuais com aviso antecipado, evidência de cumprimento e escalonamento ao dono.
- **Apuração do resultado.** Derivada dos lançamentos que a própria operação gera.

O sistema tem quatro perfis de negócio (Dono, Operador Financeiro, Cliente e Contador) e o perfil Administrador, que mantém usuários e configurações. A inteligência artificial é usada em dois pontos, sob um princípio: **a IA extrai e classifica; o sistema decide.**

Detalhes em [visão do produto](docs/visao.md).

## Situação do projeto

| Fase | Entregáveis | Situação |
|---|---|---|
| 1. Problema e contexto | [Visão](docs/visao.md), [benchmark](docs/benchmark.md), [personas](docs/personas.md) | Escrito |
| 2. Requisitos e modelagem | [Requisitos](docs/requisitos.md), [glossário](docs/glossario.md), [modelo de domínio](docs/modelo-dominio.md), [casos de uso](docs/casos-de-uso/README.md) | Escrito |
| 3. Arquitetura e decisões | [Arquitetura](docs/arquitetura.md), [ADRs](docs/adr/README.md), [constituição](SPECS.md), [segurança](docs/seguranca.md) | Tecnologias decididas: Python 3.11 com a biblioteca padrão, interface WSGI (ADR-006) e SQLite (ADR-007) |
| 4. Implementação e validação | [Mapa de specs](.specify/specs/mapa-de-specs.md), [specs](.specify/specs/), [qualidade](docs/qualidade/README.md), [rastreabilidade](docs/rastreabilidade.md) | Specs 001, 002, 003, 006, 013 e 017 verificadas: auditoria, acesso por perfil, clientes, títulos e pagamentos, consulta de auditoria e a interface web. Spec 004 (orçamentos e alçada de desconto) implementada e verificada, aguardando aprovação |

As decisões que ainda dependem da equipe estão em [questões em aberto](.specify/open.md).

## Documentação

Toda a documentação está em [`/docs`](docs/README.md). O índice indica a ordem de leitura.

## Como executar

Com Python 3.11 ou mais recente, sem instalar nada, na raiz do repositório:

```
python3 iniciar.py demonstracao
```

Abra **http://localhost:8000** e entre com `carla@demo.example` (Dono), `diego@demo.example` (Operador Financeiro), `helena@demo.example` (Contador) ou `admin@demo.example` (Administrador). A senha aparece no terminal.

Testes:

```
python3 -m unittest discover -s tests -t .
```

Uso com dados reais, HTTPS e demais opções em [`docs/execucao.md`](docs/execucao.md).

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| [`docs/`](docs/README.md) | Visão, requisitos, modelagem, arquitetura e combinados |
| [`.specify/`](.specify/README.md) | Mapa de specs, specs, planos, tarefas e questões em aberto |
| [`SPECS.md`](SPECS.md) | Constituição: regras para agentes de codificação |
| [`src/`](src/README.md) | Código |
| [`iniciar.py`](iniciar.py) | Atalho para iniciar a aplicação |
| [`tests/`](tests/README.md) | Testes |

## Como contribuir

O fluxo é issue → branch → PR revisado → merge. As regras estão em [combinados da equipe](docs/combinados.md).

## Equipe

| Integrante | GitHub |
|---|---|
| João Pedro Silva Guerra | [@pedroguerra0603](https://github.com/pedroguerra0603) |
| Bernardo Sanches | [@besanchess](https://github.com/besanchess) |
| Renan Ribeiro Gandolpho | [@Renan-Rigan](https://github.com/Renan-Rigan) |

Professor: Nilton Canto
