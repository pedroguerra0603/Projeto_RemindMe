from dataclasses import dataclass
from enum import Enum


class Perfil(Enum):
    DONO = "Dono"
    OPERADOR_FINANCEIRO = "Operador Financeiro"
    CONTADOR = "Contador"
    CLIENTE = "Cliente"
    ADMINISTRADOR = "Administrador"


@dataclass(frozen=True)
class Usuario:
    """INV-1 da Spec 002: todo usuário tem exatamente um perfil. A senha não fica aqui (INV-3)."""

    id: str
    nome: str
    perfil: Perfil
    email: str = ""
    ativo: bool = True
