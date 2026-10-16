# Visão do Produto — RemindMe

## 1. Visão

O RemindMe é um sistema web de gestão do ciclo de recebíveis e das obrigações de micro e pequenas empresas. Ele garante que cada cobrança e cada obrigação avance no prazo, com registro de quem fez o quê e quando.

O projeto se enquadra na categoria **sistema de gestão com múltiplos papéis**, com elementos de automação de processos.

> O nome inicial do projeto era "Fluxo". O nome adotado é RemindMe.

## 2. Problema

Empresas de pequeno porte raramente têm um back-office. O dono acumula vendas, cobrança e administração, e a contabilidade terceirizada entrega só o mínimo obrigatório, sem acompanhar a operação do dia a dia. Os sintomas se repetem:

- orçamento aprovado que nunca vira cobrança;
- título vencido que ninguém cobra;
- prazo fiscal ou contratual perdido por falta de calendário;
- resultado financeiro desconhecido, porque os lançamentos são classificados de forma inconsistente;
- ninguém sabe dizer quem fez o quê e quando.

A causa não é falta de sistema contábil. É falta de rotina com regra: sequência clara, alerta automático, escalonamento e registro.

## 3. Público-alvo

Micro e pequenas empresas de serviços ou comércio que vendem a prazo para clientes recorrentes e hoje controlam recebíveis em planilha ou de memória.

O sistema tem quatro perfis, descritos em [personas](personas.md):

| Perfil | O que busca | O que faz no sistema |
|---|---|---|
| Dono | Receber rápido e manter controle | Decide exceções, aprova descontos fora de alçada, recebe alertas escalonados |
| Operador Financeiro | Executar a rotina sem ambiguidade | Elabora orçamentos, registra pagamentos, trata cobranças e obrigações dentro da sua alçada |
| Cliente | Prazo e transparência | Decide orçamentos, consulta seus títulos, propõe renegociação |
| Contador | Classificação correta | Consulta e exporta dados consolidados, somente leitura |

Esses interesses entram em conflito: a empresa quer receber rápido, o cliente quer prazo, o contador quer classificação correta. O RemindMe resolve essas tensões por regra, e não por conversa.

## 4. Solução

### Núcleo: ciclo de recebíveis

O sistema acompanha o dinheiro a receber do começo ao fim, com mudanças de estado explícitas:

1. o orçamento é criado e enviado ao cliente;
2. o desconto é validado contra a alçada de quem elaborou;
3. o orçamento aprovado vira título a receber;
4. o título é cobrado por uma régua automática de lembretes;
5. o título pode ser renegociado, com histórico preservado;
6. o título é baixado quando pago.

### Frentes de apoio

- **Calendário de obrigações.** Reúne compromissos fiscais e contratuais recorrentes, avisa com antecedência, exige evidência de cumprimento e escala o alerta ao Dono quando o prazo estoura.
- **Apuração do resultado.** Montada a partir dos lançamentos que o próprio ciclo de cobrança gera. A demonstração de resultado passa a refletir a operação, em vez de chegar meses depois.

## 5. Papel da inteligência artificial

O sistema usa um modelo de linguagem em dois pontos, sob um único princípio: **a IA extrai e classifica; o sistema decide** (RB-27).

1. **Classificação de lançamentos.** A IA sugere a categoria do plano de contas com um grau de confiança. O sistema só aceita automaticamente sugestões válidas e com confiança acima do limiar. As demais vão para revisão humana e ficam fora da apuração até a confirmação.
2. **Intenção em mensagens de clientes.** A IA extrai intenção, título, valor e data prometida. O sistema processa esses dados por regra e responde por template.

Nenhum valor financeiro é produzido pela IA, e nenhum texto gerado pela IA chega ao cliente. Cada correção humana fica registrada, o que dá uma medida da qualidade das sugestões ao longo do tempo.

## 6. Escopo

### Dentro do MVP

- Ciclo completo de recebíveis, do orçamento à baixa.
- Alçadas de desconto com aprovação do Dono.
- Régua automática de cobrança com canal de notificação simulado.
- Renegociação com extração de intenção por IA.
- Calendário de obrigações com evidência e escalonamento.
- Classificação de lançamentos assistida por IA e apuração do resultado.
- Auditoria das operações.
- Importação e exportação em CSV.

### Fora do MVP

| Item | Motivo |
|---|---|
| Emissão de nota fiscal e integração com a SEFAZ | Exige certificado digital e homologação. O sistema registra a obrigação de emitir e guarda a evidência. |
| Folha de pagamento e RH | É um domínio inteiro e independente. |
| Recomendação de investimento ou de corte de gastos | Seria opinião, e não regra. |
| Canal real de WhatsApp | O canal de notificação é uma peça substituível. O MVP usa o canal simulado, o que permite rodar toda a suíte de testes sem credencial externa. |
| Contas a pagar | O núcleo do MVP é o recebível. A forma de registrar despesas para a apuração está em aberto (OPEN-07). |

## 7. Critérios de sucesso

| Critério | Como medir no MVP |
|---|---|
| Nenhum título vence sem cobrança | Todo título Vencido tem ao menos uma tentativa registrada na régua |
| Nenhuma obrigação estoura em silêncio | Toda obrigação Atrasada gera alerta escalonado ao Dono |
| Resultado disponível sem fechamento manual | A apuração reflete um pagamento logo após o seu registro |
| Operação rastreável | Toda mudança de estado tem registro de auditoria |
| IA sob controle | Taxa de divergência entre sugestão e classificação final disponível para consulta |

## 8. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| IA classifica errado com frequência | Médio | Limiar de confiança, fila de revisão humana e registro de divergências |
| Escopo maior que o semestre | Alto | Mapa de specs ordenado; entrega por fatias, do núcleo de recebíveis para fora |
| Regras de renegociação mal definidas | Médio | Limites registrados como decisão em aberto antes da implementação |
| Dependência de serviço externo nos testes | Médio | Canal de notificação e serviço de IA simulados por padrão |

## 9. Documentos relacionados

- [Benchmark](benchmark.md)
- [Personas](personas.md)
- [Requisitos](requisitos.md)
- [Modelo de domínio](modelo-dominio.md)
- [Casos de uso](casos-de-uso/README.md)
- [Arquitetura](arquitetura.md)
