"""Usuário e perfil (Spec 002). Cada usuário tem exatamente um perfil (RF-02, INV-1)."""

import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Dict

from remindme.dominio.erros import OperacaoRecusada, recusar_campos


class Perfil(Enum):
    DONO = "Dono"
    OPERADOR_FINANCEIRO = "Operador Financeiro"
    CONTADOR = "Contador"
    CLIENTE = "Cliente"
    ADMINISTRADOR = "Administrador"


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TAMANHO_MAXIMO = 200


@dataclass(frozen=True)
class Usuario:
    id: str
    nome: str
    perfil: Perfil
    email: str = ""
    ativo: bool = True

    @classmethod
    def cadastrar(cls, id: str, nome: object, email: object, perfil: object) -> "Usuario":
        """RF-02, A1. E7: nome, e-mail e perfil são obrigatórios, e a recusa indica todos os campos."""
        campos: Dict[str, str] = {}
        nome_limpo = _texto(nome)
        email_limpo = normalizar_email(email)
        if not nome_limpo:
            campos["nome"] = "Informe o nome."
        elif len(nome_limpo) > TAMANHO_MAXIMO:
            campos["nome"] = f"O nome tem no máximo {TAMANHO_MAXIMO} caracteres."
        if not email_limpo:
            campos["email"] = "Informe o e-mail."
        elif not EMAIL.match(email_limpo) or len(email_limpo) > TAMANHO_MAXIMO:
            campos["email"] = "Informe um e-mail válido, por exemplo nome@empresa.com.br."
        motivo_perfil = _motivo_do_perfil(perfil)
        if motivo_perfil:
            campos["perfil"] = motivo_perfil
        recusar_campos(campos)
        return cls(id=id, nome=nome_limpo, perfil=perfil, email=email_limpo, ativo=True)

    def com_perfil(self, perfil: object) -> "Usuario":
        """A2: troca o perfil, mantendo exatamente um (INV-1)."""
        motivo = _motivo_do_perfil(perfil)
        if motivo:
            raise OperacaoRecusada(motivo, {"perfil": motivo})
        if perfil is self.perfil:
            raise OperacaoRecusada("O usuário já tem esse perfil.", {"perfil": "O usuário já tem esse perfil."})
        return replace(self, perfil=perfil)

    def ativado(self) -> "Usuario":
        """OPEN-55: o Administrador ativa a conta criada pela tela de entrada."""
        if self.ativo:
            raise OperacaoRecusada("O usuário já está ativo.")
        return replace(self, ativo=True)

    def inativado(self) -> "Usuario":
        """A3: o histórico é preservado; só o acesso termina."""
        if not self.ativo:
            raise OperacaoRecusada("O usuário já está inativo.")
        return replace(self, ativo=False)


def normalizar_email(email: object) -> str:
    return _texto(email).lower()


def _motivo_do_perfil(perfil: object) -> str:
    if not isinstance(perfil, Perfil):
        return "Escolha um perfil."
    if perfil is Perfil.CLIENTE:
        # OPEN-46, decidida em 2026-10-23: o Cliente acessa por link com código (OPEN-08), na Spec 009.
        return "O Cliente não é cadastrado como usuário: ele acessa por link com código (Spec 009)."
    return ""


def _texto(texto: object) -> str:
    return texto.strip() if isinstance(texto, str) else ""
