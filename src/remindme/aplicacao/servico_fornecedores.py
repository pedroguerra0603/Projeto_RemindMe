"""Casos de uso da Spec 018: cadastro, alteração e pesquisa de fornecedores (UC-15)."""

import uuid
from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.cliente import normalizar_documento
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.fornecedor import Fornecedor
from remindme.dominio.operacoes import Operacao

DOCUMENTO_REPETIDO = "Já existe um fornecedor com este documento."


class ServicoFornecedores:
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

    def cadastrar_fornecedor(self, sessao: Optional[str], nome: object, documento: object, contato: object) -> Fornecedor:
        """RF-87. INV-6: o documento é único entre os fornecedores. Auditoria campo a campo."""
        with self._execucao.operacao("cadastrar fornecedor", sessao, Operacao.MANTER_FORNECEDORES) as op:
            fornecedor = Fornecedor.cadastrar(uuid.uuid4().hex, nome, documento, contato)
            _exigir_documento_livre(op, fornecedor)
            op.uow.fornecedores.salvar(fornecedor)
            for campo in ("nome", "documento", "contato"):
                op.registrar(_ref(fornecedor), campo, None, getattr(fornecedor, campo))
        return fornecedor

    def alterar_fornecedor(
        self, sessao: Optional[str], fornecedor_id: str, nome: object, documento: object, contato: object
    ) -> Fornecedor:
        """A6: um registro por campo alterado, com o valor anterior e o novo."""
        with self._execucao.operacao("alterar fornecedor", sessao, Operacao.MANTER_FORNECEDORES) as op:
            atual = _obter(op, fornecedor_id)
            alterado, alteracoes = atual.alterado(nome, documento, contato)
            if "documento" in alteracoes:
                _exigir_documento_livre(op, alterado)
            if alteracoes:
                op.uow.fornecedores.salvar(alterado)
            for campo, (anterior, novo) in alteracoes.items():
                op.registrar(_ref(alterado), campo, anterior, novo)
        return alterado

    def consultar_fornecedores(self, sessao: Optional[str], termo: Optional[str] = None) -> List[Fornecedor]:
        """Por parte do nome, sem diferença de maiúsculas, ou pelo documento com ou sem pontuação."""
        with self._execucao.operacao("consultar fornecedores", sessao, Operacao.CONSULTAR_FORNECEDORES) as op:
            fornecedores = op.uow.fornecedores.listar()
        busca = termo.strip().casefold() if isinstance(termo, str) else ""
        documento = normalizar_documento(termo)
        encontrados = [
            f for f in fornecedores
            if not busca or busca in f.nome.casefold() or (documento and documento in f.documento)
        ]
        return sorted(encontrados, key=lambda f: (f.nome.casefold(), f.documento))

    def obter_fornecedor(self, sessao: Optional[str], fornecedor_id: str) -> Fornecedor:
        with self._execucao.operacao("consultar fornecedores", sessao, Operacao.CONSULTAR_FORNECEDORES) as op:
            return _obter(op, fornecedor_id)


def _exigir_documento_livre(op: OperacaoAuditada, fornecedor: Fornecedor) -> None:
    outro = op.uow.fornecedores.obter_por_documento(fornecedor.documento)
    if outro is not None and outro.id != fornecedor.id:
        raise OperacaoRecusada(DOCUMENTO_REPETIDO, {"documento": DOCUMENTO_REPETIDO})


def _obter(op: OperacaoAuditada, fornecedor_id: str) -> Fornecedor:
    fornecedor = op.uow.fornecedores.obter(fornecedor_id) if isinstance(fornecedor_id, str) else None
    if fornecedor is None:
        raise OperacaoRecusada("Fornecedor não encontrado.")
    return fornecedor


def _ref(fornecedor: Fornecedor) -> str:
    return f"fornecedor {fornecedor.id}"
