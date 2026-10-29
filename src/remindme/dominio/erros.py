from typing import Dict, Optional


class OperacaoRecusada(Exception):
    """Recusa de uma operação por regra de negócio. Nenhum dado é alterado.

    `campos` liga cada campo inválido ao seu motivo, para a interface mostrar o erro junto do campo (RNF-14).
    """

    def __init__(self, motivo: str, campos: Optional[Dict[str, str]] = None):
        super().__init__(motivo)
        self.motivo = motivo
        self.campos = dict(campos or {})


class OperacaoNegada(OperacaoRecusada):
    """RF-67: o perfil do usuário não tem permissão para a operação (RNF-02)."""


def recusar_campos(campos: Dict[str, str]) -> None:
    """Recusa com todos os campos inválidos de uma vez (RNF-14), quando há algum."""
    if campos:
        raise OperacaoRecusada(" ".join(campos.values()), campos)
