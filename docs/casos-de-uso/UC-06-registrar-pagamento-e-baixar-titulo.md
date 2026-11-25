# UC-06 — Registrar pagamento e baixar título

| | |
|---|---|
| **Ator principal** | Operador Financeiro |
| **Atores de apoio** | Dono |
| **Objetivo** | Registrar o que o cliente pagou e manter saldo e estado do título corretos. |
| **Gatilho** | O Operador Financeiro recebe a confirmação de um pagamento. |
| **Regras de negócio** | RB-01, RB-02, RB-06, RB-21, RB-22, RB-23 |
| **Requisitos** | RF-20 a RF-27, RF-30, RF-31, RF-37, RF-51, RF-68, RNF-09 |

## Situação da implementação

**Implementado, exceto os passos 6 e 7.** Spec 006. O cancelamento dos envios da régua (passo 6, A4) depende das Specs 007 e 008, e o lançamento de receita (passo 7, A3) depende da Spec 011; as duas estão planejadas.

## Pré-condições

- O Operador Financeiro está autenticado.
- O título está Aberto, Vencido ou Em Renegociação.

## Fluxo principal

1. O Operador Financeiro localiza o título por cliente, vencimento ou estado.
2. O Operador Financeiro informa o valor e a data do pagamento.
3. O sistema valida o valor contra o saldo do título (RB-23).
4. O sistema registra o pagamento e reduz o saldo.
5. O saldo chega a zero. O sistema muda o estado do título para Baixado (RB-22).
6. O sistema cancela os envios pendentes da régua de cobrança para o título. *Planejado: Specs 007 e 008.*
7. O sistema gera o lançamento de receita, que segue para classificação (UC-10). *Planejado: Spec 011.*
8. O sistema registra a operação na auditoria.

## Fluxos alternativos

- **A1 — Pagamento parcial.** No passo 5, o saldo continua maior que zero. O sistema mantém o estado do título e apresenta o saldo restante. Os passos 7 e 8 ocorrem; o passo 6, não.
- **A2 — Cadastro manual de título.** Antes do passo 1, o usuário cadastra um título sem orçamento, com cliente, valor e vencimento. O sistema o cria em Aberto (RF-20).
- **A3 — Estorno.** O Dono seleciona um pagamento e solicita o estorno, informando o motivo. O sistema anula o pagamento, restaura o saldo, gera o lançamento de sinal contrário e devolve o título a Aberto ou Vencido, conforme o vencimento (RB-02).
- **A4 — Cancelamento de título.** Um usuário autorizado cancela um título Aberto ou Vencido informando o motivo. O sistema muda o estado para Cancelado e cancela os envios pendentes da régua.

## Exceções

- **E1 — Valor inválido.** No passo 3, o valor é menor ou igual a zero ou maior que o saldo. O sistema recusa o pagamento e nada é gravado (RF-68).
- **E2 — Título Baixado ou Cancelado.** No passo 2, o sistema recusa o pagamento e informa o estado do título (RB-21).
- **E3 — Estorno por perfil não autorizado.** Em A3, se o usuário não for o Dono, o sistema nega a operação (RB-02).
- **E4 — Motivo ausente.** Em A3 ou A4, sem motivo informado, o sistema recusa a operação (RF-31).
- **E5 — Falha durante a operação.** O sistema desfaz todas as alterações: pagamento, saldo, estado e lançamento (RNF-09).

## Pós-condições

- Sucesso: pagamento registrado; saldo atualizado; título Baixado quando o saldo é zero; lançamento gerado; operação auditada.
- Falha: título, saldo e lançamentos inalterados.

## Diagramas

- Sequência do fluxo principal: [`seq-UC-06.png`](../uml/seq-UC-06.png), fonte em [`seq-UC-06.mmd`](../uml/seq-UC-06.mmd).
- Estados do título: [estados](../uml/estados.md#título).

```mermaid
sequenceDiagram
    autonumber
    actor Operador as Operador Financeiro
    participant UI as Interface web
    participant App as ServicoTitulos
    participant Exec as Execucao (transação e autorização)
    participant Tit as Titulo
    participant Aud as OperacaoAuditada
    participant Repo as Repositório (SQLite)
    participant Lanc as LancamentoFinanceiro «planejado»
    participant Regua as Régua de cobrança «planejado»

    Operador->>UI: registra pagamento do título (RF-25)
    UI->>App: registrarPagamento(sessão, título, valor, data)
    App->>Exec: abre a operação "registrar pagamento"
    Exec->>Exec: confere a sessão e a permissão do perfil (RNF-01, RNF-03)
    alt sem sessão ou sem permissão
        Exec-->>UI: nega (RF-67), nada é gravado
    else autorizado
        App->>Repo: obtém o título
        App->>Tit: registrarPagamento(valor, data)
        alt valor menor ou igual a zero, ou maior que o saldo
            Tit-->>App: recusa (RB-23, RF-68)
            Exec->>Exec: desfaz a transação
            App-->>UI: informa o motivo, nada é gravado
        else título Baixado ou Cancelado
            Tit-->>App: recusa (RB-21)
            Exec->>Exec: desfaz a transação
            App-->>UI: informa o estado do título
        else pagamento válido
            Tit->>Tit: reduz o saldo e, com saldo zero, passa a Baixado (RF-26, RB-22)
            Tit-->>App: pagamento registrado, com saldo e estado
            App->>Aud: registra o pagamento e a mudança de estado (RB-01)
            App->>Repo: salva o título
            rect rgb(240, 240, 240)
                Note over App,Regua: Planejado (Specs 007, 008 e 011): ainda não implementado
                App->>Lanc: gera lançamento de receita Pendente de Classificação (RF-51)
                opt título Baixado
                    App->>Regua: cancela envios pendentes (RF-37)
                end
            end
            Exec->>Exec: confirma a transação: tudo ou nada (RNF-09)
            App-->>UI: confirmação, com o saldo restante (RF-27)
        end
    end
```
