"""Relógio do sistema no fuso de referência (OPEN-26: America/Sao_Paulo)."""

from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        FUSO = ZoneInfo("America/Sao_Paulo")
    except ZoneInfoNotFoundError:
        FUSO = None
except ImportError:  # pragma: no cover
    FUSO = None

if FUSO is None:
    # Sem a base de fusos (comum no Windows), usa o deslocamento fixo: o Brasil não tem horário de verão desde 2019.
    FUSO = timezone(timedelta(hours=-3), "America/Sao_Paulo")


class RelogioDoSistema:
    def agora(self) -> datetime:
        return datetime.now(FUSO)
