"""Ponto único de gravação da auditoria (Spec 001; ADR-004, decisão 3; INV-5) e registro de erro no log."""

import logging
from typing import Optional

from remindme.aplicacao.portas import RegistroErro, Relogio, UnidadeDeTrabalho
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.usuario import Usuario


class RegistroErrosNoLog:
    """Registro de erro no log da aplicação (RNF-21, verificado por inspeção de log)."""

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

    @property
    def usuario(self) -> Optional[Usuario]:
        """Quem executa a operação; vazio quando ela é automática."""
        return self._usuario

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
