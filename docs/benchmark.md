# Benchmark — RemindMe

Comparação do RemindMe com as categorias de solução que uma pequena empresa usa hoje para controlar recebíveis e obrigações. O objetivo é localizar a lacuna que o projeto ocupa, e não avaliar produtos comerciais em detalhe.

## Categorias analisadas

| Categoria | Exemplos | O que resolve bem | O que deixa em aberto |
|---|---|---|---|
| Planilha | Excel, Google Planilhas | Custo zero, flexibilidade total | Não cobra, não avisa, não registra quem alterou |
| ERP para pequenas empresas | Conta Azul, Omie | Emissão fiscal, financeiro, estoque, integração com o contador | Amplo e genérico; alçadas e escalonamento por regra não são o foco |
| Plataforma de cobrança | Asaas | Emissão de boleto e Pix, lembretes automáticos de cobrança | Não cobre o orçamento que antecede o título nem o calendário de obrigações |
| Gestor financeiro | Granatum | Fluxo de caixa, categorização, relatórios | Não conduz o ciclo comercial nem a cobrança por régua |
| Controle informal | Agenda, WhatsApp, memória do dono | Nenhum esforço de adoção | Não há registro nem garantia de execução |

Os exemplos foram escolhidos por serem conhecidos no mercado brasileiro. A descrição é de posicionamento geral; recursos e planos mudam e devem ser conferidos nos sites oficiais antes de qualquer citação na apresentação.

## Critérios de comparação

| Critério | Planilha | ERP | Plataforma de cobrança | Gestor financeiro | RemindMe |
|---|---|---|---|---|---|
| Orçamento ligado ao título | Manual | Sim | Não | Não | Sim |
| Alçada de desconto com aprovação | Não | Parcial | Não | Não | Sim |
| Régua automática de cobrança | Não | Parcial | Sim | Não | Sim |
| Renegociação com histórico | Não | Parcial | Parcial | Não | Sim |
| Calendário de obrigações com evidência e escalonamento | Não | Não | Não | Não | Sim |
| Resultado derivado da operação | Manual | Sim | Não | Sim | Sim |
| Auditoria de cada mudança de estado | Não | Parcial | Parcial | Parcial | Sim |
| Emissão fiscal | Não | Sim | Parcial | Não | Não |
| Meio de pagamento integrado | Não | Parcial | Sim | Não | Não |

"Parcial" indica que o recurso existe em alguma medida, mas não é o centro da proposta da categoria.

## Lacuna identificada

As soluções existentes cobrem bem as pontas: o ERP cobre fiscal e contábil, e a plataforma de cobrança cobre o meio de pagamento. O que fica descoberto é a **rotina com regra** entre o orçamento e a baixa, somada às obrigações recorrentes da empresa:

- quem pode dar qual desconto, e quem aprova a exceção;
- o que acontece com um título quando o cliente promete pagar;
- quem é avisado, e depois de quanto tempo, quando uma obrigação estoura;
- como o resultado se mantém coerente com a operação sem fechamento manual.

## Decisões derivadas do benchmark

1. **Não competir em emissão fiscal nem em meio de pagamento.** Esses itens ficam fora do escopo; ver [visão](visao.md).
2. **Tratar estados e transições como o centro do produto.** Orçamento, título e obrigação têm ciclo de vida explícito; ver [modelo de domínio](modelo-dominio.md).
3. **Manter o canal de notificação substituível.** O valor está na regra de quando cobrar, e não no canal; ver [ADR-002](adr/ADR-002-canal-de-notificacao-substituivel.md).
