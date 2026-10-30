"""Dados da empresa que usa o RemindMe (OPEN-54): um único cadastro, visto por todos e mantido pelo Dono."""

import re
from dataclasses import dataclass
from typing import Dict, Tuple

from remindme.dominio.cliente import EMAIL, normalizar_documento, tipo_do_documento
from remindme.dominio.erros import recusar_campos

CAMPOS = ("razao_social", "nome_fantasia", "cnpj", "telefone", "email", "endereco")
TAMANHO_MAXIMO = 200


@dataclass(frozen=True)
class Empresa:
    razao_social: str
    nome_fantasia: str
    cnpj: str
    telefone: str
    email: str
    endereco: str

    @classmethod
    def preencher(
        cls, razao_social: object, nome_fantasia: object, cnpj: object, telefone: object, email: object, endereco: object
    ) -> "Empresa":
        """Razão social e CNPJ são obrigatórios; os demais, se informados, precisam ser válidos (RNF-14)."""
        textos = {nome: _texto(entrada) for nome, entrada in zip(CAMPOS, (razao_social, nome_fantasia, cnpj, telefone, email, endereco))}
        campos: Dict[str, str] = {}
        if not textos["razao_social"]:
            campos["razao_social"] = "Informe a razão social."
        textos["cnpj"] = normalizar_documento(textos["cnpj"])
        if not textos["cnpj"]:
            campos["cnpj"] = "Informe o CNPJ."
        elif tipo_do_documento(textos["cnpj"]) != "CNPJ":
            campos["cnpj"] = "Informe um CNPJ válido."
        textos["telefone"] = re.sub(r"\D", "", textos["telefone"])
        if textos["telefone"] and len(textos["telefone"]) not in (10, 11):
            campos["telefone"] = "Informe o telefone com DDD, por exemplo (11) 3456-7890."
        textos["email"] = textos["email"].lower()
        if textos["email"] and not EMAIL.match(textos["email"]):
            campos["email"] = "Informe um e-mail válido."
        for nome, texto in textos.items():
            if len(texto) > TAMANHO_MAXIMO and nome not in campos:
                campos[nome] = f"Use no máximo {TAMANHO_MAXIMO} caracteres."
        recusar_campos(campos)
        return cls(**textos)

    def diferencas(self, outra: "Empresa") -> Dict[str, Tuple[str, str]]:
        """Para a auditoria: cada campo que mudou, com o valor anterior e o novo (RF-05)."""
        return {c: (getattr(self, c), getattr(outra, c)) for c in CAMPOS if getattr(self, c) != getattr(outra, c)}


def _texto(entrada: object) -> str:
    return " ".join(entrada.split()) if isinstance(entrada, str) else ""
