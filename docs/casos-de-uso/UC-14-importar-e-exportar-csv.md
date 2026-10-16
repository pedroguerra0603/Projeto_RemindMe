# UC-14 — Importar e exportar CSV

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Contador, Administrador |
| **Objetivo** | Trocar dados com planilhas sem redigitação. |
| **Gatilho** | O usuário solicita uma importação ou uma exportação. |
| **Regras de negócio** | RB-03, RB-19 |
| **Requisitos** | RF-83, RF-84, RF-85, RNF-09 |

## Pré-condições

- O usuário está autenticado.
- Para importar: perfil Operador Financeiro ou Administrador.

## Fluxo principal

1. O usuário escolhe o tipo de dado (clientes ou títulos) e envia o arquivo CSV.
2. O sistema valida o formato, as colunas obrigatórias e os valores de cada linha.
3. O sistema apresenta o total de linhas válidas.
4. O usuário confirma a importação.
5. O sistema importa todas as linhas e registra a operação na auditoria.

## Fluxos alternativos

- **A1 — Exportação.** O usuário escolhe títulos, lançamentos ou demonstração de resultado, aplica filtros e recebe o arquivo CSV (RF-85). O Contador pode exportar.

## Exceções

- **E1 — Arquivo com linha inválida.** No passo 2, o sistema apresenta os erros por linha e recusa a importação inteira (RB-19).
- **E2 — Arquivo que não é CSV.** No passo 2, o sistema recusa o arquivo.
- **E3 — Contador tenta importar.** O sistema nega a operação (RB-03).
- **E4 — Falha durante a importação.** O sistema desfaz todas as linhas já gravadas (RNF-09).

## Pós-condições

- Sucesso: todas as linhas importadas, ou arquivo gerado.
- Falha: nenhuma linha importada.
