"""Regras de perfil usadas pela camada de aplicação antes de chamar o domínio."""

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil, Usuario


def exigir_permissao_de_estorno(usuario: Usuario) -> None:
    """RB-02: somente o Dono estorna um pagamento."""
    if usuario.perfil is not Perfil.DONO:
        raise OperacaoRecusada("Somente o Dono estorna um pagamento (RB-02).")


def exigir_permissao_de_cancelamento(usuario: Usuario) -> None:
    """OPEN-16, decidida em 2026-10-03: somente o Dono cancela um título."""
    if usuario.perfil is not Perfil.DONO:
        raise OperacaoRecusada("Somente o Dono cancela um título (OPEN-16).")
