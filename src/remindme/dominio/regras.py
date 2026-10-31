"""Permissões fixadas por regra de negócio: não mudam por configuração (Spec 002, INV-4).

Cada regra de perfil fica só aqui (RNF-19): RB-02, RB-03, RB-15, OPEN-16 e OPEN-53. RB-26 foi retirada com o perfil Cliente (OPEN-57).
"""

from dataclasses import dataclass
from typing import Optional

from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Perfil


@dataclass(frozen=True)
class PermissaoFixada:
    permitido: bool
    regra: str
    motivo: str


# Exclusivas do Dono entre os perfis de negócio; o Administrador também pode, pela permissão global (OPEN-53).
_SOMENTE_O_DONO = {
    Operacao.ESTORNAR_PAGAMENTO: ("RB-02", "Somente o Dono estorna um pagamento (RB-02)."),
    Operacao.CANCELAR_TITULO: ("OPEN-16", "Somente o Dono cancela um título (OPEN-16)."),
    Operacao.APROVAR_DESCONTO: ("RB-15", "Somente o Dono aprova desconto fora da alçada (RB-15)."),
}

# OPEN-53, decidida em 2026-10-30 a pedido do professor: o Administrador é o administrador geral do sistema.
ADMINISTRADOR_GLOBAL = PermissaoFixada(
    True, "OPEN-53", "O Administrador tem todas as permissões do sistema (OPEN-53)."
)

# RB-03: o Contador consulta e exporta, mas não cria nem altera registros.
_CONTADOR_NAO_ALTERA = {
    Operacao.CADASTRAR_TITULO,
    Operacao.REGISTRAR_PAGAMENTO,
    Operacao.VERIFICAR_VENCIMENTOS,
    Operacao.MANTER_CLIENTES,
    Operacao.CONDUZIR_ORCAMENTO,
    Operacao.GERENCIAR_OBRIGACOES,
    Operacao.CLASSIFICAR_LANCAMENTO,
    Operacao.IMPORTAR_CSV,
}


def permissao_fixada(operacao: Operacao, perfil: Perfil) -> Optional[PermissaoFixada]:
    """A célula da matriz fixada por regra, ou None quando o Administrador pode alterá-la."""
    if perfil is Perfil.ADMINISTRADOR:
        return ADMINISTRADOR_GLOBAL
    if operacao in _SOMENTE_O_DONO:
        regra, motivo = _SOMENTE_O_DONO[operacao]
        return PermissaoFixada(perfil is Perfil.DONO, regra, motivo)
    if perfil is Perfil.CONTADOR and operacao in _CONTADOR_NAO_ALTERA:
        return PermissaoFixada(
            False, "RB-03", "O Contador consulta e exporta, mas não cria nem altera registros (RB-03)."
        )
    return None
