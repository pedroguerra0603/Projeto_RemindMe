from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class RegistroAuditoria:
    """Registro imutável de uma operação: quem, quando, o quê e sobre qual registro.

    RF-62: usuário, data e hora, operação e registro afetado. RF-05: campo, valor anterior e novo valor.
    RB-30: imutável (`frozen`). INV-3 e OPEN-30: o usuário só fica vazio em operação automática, que
    informa a rotina que a disparou.
    """

    usuario_id: Optional[str]
    data_hora: datetime
    operacao: str
    registro_afetado: str
    campo: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_novo: Optional[str] = None
    motivo: Optional[str] = None
    automatica: bool = False
    rotina: Optional[str] = None

    def __post_init__(self):
        """INV-3. Um registro incompleto é erro de programação, e não recusa de regra de negócio."""
        if not isinstance(self.data_hora, datetime):
            raise ValueError("O registro de auditoria exige data e hora (INV-3).")
        if not _preenchido(self.operacao) or not _preenchido(self.registro_afetado):
            raise ValueError("O registro de auditoria exige operação e registro afetado (INV-3).")
        if self.automatica:
            if self.usuario_id is not None or not _preenchido(self.rotina):
                raise ValueError(
                    "Operação automática tem usuário vazio e o nome da rotina (OPEN-30)."
                )
        elif not _preenchido(self.usuario_id) or self.rotina is not None:
            raise ValueError(
                "O registro de auditoria exige o usuário, salvo em operação automática (INV-3)."
            )


def _preenchido(texto: Optional[str]) -> bool:
    return isinstance(texto, str) and bool(texto.strip())
