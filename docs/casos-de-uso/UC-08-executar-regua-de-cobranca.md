# UC-08 — Executar régua de cobrança

| | |
|---|---|
| **Ator principal** | Agendador |
| **Atores de apoio** | Canal de notificação, Operador Financeiro, Cliente |
| **Objetivo** | Cobrar cada título no momento definido pela régua, sem ação manual. |
| **Gatilho** | O agendador inicia o ciclo periódico de verificação dos títulos. |
| **Regras de negócio** | RB-10, RB-11, RB-18, RB-21 |
| **Requisitos** | RF-23, RF-24, RF-32 a RF-39, RF-70, RF-71, RNF-12, RNF-13 |

## Pré-condições

- Existe uma régua de cobrança com ao menos uma etapa (UC-13).

## Fluxo principal

1. O sistema marca como Vencido todo título Aberto com vencimento passado e saldo maior que zero.
2. O sistema seleciona os títulos Abertos ou Vencidos que atingiram o prazo de uma etapa ainda não executada.
3. Para cada título, o sistema monta a mensagem da etapa com os dados do título.
4. O sistema envia a mensagem ao cliente pelo canal de notificação.
5. O sistema registra a tentativa com data, etapa e resultado.

## Fluxos alternativos

- **A1 — Etapa de intervenção manual.** No passo 4, a ação da etapa é intervenção manual. O sistema cria uma tarefa para o Operador Financeiro em vez de enviar mensagem (RF-38).
- **A2 — Canal WhatsApp habilitado.** No passo 4, o sistema usa o canal WhatsApp em vez do simulado (RB-18).
- **A3 — Consulta do histórico.** Um usuário consulta as tentativas de cobrança de um título, em ordem cronológica (RF-39).

## Exceções

- **E1 — Título Em Renegociação.** No passo 2, o título é ignorado enquanto durar a renegociação (RB-11).
- **E2 — Título Baixado ou Cancelado.** No passo 2, o título é ignorado e seus envios pendentes são cancelados (RF-37).
- **E3 — Falha no canal.** No passo 4, o envio falha. O sistema registra a tentativa com resultado de falha e cria uma tarefa para o Operador Financeiro (RF-38).

## Pós-condições

- Sucesso: cada etapa devida tem uma tentativa registrada.
- Nenhuma etapa é executada duas vezes para o mesmo título.
