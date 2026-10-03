from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RegistroAuditoria:
    """RF-62: usuário, data e hora, operação e registro afetado."""

    usuario_id: str
    data_hora: datetime
    operacao: str
    registro_afetado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None
