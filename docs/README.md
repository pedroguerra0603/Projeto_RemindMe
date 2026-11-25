# Documentação — RemindMe

A documentação está organizada em dois conjuntos, sem redundância: requisitos e modelagem, e arquitetura. Leia na ordem abaixo.

Para uma leitura única e resumida, veja a [documentação final consolidada](documentacao-final.md).

## Roteiro para avaliação (cerca de 20 minutos)

A documentação é extensa porque registra cada decisão. Para avaliar a modelagem, estes oito itens bastam, nesta ordem:

| # | O que ler | O que mostra |
|---|---|---|
| 1 | [Documentação final](documentacao-final.md) | Problema, requisitos, modelagem, arquitetura e situação, em uma página |
| 2 | [Casos de uso](casos-de-uso/README.md) e o [diagrama](uml/casos-de-uso.png) | Atores, 16 casos de uso e quais estão implementados |
| 3 | [UC-06](casos-de-uso/UC-06-registrar-pagamento-e-baixar-titulo.md), com a [sequência](uml/seq-UC-06.png) | Um caso de uso completo, do fluxo à transação |
| 4 | [Atividades do UC-04](uml/atividades-UC-04.png) | O processo central, do orçamento ao título, com quem faz cada ação |
| 5 | [Modelo de domínio](modelo-dominio.md) e o [diagrama de classes](uml/dominio-v2.png) | Classes, tipos, multiplicidades, enumerações e restrições |
| 6 | [Estados](uml/estados.md) | Ciclos de vida de título, orçamento, obrigação e conta a pagar |
| 7 | [Arquitetura](arquitetura.md), com [componentes](uml/componentes.png) e [implantação](uml/implantacao.png), e os [ADRs](adr/README.md) | Camadas, decisões e onde o sistema roda |
| 8 | [Rastreabilidade](rastreabilidade.md) | Requisito → caso de uso → classe → spec → teste |

Para ver funcionando: `python3 iniciar.py demonstracao` ([execução](execucao.md)). Os relatórios de [qualidade](qualidade/README.md) são registros datados das rodadas de outubro.

## 1. Problema e contexto

| Documento | Conteúdo |
|---|---|
| [Visão](visao.md) | Problema, público-alvo, solução, escopo, critérios de sucesso |
| [Benchmark](benchmark.md) | Soluções existentes e a lacuna que o projeto ocupa |
| [Personas](personas.md) | Quatro personas: uma por perfil de negócio e o cliente, que não acessa o sistema |

## 2. Requisitos e modelagem

| Documento | Conteúdo |
|---|---|
| [Requisitos](requisitos.md) | RF e RNF em EARS; RB declarativas |
| [Glossário](glossario.md) | Vocabulário do domínio |
| [Modelo de domínio](modelo-dominio.md) | Classes, responsabilidades, relações e multiplicidades |
| [Estados](uml/estados.md) | Ciclos de vida de orçamento, título, obrigação e conta a pagar |
| [Casos de uso](casos-de-uso/README.md) | 16 casos de uso, diagrama e cobertura dos requisitos |

## 3. Arquitetura e decisões

| Documento | Conteúdo |
|---|---|
| [Arquitetura](arquitetura.md) | Drivers, decisões técnicas, camadas e módulos |
| [ADRs](adr/README.md) | Decisões caras de reverter |
| [Segurança](seguranca.md) | Segurança do produto e do uso de agentes |
| [Testes](testes.md) | Estratégia de testes e definição de pronto |
| [Qualidade](qualidade/README.md) | Avaliação pela ISO/IEC 25010, testes e revisão de código |
| [Rastreabilidade](rastreabilidade.md) | Requisito → driver → decisão → código → teste |

## 4. Trabalho da equipe

| Documento | Conteúdo |
|---|---|
| [Combinados](combinados.md) | Regras de trabalho da equipe |
| [Execução](execucao.md) | Como instalar e rodar |
| [Mapa de specs](../.specify/specs/mapa-de-specs.md) | Unidades de implementação, em ordem |
| [Questões em aberto](../.specify/open.md) | Decisões que ainda dependem da equipe |

## Diagramas

Os diagramas ficam em [`uml/`](uml/), cada um com a fonte em Mermaid (`.mmd`) e a imagem exportada (`.png`). O texto é a fonte; o diagrama é uma vista. Nos diagramas, o que faz parte do escopo modelado mas ainda não foi implementado aparece em cinza, tracejado e com o estereótipo `«planejado»`. As imagens são geradas com o Mermaid 10.9.

| Diagrama | Fonte | Imagem |
|---|---|---|
| Classes do domínio | [`dominio-v2.mmd`](uml/dominio-v2.mmd) | [`dominio-v2.png`](uml/dominio-v2.png) |
| Casos de uso | [`casos-de-uso.mmd`](uml/casos-de-uso.mmd) | [`casos-de-uso.png`](uml/casos-de-uso.png) |
| Sequência do UC-04 | [`seq-UC-04.mmd`](uml/seq-UC-04.mmd) | [`seq-UC-04.png`](uml/seq-UC-04.png) |
| Sequência do UC-06 | [`seq-UC-06.mmd`](uml/seq-UC-06.mmd) | [`seq-UC-06.png`](uml/seq-UC-06.png) |
| Estados do título | [`estados-titulo.mmd`](uml/estados-titulo.mmd) | [`estados-titulo.png`](uml/estados-titulo.png) |
| Estados do orçamento | [`estados-orcamento.mmd`](uml/estados-orcamento.mmd) | [`estados-orcamento.png`](uml/estados-orcamento.png) |
| Estados da obrigação | [`estados-obrigacao.mmd`](uml/estados-obrigacao.mmd) | [`estados-obrigacao.png`](uml/estados-obrigacao.png) |
| Estados da conta a pagar | [`estados-conta-pagar.mmd`](uml/estados-conta-pagar.mmd) | [`estados-conta-pagar.png`](uml/estados-conta-pagar.png) |
| Atividades do UC-04 | [`atividades-UC-04.mmd`](uml/atividades-UC-04.mmd) | [`atividades-UC-04.png`](uml/atividades-UC-04.png) |
| Componentes | [`componentes.mmd`](uml/componentes.mmd) | [`componentes.png`](uml/componentes.png) |
| Implantação | [`implantacao.mmd`](uml/implantacao.mmd) | [`implantacao.png`](uml/implantacao.png) |

## Identificadores

`RF-nn` requisito funcional · `RNF-nn` requisito não funcional · `RB-nn` regra de negócio · `UC-nn` caso de uso · `DA-nn` driver arquitetural · `DT-nn` decisão técnica · `ADR-nnn` registro de decisão · `OPEN-nn` questão em aberto · `NNN` spec.
