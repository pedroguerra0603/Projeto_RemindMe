"""Cliente (Spec 003): nome, documento e contato (UC-03). Documento válido: OPEN-40. Contato: OPEN-41."""

import re
from dataclasses import dataclass, replace
from typing import Dict, Optional, Tuple

from remindme.dominio.erros import recusar_campos

TAMANHO_MAXIMO = 200
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PONTUACAO_DO_DOCUMENTO = re.compile(r"[\s./-]")
_PONTUACAO_DO_TELEFONE = re.compile(r"[\s().+-]")

Alteracoes = Dict[str, Tuple[str, str]]


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    documento: str
    contato: str

    @classmethod
    def cadastrar(cls, id: str, nome: object, documento: object, contato: object) -> "Cliente":
        """RF-01. E1, E3 e E4 de uma vez, com todos os campos inválidos (RNF-14)."""
        nome_valido, documento_valido, contato_valido = validar_pessoa(nome, documento, contato, "cliente")
        return cls(id=id, nome=nome_valido, documento=documento_valido, contato=contato_valido)

    def alterado(self, nome: object, documento: object, contato: object) -> Tuple["Cliente", Alteracoes]:
        """A1: o cliente com os novos dados e, para cada campo que mudou, o valor anterior e o novo."""
        novo = Cliente.cadastrar(self.id, nome, documento, contato)
        alteracoes = {
            campo: (getattr(self, campo), getattr(novo, campo))
            for campo in ("nome", "documento", "contato")
            if getattr(self, campo) != getattr(novo, campo)
        }
        return replace(self, nome=novo.nome, documento=novo.documento, contato=novo.contato), alteracoes


def validar_pessoa(nome: object, documento: object, contato: object, sujeito: str) -> Tuple[str, str, str]:
    """Nome, documento e contato normalizados, ou a recusa com todos os campos inválidos (RNF-14).

    Vale para o cliente (Spec 003) e para o fornecedor (Spec 018); `sujeito` entra na mensagem do nome."""
    campos: Dict[str, str] = {}
    nome_valido = _nome(nome, campos, sujeito)
    documento_valido = _documento(documento, campos)
    contato_valido = _contato(contato, campos)
    recusar_campos(campos)
    return nome_valido, documento_valido, contato_valido


def normalizar_documento(documento: object) -> str:
    """O documento só com letras maiúsculas e dígitos, como é guardado (INV-2)."""
    if not isinstance(documento, str):
        return ""
    return _PONTUACAO_DO_DOCUMENTO.sub("", documento).upper()


def tipo_do_documento(documento: str) -> Optional[str]:
    """"CPF", "CNPJ" ou None, para um documento já normalizado e válido."""
    if _cpf_valido(documento):
        return "CPF"
    if _cnpj_valido(documento):
        return "CNPJ"
    return None


def _nome(nome: object, campos: Dict[str, str], sujeito: str) -> str:
    texto = " ".join(nome.split()) if isinstance(nome, str) else ""
    if not texto:
        campos["nome"] = f"Informe o nome do {sujeito}."
    elif len(texto) > TAMANHO_MAXIMO:
        campos["nome"] = f"O nome tem no máximo {TAMANHO_MAXIMO} caracteres."
    return texto


def _documento(documento: object, campos: Dict[str, str]) -> str:
    texto = normalizar_documento(documento)
    if not texto:
        campos["documento"] = "Informe o CPF ou o CNPJ."
    elif tipo_do_documento(texto) is None:
        campos["documento"] = "Informe um CPF (11 dígitos) ou um CNPJ (14 caracteres) válido."
    return texto


def _contato(contato: object, campos: Dict[str, str]) -> str:
    """OPEN-41, decidida em 2026-10-23: e-mail ou telefone com DDD (10 ou 11 dígitos)."""
    texto = contato.strip() if isinstance(contato, str) else ""
    if not texto:
        campos["contato"] = "Informe um e-mail ou um telefone com DDD."
        return texto
    if "@" in texto:
        if EMAIL.match(texto) and len(texto) <= TAMANHO_MAXIMO:
            return texto.lower()
    else:
        digitos = _PONTUACAO_DO_TELEFONE.sub("", texto)
        if digitos.startswith("55") and len(digitos) in (12, 13):
            digitos = digitos[2:]
        if digitos.isdigit() and len(digitos) in (10, 11) and digitos[0] != "0":
            return digitos
    campos["contato"] = "Informe um e-mail válido ou um telefone com DDD, por exemplo (11) 98765-4321."
    return texto


def _cpf_valido(documento: str) -> bool:
    if len(documento) != 11 or not documento.isdigit() or len(set(documento)) == 1:
        return False
    numeros = [int(c) for c in documento]
    for posicao in (9, 10):
        soma = sum(n * peso for n, peso in zip(numeros[:posicao], range(posicao + 1, 1, -1)))
        digito = (soma * 10) % 11 % 10
        if digito != numeros[posicao]:
            return False
    return True


def _cnpj_valido(documento: str) -> bool:
    """CNPJ numérico ou alfanumérico (IN RFB 2.229/2024): o valor de cada caractere é o código ASCII
    menos 48, e os dois últimos são dígitos verificadores pelo módulo 11."""
    if len(documento) != 14 or not documento[12:].isdigit() or len(set(documento)) == 1:
        return False
    if not all(c.isdigit() or "A" <= c <= "Z" for c in documento[:12]):
        return False
    valores = [ord(c) - 48 for c in documento]
    for posicao, pesos in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        resto = sum(v * p for v, p in zip(valores[:posicao], pesos)) % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != valores[posicao]:
            return False
    return True
