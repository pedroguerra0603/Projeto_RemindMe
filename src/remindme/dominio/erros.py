class OperacaoRecusada(Exception):
    """Recusa de uma operação por regra de negócio. Nenhum dado é alterado."""

    def __init__(self, motivo: str):
        super().__init__(motivo)
        self.motivo = motivo
