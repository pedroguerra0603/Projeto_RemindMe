# ADR-007 — SQLite como banco relacional do MVP

- **Situação:** Aceito
- **Data:** 2026-10-23
- **Decisores:** João Pedro Silva Guerra, por delegação ao agente; a confirmar na revisão do PR
- **Drivers:** DA-02, DA-03, DA-07, DA-08
- **Requisitos e regras:** RNF-06, RNF-08, RNF-09, RB-30; OPEN-36; complementa o ADR-005

## Contexto

O ADR-005 escolheu um banco relacional com transações e restrição de unicidade, sem escolher o produto (OPEN-36). A apresentação roda na máquina de quem apresenta (OPEN-12), e o projeto não instala dependência (OPEN-01, RNF-23).

## Decisão

O banco do MVP é o SQLite, pelo módulo `sqlite3` da biblioteca padrão, em um arquivo local. Cada transação usa `BEGIN IMMEDIATE`, e a tabela de auditoria recusa `UPDATE` e `DELETE` no próprio banco.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| PostgreSQL | Exige servidor instalado e configurado, e um driver de terceiros (`psycopg`). Fica como evolução para a hospedagem real. |
| MySQL ou MariaDB | Mesmos motivos do PostgreSQL. |

## Consequências

- Positivas: transação real (RNF-09) e unicidade (DA-08) sem servidor e sem dependência; os testes de contrato rodam sobre o banco real, em arquivo temporário; o backup é a cópia do arquivo pela API de backup do SQLite.
- Negativas: um único escritor por vez, o que basta para uma empresa pequena, mas limita a escala; não há usuários nem permissões de banco, por isso a imutabilidade da auditoria no armazenamento é feita por gatilho que só recusa a operação.
- O que passa a ser obrigatório: valores monetários guardados como texto decimal, sem `float`; toda leitura e escrita dentro da unidade de trabalho; o esquema criado por migração numerada (`PRAGMA user_version`).
