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

---

## 2. Diagrama de Classes Conceitual (UML)

*(O bloco abaixo é renderizado automaticamente pelo GitHub como uma imagem de diagrama UML)*

```mermaid
classDiagram
    %% Entidades de Acesso e Regras
    class Usuario {
        +id: UUID
        +nome: String
        +email: String
    }
    class Perfil {
        +nome: String
    }
    class AlcadaDesconto {
        +percentual_maximo: Decimal
    }
    
    %% Entidades Comerciais
    class Cliente {
        +id: UUID
        +nome: String
        +documento: String
    }
    class Orcamento {
        +id: UUID
        +data: Date
        +estado: EstadoOrcamento
        +valor_total: Decimal
        +desconto_aplicado: Decimal
        +aprovar()
        +cancelar()
        +validarAlcada()
    }
    class ItemOrcamento {
        +descricao: String
        +quantidade: int
        +valor_unitario: Decimal
    }
    
    %% Entidades Financeiras
    class Titulo {
        +id: UUID
        +valor: Decimal
        +vencimento: Date
        +estado: EstadoTitulo
        +registrarPagamento()
        +baixar()
        +renegociar()
    }
    class Pagamento {
        +id: UUID
        +valor_pago: Decimal
        +data: Date
        +estornar()
    }
    
    %% Entidades de Cobrança Automática
    class SequenciaCobranca {
        +nome: String
    }
    class EtapaCobranca {
        +prazo_dias: int
        +mensagem: String
        +acao: String
    }
    class HistoricoCobranca {
        +data: Date
        +resultado: String
    }
    
    %% Entidades de Obrigações
    class Obrigacao {
        +id: UUID
        +tipo: String
        +periodicidade: String
        +prazo: Date
        +estado: EstadoObrigacao
        +registrarCumprimento()
        +anexarEvidencia()
    }
    
    %% Entidades de Apuração
    class LancamentoFinanceiro {
        +id: UUID
        +valor: Decimal
        +tipo: TipoLancamento
        +data: Date
    }
    class CategoriaFinanceira {
        +nome: String
    }

    %% Relacionamentos e Multiplicidades
    Usuario "1" -- "1" Perfil : possui >
    Perfil "1" -- "0..1" AlcadaDesconto : define >
    
    Cliente "1" -- "0..*" Orcamento : solicita >
    Orcamento "1" *-- "1..*" ItemOrcamento : contem >
    
    Orcamento "1" -- "0..1" Titulo : origina >
    Titulo "1" *-- "0..*" Pagamento : recebe >
    
    SequenciaCobranca "1" *-- "1..*" EtapaCobranca : possui >
    EtapaCobranca "1" -- "0..*" HistoricoCobranca : gera >
    Titulo "1" -- "0..*" HistoricoCobranca : possui >
    
    Usuario "1" -- "0..*" Obrigacao : responsável por >
    
    Pagamento "1" -- "1" LancamentoFinanceiro : gera >
    LancamentoFinanceiro "0..*" -- "0..1" CategoriaFinanceira : classificado como >
