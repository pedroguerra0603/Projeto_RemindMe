"""Caixa de saída (Spec 005): o que o canal de notificação tentou entregar aos clientes."""

from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import Mensagem, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.operacoes import Operacao


class ServicoMensagens:
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

    def consultar(self, sessao: Optional[str]) -> List[Mensagem]:
        """Da mais recente para a mais antiga."""
        with self._execucao.operacao("consultar mensagens", sessao, Operacao.CONSULTAR_MENSAGENS) as op:
            mensagens = op.uow.mensagens.listar()
        return sorted(mensagens, key=lambda m: m.enviada_em, reverse=True)
