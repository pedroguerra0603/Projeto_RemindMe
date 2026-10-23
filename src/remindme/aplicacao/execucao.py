"""Ponto único por onde passa toda operação da camada de aplicação: transação, autorização e erro não tratado.

A gravação da auditoria fica em `auditoria.OperacaoAuditada` (Spec 001, INV-5); a verificação de acesso, em
`acesso.Autorizacao` (Spec 002, INV-5).
"""

import uuid
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada
from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Usuario


class Execucao:
    def __init__(
        self, uow: UnidadeDeTrabalho, relogio: Relogio, erros: RegistroErros, autorizacao: Autorizacao
    ):
        self._uow = uow
        self._relogio = relogio
        self._erros = erros
        self._autorizacao = autorizacao

    @contextmanager
    def operacao(
        self, nome: str, sessao: Optional[str], permissao: Operacao
    ) -> Iterator[OperacaoAuditada]:
        """Operação de um usuário: exige sessão válida e a permissão do perfil (Spec 002, INV-2)."""
        with self._executar(nome, lambda uow: self._autorizacao.exigir(uow, sessao, permissao)) as op:
            yield op

    @contextmanager
    def do_usuario(
        self, nome: str, identificar: Callable[[UnidadeDeTrabalho], Usuario]
    ) -> Iterator[OperacaoAuditada]:
        """Operação em que o próprio usuário se identifica, como entrar e sair do sistema (OPEN-47)."""
        with self._executar(nome, identificar) as op:
            yield op

    @contextmanager
    def automatica(self, nome: str, rotina: str) -> Iterator[OperacaoAuditada]:
        """Operação disparada pelo sistema, sem usuário (Spec 001, A4; OPEN-30)."""
        if not rotina:
            raise ValueError("Operação automática exige o nome da rotina.")
        with self._executar(nome, None, rotina) as op:
            yield op

    @contextmanager
    def _executar(
        self,
        nome: str,
        identificar: Optional[Callable[[UnidadeDeTrabalho], Usuario]],
        rotina: Optional[str] = None,
    ) -> Iterator[OperacaoAuditada]:
        """Recusa por regra de negócio ou por acesso desfaz a transação e não deixa registro (Spec 001, E1).
        Qualquer outro erro desfaz a transação, gera um registro de erro e chega a quem chamou (E2, E3, E5)."""
        usuario: Optional[Usuario] = None
        try:
            with self._uow as uow:
                if identificar is not None:
                    usuario = identificar(uow)
                yield OperacaoAuditada(uow, self._relogio, nome, usuario, rotina)
        except OperacaoRecusada:
            raise
        except Exception as erro:
            correlacao = uuid.uuid4().hex
            self._erros.registrar(
                RegistroErro(
                    data_hora=self._relogio.agora(),
                    operacao=nome,
                    usuario_id=usuario.id if usuario else None,
                    correlacao=correlacao,
                    erro=f"{type(erro).__name__}: {erro}",
                )
            )
            erro.add_note(f"Identificador de correlação: {correlacao}")
            raise
