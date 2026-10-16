# Glossário — RemindMe

Vocabulário do domínio. Os termos abaixo são os únicos usados em requisitos, casos de uso, specs e código. Quando houver nome de classe correspondente no [modelo de domínio](modelo-dominio.md), ele aparece na segunda coluna.

| Termo | Classe | Definição |
|---|---|---|
| Alçada de desconto | `AlcadaDesconto` | Percentual máximo de desconto que um perfil pode conceder sem aprovação do Dono. |
| Apuração do resultado | — | Cálculo de receitas menos despesas dos lançamentos classificados de um período. |
| Baixa | — | Passagem de um título ao estado Baixado, quando o saldo chega a zero. |
| Canal de notificação | — | Meio pelo qual o sistema envia orçamentos, cobranças e alertas. O padrão é o canal simulado. |
| Categoria financeira | `CategoriaFinanceira` | Conta do plano de contas da empresa, de receita ou de despesa. |
| Cliente | `Cliente` | Pessoa ou empresa que recebe orçamentos e deve títulos. |
| Demonstração de resultado (DRE) | — | Apresentação de receitas, despesas e resultado por categoria. |
| Divergência | `SugestaoClassificacao` | Diferença entre a categoria sugerida pela IA e a categoria confirmada por uma pessoa. |
| Escalonamento | — | Envio de alerta ao Dono quando uma obrigação permanece Atrasada. |
| Estorno | — | Anulação de um pagamento registrado. Só o Dono estorna. |
| Etapa de cobrança | `EtapaCobranca` | Passo da régua: prazo em dias em relação ao vencimento, mensagem e ação. |
| Evidência | `Evidencia` | Documento anexado que comprova o cumprimento de uma obrigação. |
| Fila de revisão | — | Conjunto de lançamentos Pendentes de Classificação que aguardam decisão humana. |
| Lançamento financeiro | `LancamentoFinanceiro` | Registro de receita ou despesa usado na apuração do resultado. |
| Limiar de confiança | — | Valor mínimo de confiança para aceitar automaticamente uma sugestão da IA. |
| Obrigação | `Obrigacao` | Compromisso fiscal ou contratual com prazo, responsável e periodicidade. |
| Orçamento | `Orcamento` | Proposta comercial feita a um cliente, composta de itens. |
| Pagamento | `Pagamento` | Valor recebido de um cliente e associado a um título. |
| Perfil | `Perfil` | Papel de acesso: Dono, Operador Financeiro, Contador, Cliente ou Administrador. |
| Plano de contas | — | Conjunto das categorias financeiras da empresa. |
| Promessa de pagamento | `Renegociacao` | Compromisso do cliente de pagar um título em uma data. |
| Régua de cobrança | `ReguaCobranca` | Sequência ordenada de etapas de cobrança aplicada aos títulos. |
| Registro de auditoria | `RegistroAuditoria` | Registro imutável de uma operação: quem, quando, o quê e sobre qual registro. |
| Renegociação | `Renegociacao` | Alteração das condições de um título, com as condições originais preservadas. |
| Saldo | — | Valor do título menos a soma dos pagamentos não estornados. |
| Sugestão de classificação | `SugestaoClassificacao` | Categoria proposta pela IA para um lançamento, com grau de confiança. |
| Tentativa de cobrança | `TentativaCobranca` | Registro do envio de uma etapa da régua para um título, com data e resultado. |
| Título | `Titulo` | Valor a receber de um cliente, com vencimento. |
| Usuário | `Usuario` | Pessoa que acessa o sistema com um perfil. |

## Estados

| Entidade | Estados |
|---|---|
| Orçamento | Rascunho, Pendente de Alçada, Enviado, Aprovado, Rejeitado, Convertido, Cancelado |
| Título | Aberto, Vencido, Em Renegociação, Baixado, Cancelado |
| Obrigação | Pendente, Aguardando Evidência, Atrasada, Cumprida |
| Lançamento | Pendente de Classificação, Classificado |

"Próximo do vencimento" não é estado do título. É uma sinalização calculada sobre títulos Abertos (RF-23).

## Termos que não usamos

| Evitar | Usar |
|---|---|
| Fatura, boleto, duplicata | Título |
| Proposta, pedido | Orçamento |
| Conta contábil, conta | Categoria financeira |
| Lembrete, notificação de cobrança | Tentativa de cobrança (o registro) ou etapa de cobrança (a configuração) |
| Fluxo (nome antigo do projeto) | RemindMe |
| RN (prefixo antigo) | RB |
