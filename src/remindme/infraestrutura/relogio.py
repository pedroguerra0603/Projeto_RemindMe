"""Relógio do sistema: horários em UTC (OPEN-26). A data de referência sai de `aplicacao.tempo`."""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional


class RelogioDoSistema:
    def agora(self) -> datetime:
        return datetime.now(timezone.utc)


class RelogioCongelavel:
    """Delega ao relógio de base; dentro de `congelado()`, devolve sempre o mesmo instante.

    A preparação da demonstração faz dezenas de operações seguidas: com o relógio andando, a virada da meia-noite
    no meio dela dava ao envio de um orçamento uma data posterior à da decisão do cliente.
    """

    def __init__(self, base) -> None:
        self._base = base
        self._fixo: Optional[datetime] = None

    def agora(self) -> datetime:
        return self._fixo if self._fixo is not None else self._base.agora()

    @contextmanager
    def congelado(self) -> Iterator[datetime]:
        self._fixo = self._base.agora()
        try:
            yield self._fixo
        finally:
            self._fixo = None
