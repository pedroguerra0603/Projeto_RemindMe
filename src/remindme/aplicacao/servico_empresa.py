"""Dados da empresa (OPEN-54): todo usuário com sessão vê; quem tem "Manter dados da empresa" altera."""

from typing import Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.empresa import CAMPOS, Empresa
from remindme.dominio.operacoes import Operacao


class ServicoEmpresa:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._autorizacao = autorizacao or Autorizacao(relogio)
        self._execucao = Execucao(uow, relogio, erros or RegistroErrosNoLog(), self._autorizacao)

    def obter(self, sessao: Optional[str]) -> Optional[Empresa]:
        """Vazio enquanto ninguém preencheu os dados."""
        with self._execucao.do_usuario("consultar empresa", lambda uow: self._autorizacao.sessao(uow, sessao)[1]) as op:
            return op.uow.empresa.obter()

    def salvar(self, sessao: Optional[str], **dados: object) -> Empresa:
        """Cria ou altera os dados. RF-05: um registro de auditoria por campo alterado."""
        with self._execucao.operacao("alterar empresa", sessao, Operacao.MANTER_EMPRESA) as op:
            nova = Empresa.preencher(**{c: dados.get(c) for c in CAMPOS})
            atual = op.uow.empresa.obter() or Empresa(*[""] * len(CAMPOS))
            for campo, (anterior, novo) in atual.diferencas(nova).items():
                op.registrar("empresa", campo, anterior or None, novo or None)
            op.uow.empresa.salvar(nova)
        return nova
