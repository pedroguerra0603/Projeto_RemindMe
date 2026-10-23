from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RegistroAuditoria:
    """RF-62: usuário, data e hora, operação e registro afetado. RF-05: campo, valor anterior e novo valor.

    Imutável (RB-30). Operação automática não tem usuário e informa a rotina que a disparou (OPEN-30).
    """

    usuario_id: Optional[str]
    data_hora: datetime
    operacao: str
    registro_afetado: str
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None
    campo: Optional[str] = None
    automatica: bool = False
    rotina: Optional[str] = None

    def __post_init__(self):
        """INV-3 da Spec 001."""
        if not isinstance(self.data_hora, datetime):
            raise ValueError("O registro de auditoria exige data e hora.")
        if not self.operacao or not self.registro_afetado:
            raise ValueError("O registro de auditoria exige a operação e o registro afetado.")
        if self.automatica:
            if self.usuario_id is not None or not self.rotina:
                raise ValueError("Operação automática não tem usuário e informa a rotina.")
        elif not self.usuario_id:
            raise ValueError("O registro de auditoria exige o usuário, salvo em operação automática.")
