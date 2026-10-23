"""Ponto único de gravação da auditoria e do registro de erro (Spec 001; ADR-004, decisão 3; INV-5)."""

import logging
import uuid
from contextlib import contextmanager
from typing import Iterator, Optional

from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Usuario


class RegistroErrosNoLog:
    """Registro de erro padrão, no log da aplicação, até a escolha do armazenamento (OPEN-02)."""

    def registrar(self, registro: RegistroErro) -> None:
        logging.getLogger("remindme").error(
            "Erro não tratado em %s (usuário %s, correlação %s): %s",
            registro.operacao,
            registro.usuario_id,
            registro.correlacao,
            registro.erro,
        )


class OperacaoAuditada:
    """Uma operação em andamento, dentro da transação. Grava a auditoria na mesma transação (INV-2)."""

    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        nome: str,
        usuario: Optional[Usuario],
        rotina: Optional[str],
    ):
        self.uow = uow
        self._relogio = relogio
        self._nome = nome
        self._usuario = usuario
        self._rotina = rotina

    def registrar(
        self,
        registro_afetado: str,
        campo: str,
        valor_anterior: Optional[str],
        valor_novo: Optional[str],
        motivo: Optional[str] = None,
        operacao: Optional[str] = None,
    ) -> None:
        """Um registro por registro afetado e campo alterado (A5; RF-05)."""
        self.uow.auditoria.registrar(
            RegistroAuditoria(
                usuario_id=self._usuario.id if self._usuario else None,
                data_hora=self._relogio.agora(),
                operacao=operacao or self._nome,
                registro_afetado=registro_afetado,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                motivo=motivo,
                campo=campo,
                automatica=self._usuario is None,
                rotina=self._rotina if self._usuario is None else None,
            )
        )


class Auditoria:
    def __init__(self, uow: UnidadeDeTrabalho, relogio: Relogio, erros: RegistroErros):
        self._uow = uow
        self._relogio = relogio
        self._erros = erros

    @contextmanager
    def operacao(
        self, nome: str, usuario: Optional[Usuario], rotina: Optional[str] = None
    ) -> Iterator[OperacaoAuditada]:
        """Abre a transação. Sem usuário, a operação é automática e exige a rotina (A4).

        Recusa por regra de negócio desfaz a transação e não deixa registro (E1). Qualquer outro erro
        desfaz a transação, gera um registro de erro e chega a quem chamou (E2, E3, E5).
        """
        if usuario is None and not rotina:
            raise ValueError("Operação sem usuário exige o nome da rotina.")
        try:
            with self._uow as uow:
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
