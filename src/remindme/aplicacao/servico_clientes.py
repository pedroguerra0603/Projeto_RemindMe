"""Casos de uso da Spec 003: cadastro, alteração e pesquisa de clientes (UC-03)."""

import uuid
from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.cliente import Cliente, normalizar_documento
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao

DOCUMENTO_REPETIDO = "Já existe um cliente com este documento."


class ServicoClientes:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    def cadastrar_cliente(self, sessao: Optional[str], nome: object, documento: object, contato: object) -> Cliente:
        """RF-01. E1 a E4. INV-1: o documento é único. INV-4: auditoria campo a campo."""
        with self._execucao.operacao("cadastrar cliente", sessao, Operacao.MANTER_CLIENTES) as op:
            cliente = Cliente.cadastrar(uuid.uuid4().hex, nome, documento, contato)
            _exigir_documento_livre(op, cliente)
            op.uow.clientes.salvar(cliente)
            for campo in ("nome", "documento", "contato"):
                op.registrar(_ref(cliente), campo, None, getattr(cliente, campo))
        return cliente

    def alterar_cliente(
        self, sessao: Optional[str], cliente_id: str, nome: object, documento: object, contato: object
    ) -> Cliente:
        """A1, RF-05: um registro por campo alterado, com o valor anterior e o novo."""
        with self._execucao.operacao("alterar cliente", sessao, Operacao.MANTER_CLIENTES) as op:
            atual = _obter(op, cliente_id)
            alterado, alteracoes = atual.alterado(nome, documento, contato)
            if "documento" in alteracoes:
                _exigir_documento_livre(op, alterado)
            if alteracoes:
                op.uow.clientes.salvar(alterado)
            for campo, (anterior, novo) in alteracoes.items():
                op.registrar(_ref(alterado), campo, anterior, novo)
        return alterado

    def consultar_clientes(self, sessao: Optional[str], termo: Optional[str] = None) -> List[Cliente]:
        """A2: por parte do nome, sem diferença de maiúsculas, ou pelo documento com ou sem pontuação."""
        with self._execucao.operacao("consultar clientes", sessao, Operacao.CONSULTAR_CLIENTES) as op:
            clientes = op.uow.clientes.listar()
        busca = termo.strip().casefold() if isinstance(termo, str) else ""
        documento = normalizar_documento(termo)
        encontrados = [
            c for c in clientes
            if not busca or busca in c.nome.casefold() or (documento and documento in c.documento)
        ]
        return sorted(encontrados, key=lambda c: (c.nome.casefold(), c.documento))

    def obter_cliente(self, sessao: Optional[str], cliente_id: str) -> Cliente:
        with self._execucao.operacao("consultar clientes", sessao, Operacao.CONSULTAR_CLIENTES) as op:
            return _obter(op, cliente_id)


def _exigir_documento_livre(op: OperacaoAuditada, cliente: Cliente) -> None:
    outro = op.uow.clientes.obter_por_documento(cliente.documento)
    if outro is not None and outro.id != cliente.id:
        raise OperacaoRecusada(DOCUMENTO_REPETIDO, {"documento": DOCUMENTO_REPETIDO})


def _obter(op: OperacaoAuditada, cliente_id: str) -> Cliente:
    cliente = op.uow.clientes.obter(cliente_id) if isinstance(cliente_id, str) else None
    if cliente is None:
        raise OperacaoRecusada("Cliente não encontrado.")
    return cliente


def _ref(cliente: Cliente) -> str:
    return f"cliente {cliente.id}"
