# Modelo de Domínio - RemindMe

Este documento descreve as entidades centrais do negócio, suas responsabilidades e como elas se relacionam. O foco aqui é no problema de negócio, sem contaminação com detalhes técnicos (como banco de dados ou telas).

## 1. Dicionário de Classes (Entidades do Domínio)

* **Usuário:** Representa os operadores do sistema (Dono, Contador). Pode ser o responsável pela aprovação de descontos e cumprimento de obrigações.
* **Perfil & Alçada de Desconto:** Define as permissões de acesso e o limite (percentual máximo) de desconto que um usuário pode aplicar em um orçamento sem precisar de aprovação superior.
* **Cliente:** A entidade que solicita orçamentos e para quem os títulos são gerados e cobrados.
* **Orçamento & ItemOrçamento:** Representa a proposta comercial. Contém itens (produtos/serviços). É a origem do ciclo financeiro.
* **Título & Pagamento:** Quando um orçamento é aprovado, ele origina um Título (Contas a Receber). O título recebe pagamentos (totais ou parciais) e controla o estado de inadimplência (vencido, baixado, aberto).
* **Etapa de Cobrança & Histórico de Cobrança:** Define as réguas de cobrança (ex: "3 dias antes do vencimento", "5 dias após o vencimento"). O histórico registra cada tentativa e o resultado.
* **Obrigação:** Representa o calendário de compromissos fiscais e operacionais. Possui prazos, periodicidade e um usuário responsável.
* **Lançamento Financeiro & Categoria:** Representa a movimentação de apuração (Receita/Despesa). Os lançamentos são gerados pelas baixas de pagamento e classificados para a DRE (Demonstração de Resultado).
