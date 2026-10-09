# Documentação — RemindMe

A documentação está organizada em dois conjuntos, sem redundância: requisitos e modelagem, e arquitetura. Leia na ordem abaixo.

Para uma leitura única e resumida, veja a [documentação final consolidada](documentacao-final.md).

## 1. Problema e contexto

| Documento | Conteúdo |
|---|---|
| [Visão](visao.md) | Problema, público-alvo, solução, escopo, critérios de sucesso |
| [Benchmark](benchmark.md) | Soluções existentes e a lacuna que o projeto ocupa |
| [Personas](personas.md) | Quatro personas, uma por perfil |

## 2. Requisitos e modelagem

| Documento | Conteúdo |
|---|---|
| [Requisitos](requisitos.md) | RF e RNF em EARS; RB declarativas |
| [Glossário](glossario.md) | Vocabulário do domínio |
| [Modelo de domínio](modelo-dominio.md) | Classes, responsabilidades, relações e multiplicidades |
| [Estados](uml/estados.md) | Ciclos de vida de orçamento, título e obrigação |
| [Casos de uso](casos-de-uso/README.md) | 14 casos de uso, diagrama e cobertura dos requisitos |

## 3. Arquitetura e decisões

| Documento | Conteúdo |
|---|---|
| [Arquitetura](arquitetura.md) | Drivers, decisões técnicas, camadas e módulos |
| [ADRs](adr/README.md) | Decisões caras de reverter |
| [Segurança](seguranca.md) | Segurança do produto e do uso de agentes |
| [Testes](testes.md) | Estratégia de testes e definição de pronto |
| [Qualidade](qualidade/README.md) | Avaliação pela ISO/IEC 25010, testes e revisão de código |

## 4. Trabalho da equipe

| Documento | Conteúdo |
|---|---|
| [Combinados](combinados.md) | Regras de trabalho da equipe |
| [Execução](execucao.md) | Como instalar e rodar |
| [Mapa de specs](../.specify/specs/mapa-de-specs.md) | Unidades de implementação, em ordem |
| [Questões em aberto](../.specify/open.md) | Decisões que ainda dependem da equipe |

## Diagramas

Os diagramas ficam em [`uml/`](uml/), cada um com a fonte em Mermaid (`.mmd`) e a imagem exportada (`.png`). O texto é a fonte; o diagrama é uma vista.

| Diagrama | Fonte | Imagem |
|---|---|---|
| Classes do domínio | [`dominio-v2.mmd`](uml/dominio-v2.mmd) | [`dominio-v2.png`](uml/dominio-v2.png) |
| Casos de uso | [`casos-de-uso.mmd`](uml/casos-de-uso.mmd) | [`casos-de-uso.png`](uml/casos-de-uso.png) |
| Sequência do UC-04 | [`seq-UC-04.mmd`](uml/seq-UC-04.mmd) | [`seq-UC-04.png`](uml/seq-UC-04.png) |
| Sequência do UC-06 | [`seq-UC-06.mmd`](uml/seq-UC-06.mmd) | [`seq-UC-06.png`](uml/seq-UC-06.png) |
| Estados do título | [`estados-titulo.mmd`](uml/estados-titulo.mmd) | [`estados-titulo.png`](uml/estados-titulo.png) |
| Estados do orçamento | [`estados-orcamento.mmd`](uml/estados-orcamento.mmd) | [`estados-orcamento.png`](uml/estados-orcamento.png) |
| Estados da obrigação | [`estados-obrigacao.mmd`](uml/estados-obrigacao.mmd) | [`estados-obrigacao.png`](uml/estados-obrigacao.png) |

## Identificadores

`RF-nn` requisito funcional · `RNF-nn` requisito não funcional · `RB-nn` regra de negócio · `UC-nn` caso de uso · `DA-nn` driver arquitetural · `DT-nn` decisão técnica · `ADR-nnn` registro de decisão · `OPEN-nn` questão em aberto · `NNN` spec.
