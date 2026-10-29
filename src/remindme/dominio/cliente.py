"""Cliente: pessoa ou empresa que recebe orçamentos e deve títulos (RF-01, UC-03)."""

import re
from dataclasses import dataclass
from typing import Dict, Optional

from remindme.dominio.erros import EntradaInvalida

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    documento: str
    email: str = ""
    telefone: str = ""

    @classmethod
    def criar(
        cls,
        id: str,
        nome: Optional[str],
        documento: Optional[str],
        email: Optional[str] = "",
        telefone: Optional[str] = "",
    ) -> "Cliente":
        """UC-03, E1 e E2: nome e documento válido são obrigatórios; o contato, quando informado, é válido."""
        nome = (nome or "").strip()
        email = (email or "").strip()
        telefone = (telefone or "").strip()
        erros: Dict[str, str] = {}
        if not nome:
            erros["nome"] = "obrigatório"
        documento_normalizado = normalizar_documento(documento)
        if not (documento or "").strip():
            erros["documento"] = "obrigatório"
        elif not documento_valido(documento_normalizado):
            erros["documento"] = "CPF ou CNPJ inválido"
        if email and not _EMAIL.match(email):
            erros["e-mail"] = "formato inválido"
        if telefone and len(re.sub(r"\D", "", telefone)) < 8:
            erros["telefone"] = "deve ter ao menos 8 dígitos"
        if erros:
            raise EntradaInvalida(erros)
        return cls(id=id, nome=nome, documento=documento_normalizado, email=email, telefone=telefone)

    @property
    def documento_formatado(self) -> str:
        d = self.documento
        if len(d) == 11:
            return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def normalizar_documento(documento: Optional[str]) -> str:
    return re.sub(r"\D", "", documento or "")


def documento_valido(digitos: str) -> bool:
    """CPF (11 dígitos) ou CNPJ (14 dígitos), com os dígitos verificadores."""
    if len(digitos) not in (11, 14) or len(set(digitos)) == 1:
        return False
    if len(digitos) == 11:
        pesos = [list(range(10, 1, -1)), list(range(11, 1, -1))]
    else:
        pesos = [[5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]]
    for peso in pesos:
        base = digitos[: len(peso)]
        resto = sum(int(d) * p for d, p in zip(base, peso)) % 11
        verificador = 0 if resto < 2 else 11 - resto
        if int(digitos[len(peso)]) != verificador:
            return False
    return True
