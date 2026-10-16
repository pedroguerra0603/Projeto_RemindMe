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
    id: str
    nome: str
    perfil: Perfil
