"""Sessão e autorização (Spec 002). A verificação de acesso fica neste único ponto (INV-5, DT-06)."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from remindme.aplicacao.portas import Relogio, Sessao, UnidadeDeTrabalho
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Usuario

# OPEN-43, decidida em 2026-10-23: a sessão vale 8 horas a partir da entrada.
DURACAO_DA_SESSAO = timedelta(hours=8)


class SessaoInvalida(OperacaoRecusada):
    """RNF-01, E3: sem sessão, com sessão desconhecida, vencida ou de usuário inativo."""

    def __init__(self, motivo: str = "Sessão inválida ou encerrada. Entre novamente."):
        super().__init__(motivo)


def chave_da_sessao(identificador: str) -> str:
    return hashlib.sha256(identificador.encode("utf-8")).hexdigest()


def nova_sessao(usuario_id: str, agora: datetime) -> Tuple[str, Sessao]:
    """Devolve o identificador, que só o navegador guarda, e a sessão a armazenar."""
    identificador = secrets.token_urlsafe(32)
    sessao = Sessao(
        chave=chave_da_sessao(identificador),
        usuario_id=usuario_id,
        aberta_em=agora,
        expira_em=agora + DURACAO_DA_SESSAO,
        protecao=secrets.token_urlsafe(32),
    )
    return identificador, sessao


class Autorizacao:
    def __init__(self, relogio: Relogio):
        self._relogio = relogio

    def sessao(self, uow: UnidadeDeTrabalho, identificador: Optional[str]) -> Tuple[Sessao, Usuario]:
        """A sessão vale se existe, não venceu e é de usuário ativo (RNF-01, A3)."""
        if not isinstance(identificador, str) or not identificador:
            raise SessaoInvalida("É preciso entrar no sistema para continuar.")
        sessao = uow.sessoes.obter(chave_da_sessao(identificador))
        if sessao is None or self._relogio.agora() >= sessao.expira_em:
            raise SessaoInvalida()
        usuario = uow.usuarios.obter(sessao.usuario_id)
        if usuario is None or not usuario.ativo:
            raise SessaoInvalida("Usuário inativo. Procure o Administrador.")
        return sessao, usuario

    def exigir(self, uow: UnidadeDeTrabalho, identificador: Optional[str], operacao: Operacao) -> Usuario:
        """INV-2: sessão válida de usuário ativo e permissão explícita do perfil atual (RNF-02, RF-03, A2)."""
        _, usuario = self.sessao(uow, identificador)
        uow.permissoes.obter().exigir(usuario.perfil, operacao)
        return usuario
