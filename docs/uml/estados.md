# Estados — RemindMe

Ciclos de vida das quatro entidades com estado explícito. Uma transição que não está na tabela é inválida e deve ser recusada.

## Título

Regra: RB-21. Imagem: [`estados-titulo.png`](estados-titulo.png).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Aberto : criado
    Aberto --> Vencido : vencimento passa
    Aberto --> Baixado : saldo zero
    Vencido --> Baixado : saldo zero
    Vencido --> EmRenegociacao : promessa válida
    EmRenegociacao --> Aberto : aprovada
    EmRenegociacao --> Vencido : recusada
    EmRenegociacao --> Baixado : saldo zero
    Baixado --> Aberto : estorno, a vencer
    Baixado --> Vencido : estorno, já vencido
    Aberto --> Cancelado : cancelamento
    Vencido --> Cancelado : cancelamento
    Cancelado --> [*]
    EmRenegociacao : Em Renegociação
```

| De | Para | Gatilho | Requisito |
|---|---|---|---|
| — | Aberto | Título gerado de orçamento ou cadastrado manualmente | RF-11, RF-20 |
| Aberto | Vencido | Vencimento passa com saldo maior que zero | RF-24 |
| Aberto, Vencido, Em Renegociação | Baixado | Saldo chega a zero | RF-26 |
| Vencido | Em Renegociação | Promessa de pagamento válida do cliente | RF-73 |
| Em Renegociação | Aberto | Renegociação aprovada, com novo vencimento | RF-28 |
| Em Renegociação | Vencido | Proposta recusada | RF-76 |
| Baixado | Aberto | Estorno pelo Dono, com vencimento futuro | RF-30 |
| Baixado | Vencido | Estorno pelo Dono, com vencimento passado | RF-30 |
| Aberto, Vencido | Cancelado | Cancelamento com motivo | RF-31 |

Cláusulas de estado derivadas:

- WHILE o título estiver Vencido, o sistema cobra pela régua (RF-34).
- WHILE o título estiver Em Renegociação, o sistema suspende a régua (RF-70).
- IF for solicitado pagamento em título Baixado ou Cancelado, THEN o sistema recusa (RB-21).

## Orçamento

Imagem: [`estados-orcamento.png`](estados-orcamento.png).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Rascunho : criado
    Rascunho --> PendenteAlcada : desconto acima da alçada
    PendenteAlcada --> Rascunho : decisão do Dono
    Rascunho --> Enviado : envio
    Enviado --> Aprovado : cliente aprova
    Enviado --> Rejeitado : cliente rejeita
    Aprovado --> Convertido : título gerado
    Rascunho --> Cancelado : cancelamento
    PendenteAlcada --> Cancelado : cancelamento
    Enviado --> Cancelado : cancelamento
    Rejeitado --> [*]
    Convertido --> [*]
    Cancelado --> [*]
    PendenteAlcada : Pendente de Alçada
```

| De | Para | Gatilho | Requisito |
|---|---|---|---|
| — | Rascunho | Orçamento criado | RF-06 |
| Rascunho | Pendente de Alçada | Desconto acima da alçada de quem elaborou | RF-16 |
| Pendente de Alçada | Rascunho | Dono aprova ou rejeita o desconto | RF-17 |
| Rascunho | Enviado | Envio com ao menos um item e desconto permitido | RF-08 |
| Enviado | Aprovado | Cliente aprova | RF-09 |
| Enviado | Rejeitado | Cliente rejeita | RF-09 |
| Aprovado | Convertido | Título gerado | RF-11 |
| Rascunho, Pendente de Alçada, Enviado | Cancelado | Cancelamento com motivo | RF-13 |

Aprovado é um estado de passagem: a conversão ocorre na mesma operação da aprovação (RB-05). Se o desconto for rejeitado pelo Dono, o orçamento volta a Rascunho com o desconto anterior.

## Obrigação

Imagem: [`estados-obrigacao.png`](estados-obrigacao.png).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Pendente : cadastrada ou gerada
    Pendente --> Cumprida : cumprimento sem exigência de evidência
    Pendente --> AguardandoEvidencia : cumprimento sem a evidência exigida
    AguardandoEvidencia --> Cumprida : evidência anexada
    Pendente --> Atrasada : prazo passa
    AguardandoEvidencia --> Atrasada : prazo passa
    Atrasada --> Cumprida : cumprimento completo
    Cumprida --> [*]
    AguardandoEvidencia : Aguardando Evidência
```

| De | Para | Gatilho | Requisito |
|---|---|---|---|
| — | Pendente | Obrigação cadastrada ou ocorrência gerada | RF-40, RF-42 |
| Pendente | Cumprida | Cumprimento registrado; evidência não exigida ou já anexada | RF-45, RF-46 |
| Pendente | Aguardando Evidência | Cumprimento registrado sem a evidência exigida | RF-46 |
| Aguardando Evidência | Cumprida | Evidência anexada | RF-46 |
| Pendente, Aguardando Evidência | Atrasada | Prazo passa | RF-48 |
| Atrasada | Cumprida | Cumprimento registrado, com evidência quando exigida | RF-45, RF-46 |

Cláusulas de estado derivadas:

- WHILE a obrigação estiver Aguardando Evidência, o alerta permanece no painel do Operador Financeiro (RF-77).
- IF a obrigação permanecer Atrasada pela tolerância configurada, THEN o sistema escala ao Dono (RF-49).

## Conta a pagar

Regras: RB-31, RB-32 e RB-33 (Spec 018). Imagem: [`estados-conta-pagar.png`](estados-conta-pagar.png).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Aberta : cadastrada
    Aberta --> Vencida : vencimento passa
    Aberta --> Paga : saldo zero
    Vencida --> Paga : saldo zero
    Paga --> Aberta : estorno, a vencer
    Paga --> Vencida : estorno, já vencida
    Aberta --> Cancelada : cancelamento
    Vencida --> Cancelada : cancelamento
    Cancelada --> [*]
```

| De | Para | Gatilho | Requisito |
|---|---|---|---|
| — | Aberta | Conta cadastrada para um fornecedor, com saldo igual ao valor | RF-88 |
| Aberta | Vencida | Vencimento passa, pelo agendador | RF-90 |
| Aberta, Vencida | Paga | Pagamento leva o saldo a zero | RF-91 |
| Paga | Aberta | Estorno pelo Dono, com motivo e vencimento futuro | RF-92 |
| Paga | Vencida | Estorno pelo Dono, com motivo e vencimento passado | RF-92 |
| Aberta, Vencida | Cancelada | Cancelamento pelo Dono, com motivo | RF-93 |

Cláusulas de estado derivadas:

- Pagamento parcial e estorno de pagamento em conta Aberta ou Vencida não mudam o estado; só o saldo (RF-91, RF-92).
- IF for solicitado pagamento em conta Paga ou Cancelada, THEN o sistema recusa (RB-31).
- IF for solicitado o cancelamento de conta Paga, THEN o sistema recusa; os pagamentos são estornados antes (RB-31).
- Pela OPEN-53, o Administrador também estorna e cancela (RB-33).
