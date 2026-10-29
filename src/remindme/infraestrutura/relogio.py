"""Relógio do sistema: horários em UTC (OPEN-26). A data de referência sai de `aplicacao.tempo`."""

from datetime import datetime, timezone


class RelogioDoSistema:
    def agora(self) -> datetime:
        return datetime.now(timezone.utc)
