"""Casos de uso do UC-03 (Spec 003): cadastrar, alterar e consultar clientes."""

import uuid
from typing import List, Optional

from remindme.aplicacao.auditoria import Auditoria, RegistroErrosNoLog
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalhoCompleta
from remindme.dominio.cliente import Cliente
from remindme.dominio.erros import EntradaInvalida, OperacaoRecusada
from remindme.dominio.usuario import Usuario

CAMPOS = ("nome", "documento", "email", "telefone")


class ServicoClientes:
    def __init__(
        self, uow: UnidadeDeTrabalhoCompleta, relogio: Relogio, erros: Optional[RegistroErros] = None
    ):
        self._uow = uow
        self._auditoria = Auditoria(uow, relogio, erros or RegistroErrosNoLog())

    def cadastrar_cliente(
        self,
        usuario: Usuario,
        nome: Optional[str],
        documento: Optional[str],
        email: Optional[str] = "",
        telefone: Optional[str] = "",
    ) -> Cliente:
        """Fluxo principal, E1 e E2."""
        cliente = Cliente.criar(uuid.uuid4().hex, nome, documento, email, telefone)
        with self._auditoria.operacao("cadastrar cliente", usuario) as op:
            _exigir_documento_unico(op.uow, cliente)
            op.uow.clientes.salvar(cliente)
            op.registrar(_ref(cliente), "nome", None, cliente.nome)
        return cliente

    def alterar_cliente(
        self,
        usuario: Usuario,
        cliente_id: str,
        nome: Optional[str],
        documento: Optional[str],
        email: Optional[str] = "",
        telefone: Optional[str] = "",
    ) -> Cliente:
        """A1: um registro de auditoria por campo alterado, com valor anterior e novo (RF-05)."""
        with self._auditoria.operacao("alterar cliente", usuario) as op:
            anterior = op.uow.clientes.obter(cliente_id)
            if anterior is None:
                raise OperacaoRecusada("Cliente não encontrado.")
            novo = Cliente.criar(cliente_id, nome, documento, email, telefone)
            _exigir_documento_unico(op.uow, novo)
            op.uow.clientes.salvar(novo)
            for campo in CAMPOS:
                antes, depois = getattr(anterior, campo), getattr(novo, campo)
                if antes != depois:
                    op.registrar(_ref(novo), campo, antes, depois)
        return novo

    def listar_clientes(self, busca: Optional[str] = None) -> List[Cliente]:
        """A2: pesquisa por nome ou documento."""
        with self._uow as uow:
            return uow.clientes.listar((busca or "").strip() or None)

    def obter_cliente(self, cliente_id: str) -> Cliente:
        with self._uow as uow:
            cliente = uow.clientes.obter(cliente_id)
        if cliente is None:
            raise OperacaoRecusada("Cliente não encontrado.")
        return cliente


def _exigir_documento_unico(uow, cliente: Cliente) -> None:
    existente = uow.clientes.obter_por_documento(cliente.documento)
    if existente is not None and existente.id != cliente.id:
        raise EntradaInvalida({"documento": "já cadastrado"})


def _ref(cliente: Cliente) -> str:
    return f"cliente {cliente.id}"
