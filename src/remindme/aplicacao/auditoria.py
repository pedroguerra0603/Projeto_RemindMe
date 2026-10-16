"""Spec 001: execução de operações com auditoria na mesma transação e registro de erro não tratado.

INV-5 e ADR-004, decisão 3: este módulo é o único ponto da aplicação que grava registro de auditoria.
"""

import uuid
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Usuario

T = TypeVar("T")


@dataclass(frozen=True)
class Alteracao:
    """Um campo alterado de um registro afetado (RF-05). A5: um registro de auditoria por registro afetado.

    Sem `operacao`, vale a operação solicitada. Em criação (A1), `valor_anterior` fica vazio.
    """

    registro_afetado: str
    campo: str
    valor_anterior: Optional[str]
    valor_novo: Optional[str]
    motivo: Optional[str] = None
    operacao: Optional[str] = None


Auditar = Callable[[Alteracao], None]


class OperacaoAuditada:
    def __init__(
        self, uow: UnidadeDeTrabalho, relogio: Relogio, erros: Optional[RegistroErros] = None
    ):
        self._uow = uow
        self._relogio = relogio
        self._erros = erros

    def executar(
        self,
        usuario: Optional[Usuario],
        operacao: str,
        acao: Callable[[UnidadeDeTrabalho, Auditar], T],
        rotina: Optional[str] = None,
    ) -> T:
        """Executa `acao` em uma transação. `acao` recebe a unidade de trabalho e a função `auditar`.

        Sem usuário, a operação é automática e informa a rotina (A4, OPEN-30).
        E1: recusa desfaz a transação, inclusive a auditoria, e não é erro não tratado.
        E2, E3: qualquer falha desfaz operação e auditoria juntas (RNF-09).
        E5: erro não tratado é registrado com identificador de correlação e chega a quem chamou (RNF-21).
        """
        try:
            with self._uow as uow:
                data_hora = self._relogio.agora()

                def auditar(alteracao: Alteracao) -> None:
                    uow.auditoria.registrar(
                        RegistroAuditoria(
                            usuario_id=usuario.id if usuario is not None else None,
                            data_hora=data_hora,
                            operacao=alteracao.operacao or operacao,
                            registro_afetado=alteracao.registro_afetado,
                            campo=alteracao.campo,
                            valor_anterior=alteracao.valor_anterior,
                            valor_novo=alteracao.valor_novo,
                            motivo=alteracao.motivo,
                            automatica=usuario is None,
                            rotina=rotina if usuario is None else None,
                        )
                    )

                return acao(uow, auditar)
        except OperacaoRecusada:
            raise
        except Exception as erro:
            self._registrar_erro(usuario, operacao, erro)
            raise

    def _registrar_erro(self, usuario: Optional[Usuario], operacao: str, erro: Exception) -> None:
        if self._erros is None:
            return
        correlacao = uuid.uuid4().hex
        try:
            self._erros.registrar(
                RegistroErro(
                    data_hora=self._relogio.agora(),
                    operacao=operacao,
                    usuario_id=usuario.id if usuario is not None else None,
                    correlacao=correlacao,
                    erro=f"{type(erro).__name__}: {erro}",
                )
            )
        except Exception as falha:
            # O erro original continua sendo o que chega a quem chamou.
            erro.add_note(f"Falha ao registrar o erro (correlação {correlacao}): {falha!r}")
            return
        erro.add_note(f"Identificador de correlação: {correlacao}")
