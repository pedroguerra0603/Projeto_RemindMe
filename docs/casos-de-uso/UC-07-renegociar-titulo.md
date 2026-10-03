# UC-07 — Renegociar título

| | |
|---|---|
| **Ator principal** | Cliente |
| **Atores de apoio** | Serviço de IA, Operador Financeiro, Dono |
| **Objetivo** | Obter novo prazo para um título vencido, com o combinado registrado. |
| **Gatilho** | O Cliente envia uma mensagem sobre um título seu. |
| **Regras de negócio** | RB-11, RB-17, RB-20, RB-26, RB-27, RB-28 |
| **Requisitos** | RF-28, RF-29, RF-69, RF-72 a RF-76, RNF-22, RNF-24 |

## Pré-condições

- O título pertence ao cliente e está Vencido.

## Fluxo principal

1. O Cliente envia uma mensagem prometendo pagar um título em uma data.
2. O sistema solicita ao serviço de IA a extração de intenção, título, valor e data prometida.
3. O sistema valida os dados extraídos: o título existe, é do cliente, está Vencido e a data é futura.
4. O sistema muda o estado do título para Em Renegociação e suspende a régua de cobrança (RB-20, RB-11).
5. O sistema verifica a proposta contra os limites de renegociação configurados.
6. A proposta está dentro dos limites. O sistema aplica o novo vencimento, devolve o título a Aberto e registra as condições anteriores e as novas (RB-28).
7. O sistema responde ao Cliente por template com o novo vencimento.

## Fluxos alternativos

- **A1 — Proposta fora dos limites.** No passo 6, o sistema encaminha a proposta ao Operador Financeiro ou ao Dono. Se aprovada, o fluxo segue no passo 6. Se recusada, o título volta a Vencido e o Cliente é avisado por template (RF-76).
- **A2 — Consulta de títulos.** O Cliente autenticado consulta seus títulos, com valor, vencimento, saldo e estado, sem propor renegociação (RF-69).
- **A3 — Renegociação registrada pelo Operador.** O Operador Financeiro registra a proposta recebida por outro meio. O fluxo segue no passo 3.

## Exceções

- **E1 — IA sem dados estruturados válidos.** No passo 2, o serviço de IA falha, excede o tempo limite ou devolve dados incompletos. O sistema encaminha a mensagem para tratamento manual e não altera o título (RB-17).
- **E2 — Mensagem sem promessa válida.** No passo 3, os dados não formam uma promessa válida. O estado do título não muda.
- **E3 — Título de outro cliente.** No passo 3, o título não pertence ao cliente. O sistema não revela dados do título e encaminha a mensagem para tratamento manual (RB-26).

## Pós-condições

- Sucesso: título Aberto com novo vencimento; renegociação registrada com condições anteriores e novas.
- Pendente: título Em Renegociação, aguardando decisão humana, com a régua suspensa.
- Falha: título inalterado; mensagem na fila de tratamento manual.
