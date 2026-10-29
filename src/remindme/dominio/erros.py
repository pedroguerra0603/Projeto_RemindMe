from typing import Dict


class OperacaoRecusada(Exception):
    """Recusa de uma operação por regra de negócio. Nenhum dado é alterado."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo


class EntradaInvalida(OperacaoRecusada):
    """RNF-14: a recusa informa cada campo e o motivo."""

    def __init__(self, campos: Dict[str, str]):
        self.campos = dict(campos)
        super().__init__("; ".join(f"{campo}: {motivo}" for campo, motivo in self.campos.items()))


class AcessoNegado(OperacaoRecusada):
    """RNF-01, RNF-02, RF-67: sem sessão válida ou sem permissão do perfil."""
