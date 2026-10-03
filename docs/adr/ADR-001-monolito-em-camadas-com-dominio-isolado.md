# ADR-001 — Monólito em camadas com domínio isolado

- **Situação:** Proposto, aguardando aprovação da equipe
- **Data:** 2026-10-03
- **Decisores:** a definir pela equipe
- **Drivers:** DA-01, DA-09
- **Requisitos e regras:** RB-05, RB-21, RB-22, RB-23, RNF-19

## Contexto

O valor do RemindMe está nas regras de estado e de alçada. Essas regras são acionadas por quatro entradas diferentes: a interface web, o agendador, a importação CSV e a recepção de mensagens de clientes. Se a regra morar na tela ou no controlador, cada entrada precisa repeti-la, e alguma vai esquecer.

A equipe tem três pessoas e um semestre.

## Decisão

Construir uma única aplicação, organizada em camadas, em que o domínio não depende de framework, banco de dados nem serviço externo. Toda regra de negócio fica no domínio e é alcançada por qualquer entrada pelo mesmo caminho.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Microsserviços | Custo de operação e de integração incompatível com a equipe e o prazo. Não há requisito de escala que justifique. |
| Regras nos controladores (MVC simples) | Agendador e importação teriam de duplicar as regras. Viola DA-01. |
| Regras em gatilhos de banco de dados | Regras ficam difíceis de testar e de rastrear até o identificador. Viola DA-09. |

## Consequências

- Positivas: cada regra de negócio é testada sem banco e sem interface; trocar framework ou banco não altera regra.
- Negativas: mais código de ligação entre camadas do que em um MVC direto.
- O que passa a ser obrigatório: o domínio não importa nada das outras camadas; todo teste de regra leva o identificador da regra no nome.
