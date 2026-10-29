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
| 3. Arquitetura e decisões | [Arquitetura](docs/arquitetura.md), [ADRs](docs/adr/README.md), [constituição](SPECS.md), [segurança](docs/seguranca.md) | Proposto; Python 3.11 só com a biblioteca padrão, WSGI e SQLite (OPEN-01, OPEN-02) |
| 4. Implementação e validação | [Mapa de specs](.specify/specs/mapa-de-specs.md), [Spec 006](.specify/specs/006-titulo-pagamento-baixa-e-estorno.md), [qualidade](docs/qualidade/README.md), [rastreabilidade](docs/rastreabilidade.md) | Specs 001, 002 e 006 verificadas; Specs 003 e 017 (interface web) implementadas, aguardando aprovação |

As decisões que ainda dependem da equipe estão em [questões em aberto](.specify/open.md).

## Documentação

Toda a documentação está em [`/docs`](docs/README.md). O índice indica a ordem de leitura.

## Como executar

Requer só Python 3.11 ou mais recente. Não há nada para instalar: o sistema usa apenas a biblioteca padrão (servidor WSGI e banco SQLite).

Para ver o sistema funcionando com dados de exemplo:

```bash
python3 executar.py demo --senha demo12345
```

```bash
python3 executar.py servir
```

Abra <http://127.0.0.1:8000> e entre com um dos usuários abaixo (senha `demo12345`):

| Perfil | E-mail |
|---|---|
| Administrador | `admin@remindme.local` |
| Dono | `dona@remindme.local` |
| Operador Financeiro | `operador@remindme.local` |
| Contador | `contador@remindme.local` |

Para começar do zero, sem dados de exemplo, crie o primeiro Administrador e depois inicie o servidor:

```bash
python3 executar.py criar-admin --nome "Seu Nome" --email voce@empresa.com.br
```

Testes:

```bash
python3 -m unittest discover -s tests -t .
```

Detalhes, opções e publicação em [`docs/execucao.md`](docs/execucao.md).

### O que a aplicação faz hoje

- Login com sessão no servidor, senha com `scrypt` e permissões por perfil, negadas por padrão (Spec 002).
- Painel com valores a receber, títulos vencidos e próximos do vencimento.
- Clientes com CPF ou CNPJ validado (Spec 003).
- Títulos: cadastro, filtros, pagamento parcial ou integral, baixa automática, estorno (só o Dono), cancelamento (só o Dono) e verificação automática de vencimentos (Spec 006).
- Auditoria imutável de toda operação, com consulta e filtros (Spec 001).
- Administração de usuários e da matriz de permissões.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| [`docs/`](docs/README.md) | Visão, requisitos, modelagem, arquitetura e combinados |
| [`.specify/`](.specify/README.md) | Mapa de specs, specs, planos, tarefas e questões em aberto |
| [`SPECS.md`](SPECS.md) | Constituição: regras para agentes de codificação |
| [`executar.py`](executar.py) | Atalho para rodar a aplicação sem instalar nada |
| [`src/`](src/README.md) | Código |
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
