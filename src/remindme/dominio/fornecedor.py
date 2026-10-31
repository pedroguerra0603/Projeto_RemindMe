"""Fornecedor (Spec 018): de quem a empresa compra e a quem deve contas a pagar. Mesma validação do cliente."""

from dataclasses import dataclass, replace
from typing import Tuple

from remindme.dominio.cliente import Alteracoes, validar_pessoa


@dataclass(frozen=True)
class Fornecedor:
    id: str
    nome: str
    documento: str
    contato: str

    @classmethod
    def cadastrar(cls, id: str, nome: object, documento: object, contato: object) -> "Fornecedor":
        """RF-87. Todos os campos inválidos de uma vez (RNF-14)."""
        nome_valido, documento_valido, contato_valido = validar_pessoa(nome, documento, contato, "fornecedor")
        return cls(id=id, nome=nome_valido, documento=documento_valido, contato=contato_valido)

    def alterado(self, nome: object, documento: object, contato: object) -> Tuple["Fornecedor", Alteracoes]:
        """A6: o fornecedor com os novos dados e, para cada campo que mudou, o valor anterior e o novo."""
        novo = Fornecedor.cadastrar(self.id, nome, documento, contato)
        alteracoes = {
            campo: (getattr(self, campo), getattr(novo, campo))
            for campo in ("nome", "documento", "contato")
            if getattr(self, campo) != getattr(novo, campo)
        }
        return replace(self, nome=novo.nome, documento=novo.documento, contato=novo.contato), alteracoes
