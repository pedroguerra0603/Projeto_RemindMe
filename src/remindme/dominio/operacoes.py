"""Operações sujeitas a permissão: as linhas da matriz da Spec 002 (OPEN-32) e a consulta de clientes (OPEN-42)."""

from enum import Enum


class Operacao(Enum):
    CADASTRAR_TITULO = "Cadastrar título"
    REGISTRAR_PAGAMENTO = "Registrar pagamento"
    VERIFICAR_VENCIMENTOS = "Verificar vencimentos"
    ESTORNAR_PAGAMENTO = "Estornar pagamento"
    CANCELAR_TITULO = "Cancelar título"
    CONSULTAR_TITULOS = "Consultar títulos"
    MANTER_CLIENTES = "Manter clientes"
    CONSULTAR_CLIENTES = "Consultar clientes"
    CONDUZIR_ORCAMENTO = "Conduzir orçamento"
    APROVAR_DESCONTO = "Aprovar desconto fora da alçada"
    GERENCIAR_OBRIGACOES = "Gerenciar obrigações"
    CLASSIFICAR_LANCAMENTO = "Classificar lançamento"
    APURAR_RESULTADO = "Apurar e consultar resultado"
    CONSULTAR_AUDITORIA = "Consultar auditoria"
    CONFIGURAR_REGRAS = "Configurar regras"
    IMPORTAR_CSV = "Importar CSV"
    EXPORTAR_CSV = "Exportar CSV"
    ADMINISTRAR_USUARIOS = "Administrar usuários e permissões"
    MANTER_EMPRESA = "Manter dados da empresa"

    @property
    def descricao(self) -> str:
        """O nome da operação no meio de uma frase: "cadastrar título"."""
        return self.value[0].lower() + self.value[1:]
