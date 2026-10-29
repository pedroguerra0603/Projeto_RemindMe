"""Matriz de permissões por perfil (Spec 002, seção 4; OPEN-32). Negado por padrão (RNF-02)."""

from enum import Enum
from typing import Dict, FrozenSet, Optional, Tuple

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil


class Operacao(Enum):
    """Uma linha da matriz. O valor é o nome apresentado ao usuário."""

    MANTER_TITULOS = "Cadastrar título, registrar pagamento"
    VERIFICAR_VENCIMENTOS = "Verificar vencimentos"
    ESTORNAR_PAGAMENTO = "Estornar pagamento"
    CANCELAR_TITULO = "Cancelar título"
    CONSULTAR_TITULOS = "Consultar títulos"
    MANTER_CLIENTES = "Manter clientes"
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


_D = Perfil.DONO
_O = Perfil.OPERADOR_FINANCEIRO
_C = Perfil.CONTADOR
_A = Perfil.ADMINISTRADOR

MATRIZ_INICIAL: Dict[Perfil, FrozenSet[Operacao]] = {
    _D: frozenset(
        {
            Operacao.MANTER_TITULOS,
            Operacao.VERIFICAR_VENCIMENTOS,
            Operacao.ESTORNAR_PAGAMENTO,
            Operacao.CANCELAR_TITULO,
            Operacao.CONSULTAR_TITULOS,
            Operacao.MANTER_CLIENTES,
            Operacao.CONDUZIR_ORCAMENTO,
            Operacao.APROVAR_DESCONTO,
            Operacao.GERENCIAR_OBRIGACOES,
            Operacao.CLASSIFICAR_LANCAMENTO,
            Operacao.APURAR_RESULTADO,
            Operacao.CONSULTAR_AUDITORIA,
            Operacao.IMPORTAR_CSV,
            Operacao.EXPORTAR_CSV,
        }
    ),
    _O: frozenset(
        {
            Operacao.MANTER_TITULOS,
            Operacao.VERIFICAR_VENCIMENTOS,
            Operacao.CONSULTAR_TITULOS,
            Operacao.MANTER_CLIENTES,
            Operacao.CONDUZIR_ORCAMENTO,
            Operacao.GERENCIAR_OBRIGACOES,
            Operacao.CLASSIFICAR_LANCAMENTO,
            Operacao.APURAR_RESULTADO,
            Operacao.IMPORTAR_CSV,
            Operacao.EXPORTAR_CSV,
        }
    ),
    _C: frozenset(
        {
            Operacao.CONSULTAR_TITULOS,
            Operacao.APURAR_RESULTADO,
            Operacao.CONSULTAR_AUDITORIA,
            Operacao.EXPORTAR_CSV,
        }
    ),
    # O acesso do Cliente aos próprios títulos entra com a Spec 009 (OPEN-08).
    Perfil.CLIENTE: frozenset(),
    _A: frozenset(
        {
            Operacao.CONSULTAR_AUDITORIA,
            Operacao.CONFIGURAR_REGRAS,
            Operacao.ADMINISTRAR_USUARIOS,
        }
    ),
}


def _fixada_para_todos(operacao: Operacao, dono: bool, regra: str) -> Dict[Tuple[Perfil, Operacao], str]:
    return {(perfil, operacao): regra for perfil in Perfil if dono or perfil is not _D}


# Células marcadas com F na matriz: não mudam por configuração (INV-4). O valor é a regra que as fixa.
FIXADAS: Dict[Tuple[Perfil, Operacao], str] = {
    **_fixada_para_todos(Operacao.ESTORNAR_PAGAMENTO, True, "RB-02"),
    **_fixada_para_todos(Operacao.CANCELAR_TITULO, True, "OPEN-16"),
    **_fixada_para_todos(Operacao.APROVAR_DESCONTO, True, "RB-15"),
    **{
        (_C, operacao): "RB-03"
        for operacao in (
            Operacao.MANTER_TITULOS,
            Operacao.VERIFICAR_VENCIMENTOS,
            Operacao.MANTER_CLIENTES,
            Operacao.CONDUZIR_ORCAMENTO,
            Operacao.GERENCIAR_OBRIGACOES,
            Operacao.CLASSIFICAR_LANCAMENTO,
            Operacao.IMPORTAR_CSV,
        )
    },
    (Perfil.CLIENTE, Operacao.CONSULTAR_TITULOS): "RB-26",
    # Provisório (OPEN-36): sem isso, o Administrador poderia trancar o sistema para todos.
    (_A, Operacao.ADMINISTRAR_USUARIOS): "OPEN-36",
}


def regra_que_fixa(perfil: Perfil, operacao: Operacao) -> Optional[str]:
    return FIXADAS.get((perfil, operacao))


def exigir_permissao_alteravel(perfil: Perfil, operacao: Operacao) -> None:
    """E5 da Spec 002: permissão fixada por regra de negócio não é concedida nem retirada."""
    regra = regra_que_fixa(perfil, operacao)
    if regra is not None:
        raise OperacaoRecusada(
            f"A permissão “{operacao.value}” do perfil {perfil.value} é fixada por regra de negócio ({regra})."
        )


def permissoes_efetivas(perfil: Perfil, configuradas: FrozenSet[Operacao]) -> FrozenSet[Operacao]:
    """INV-4: a configuração vale só para as células não fixadas; as fixadas seguem a matriz inicial."""
    efetivas = set()
    for operacao in Operacao:
        if regra_que_fixa(perfil, operacao) is not None:
            permitida = operacao in MATRIZ_INICIAL[perfil]
        else:
            permitida = operacao in configuradas
        if permitida:
            efetivas.add(operacao)
    return frozenset(efetivas)
