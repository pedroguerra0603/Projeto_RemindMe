# ADR-003 — A IA extrai e classifica; o sistema decide

- **Situação:** Proposto, aguardando aprovação da equipe
- **Data:** 2026-10-03
- **Decisores:** a definir pela equipe
- **Drivers:** DA-06, DA-07
- **Requisitos e regras:** RB-08, RB-09, RB-14, RB-17, RB-27, RF-72 a RF-81, RNF-22, RNF-24, RNF-26

## Contexto

O sistema usa um modelo de linguagem em dois pontos: sugerir a categoria de um lançamento e extrair a intenção de uma mensagem de cliente. Modelos de linguagem erram, ficam indisponíveis e podem ser induzidos por texto malicioso na entrada. O sistema lida com valores financeiros.

## Decisão

1. O serviço de IA é acessado por uma interface, com implementação simulada como padrão nos testes.
2. A IA só devolve dados estruturados: uma categoria com confiança, ou intenção, título, valor e data.
3. Todo dado devolvido é validado por regra determinística antes de produzir efeito. A categoria precisa existir no plano de contas, e a confiança precisa atingir o limiar. O título precisa existir, ser do cliente e estar Vencido.
4. Falha, tempo excedido ou dado inválido levam ao tratamento humano. Nenhuma operação depende da IA para ser concluída.
5. Nenhum valor financeiro vem da IA, e nenhum texto gerado pela IA é enviado ao cliente. As respostas usam templates.
6. A entrada enviada à IA não contém dados de identificação do cliente.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| IA responde ao cliente em texto livre | Risco de promessa indevida em nome da empresa e de vazamento de dados. |
| IA aprova a renegociação | Decisão financeira sem regra auditável. |
| Não usar IA | Perde-se a redução de trabalho manual na classificação, que é parte da proposta do produto. |

## Consequências

- Positivas: o comportamento financeiro é determinístico e testável; a qualidade da IA é medida pelas divergências registradas.
- Negativas: parte dos lançamentos sempre exigirá revisão humana.
- O que passa a ser obrigatório: toda sugestão é registrada, aceita ou não; a escolha do provedor (OPEN-04) e do limiar (OPEN-05) não altera o domínio.
