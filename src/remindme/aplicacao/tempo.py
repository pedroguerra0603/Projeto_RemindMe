"""Data de referência do sistema (OPEN-26): o "hoje" é o de America/Sao_Paulo; os horários ficam em UTC."""

from datetime import date, datetime, timedelta, timezone, tzinfo


def _fuso_de_referencia() -> tzinfo:
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("America/Sao_Paulo")
    except Exception:
        # Sem a base de fusos do sistema (comum no Windows sem o pacote tzdata), vale o horário de Brasília,
        # sem horário de verão desde 2019.
        return timezone(timedelta(hours=-3), "America/Sao_Paulo")


FUSO_DE_REFERENCIA = _fuso_de_referencia()


def horario_local(momento: datetime) -> datetime:
    """Momento no fuso de referência. Momento sem fuso já é tratado como horário local."""
    if momento.tzinfo is None:
        return momento
    return momento.astimezone(FUSO_DE_REFERENCIA)


def data_local(momento: datetime) -> date:
    return horario_local(momento).date()
