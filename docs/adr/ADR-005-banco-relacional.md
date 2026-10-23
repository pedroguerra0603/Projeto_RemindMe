# ADR-005 — Banco de dados relacional

- **Situação:** Aceito
- **Data:** 2026-10-23
- **Decisores:** João Pedro Silva Guerra
- **Drivers:** DA-03, DA-08
- **Requisitos e regras:** RNF-06, RNF-09, RB-19, RB-30; OPEN-02

## Contexto

Pagamento, estorno, conversão de orçamento e importação CSV precisam ser atômicos (DA-03, RNF-09). A régua não pode repetir uma etapa, o que pede uma restrição de unicidade (DA-08). A auditoria só aceita inclusão (ADR-004, RB-30). Hoje a persistência é em memória, e a garantia de atomicidade vem de uma cópia do estado, que não vale entre processos.

## Decisão

A persistência usa um banco de dados relacional, com transações e restrição de unicidade. O produto específico ainda será escolhido (OPEN-36).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| Banco de documentos | Transação entre vários registros e restrição de unicidade dependem do produto e da configuração; o modelo de domínio é fortemente relacional (título, pagamento, cliente, orçamento). |
| Arquivos (JSON ou CSV) | Sem transação nem concorrência segura; não atende a RNF-09. |
| Manter só a persistência em memória | Os dados não sobrevivem ao fim do processo; não atende a RNF-08. |

## Consequências

- Positivas: a atomicidade e a unicidade passam a ser garantidas pelo banco, e não pela aplicação; a auditoria pode ter permissão só de inclusão no próprio banco.
- Negativas: exige migração de esquema e um adaptador de persistência para cada repositório.
- O que passa a ser obrigatório: os testes de contrato hoje rodados sobre a implementação em memória são repetidos sobre o banco (Spec 001); o domínio continua sem depender do banco (ADR-001).
