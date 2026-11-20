"""Manipuladores de acesso: entrar, criar conta, sair, trocar a própria senha, usuários e permissões (Specs 002, 017 e 019). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

import secrets
from typing import Dict, Optional

from remindme.aplicacao.acesso import SessaoInvalida
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_entrada as pe
from remindme.apresentacao.web import paginas_usuarios as pu
from remindme.apresentacao.web.requisicao import (
    AVISOS,
    COOKIE_ENTRADA,
    COOKIE_SESSAO,
    Requisicao,
    Resposta,
    _aviso,
    _confere,
    _erros,
    _perfil,
    _valores,
    _volta,
)
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao


class RotasAcesso:
    """Rotas de acesso e administração de usuários; usa os serviços e os auxiliares de `AplicacaoWeb`."""

    def _entrar_pagina(self, req: Requisicao, erro: str = "", email: str = "", status: int = 200) -> Resposta:
        """UC-01, A1: com sessão ativa, segue direto para o painel."""
        if not erro:
            try:
                self._s.acesso.sessao_ativa(req.cookies.get(COOKIE_SESSAO))
                return Resposta.redirecionar("/painel")
            except SessaoInvalida:
                pass
        protecao = req.cookies.get(COOKIE_ENTRADA) or secrets.token_urlsafe(24)
        aviso = AVISOS.get(req.consulta.get("aviso", ""), ("", ""))[1]
        volta = _volta(req.formulario.get("volta") or req.consulta.get("volta", ""))
        pagina = pe.pagina_entrar(protecao, email=email, erro=erro, aviso="" if erro else aviso, volta=volta)
        return Resposta.pagina(pagina, status).cookie(COOKIE_ENTRADA, protecao, req.https)

    def _entrar(self, req: Requisicao) -> Resposta:
        """RF-65, RF-66. O formulário de entrada também tem proteção, guardada em cookie próprio."""
        if not _confere(req.formulario.get("protecao", ""), req.cookies.get(COOKIE_ENTRADA, "")):
            return self._entrar_pagina(req, "A página de entrada expirou. Tente de novo.", req.campo("email"), 400)
        try:
            aberta = self._s.acesso.entrar(req.campo("email"), req.formulario.get("senha", ""))
        except OperacaoRecusada as recusa:
            return self._entrar_pagina(req, recusa.motivo, req.campo("email"), 401)
        destino = _volta(req.formulario.get("volta", "")) or "/painel"
        resposta = Resposta.redirecionar(destino).cookie(COOKIE_SESSAO, aberta.identificador, req.https)
        return resposta.cookie(COOKIE_ENTRADA, "", req.https, apagar=True)

    def _criar_conta_pagina(
        self, req: Requisicao, valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
        criada: bool = False,
    ) -> Resposta:
        """OPEN-55. Usa a mesma proteção de formulário da entrada."""
        protecao = req.cookies.get(COOKIE_ENTRADA) or secrets.token_urlsafe(24)
        pagina = pe.pagina_criar_conta(protecao, valores or {}, erros or {}, criada)
        return Resposta.pagina(pagina, 400 if erros else 200).cookie(COOKIE_ENTRADA, protecao, req.https)

    def _criar_conta(self, req: Requisicao) -> Resposta:
        valores = _valores(req, "nome", "email", "perfil")
        if not _confere(req.formulario.get("protecao", ""), req.cookies.get(COOKIE_ENTRADA, "")):
            return self._criar_conta_pagina(req, valores, {"_": "A página expirou. Tente de novo."})
        try:
            self._s.acesso.criar_conta(valores["nome"], valores["email"], _perfil(valores["perfil"]), req.formulario.get("senha", ""))
        except OperacaoRecusada as recusa:
            return self._criar_conta_pagina(req, valores, _erros(recusa))
        return self._criar_conta_pagina(req, valores, criada=True)

    def _sair(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.sair(sessao)
        return Resposta.redirecionar("/entrar?aviso=saiu").cookie(COOKIE_SESSAO, "", req.https, apagar=True)

    def _trocar_senha_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto, erros: Optional[Dict[str, str]] = None) -> Resposta:
        return Resposta.pagina(pu.pagina_trocar_senha(ctx, erros or {}), 400 if erros else 200)

    def _trocar_senha(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        """RF-95: lê as senhas como digitadas (sem aparar) e nunca as devolve à página."""
        senhas = [req.formulario.get(nome, "") for nome in ("senha_atual", "nova_senha", "confirmacao")]
        try:
            self._s.acesso.trocar_senha(sessao, *senhas)
        except SessaoInvalida:
            raise
        except OperacaoRecusada as recusa:
            return self._trocar_senha_pagina(req, sessao, ctx, _erros(recusa))
        return Resposta.redirecionar("/painel?aviso=senha")

    def _usuarios(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        return Resposta.pagina(pu.pagina_usuarios(ctx, self._s.acesso.listar_usuarios(sessao), _aviso(req)))

    def _usuario_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.ADMINISTRAR_USUARIOS)
        return Resposta.pagina(pu.pagina_usuario_formulario(ctx, {}, {}))

    def _usuario_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "email", "perfil")
        senha = req.formulario.get("senha", "")
        try:
            usuario = self._s.acesso.cadastrar_usuario(sessao, valores["nome"], valores["email"], _perfil(valores["perfil"]), senha)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(pu.pagina_usuario_formulario(ctx, valores, _erros(recusa)), 400)
        return Resposta.redirecionar(f"/usuarios/{usuario.id}?aviso=usuario")

    def _usuario(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, usuario_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        usuario = self._s.acesso.obter_usuario(sessao, usuario_id)
        pagina = pu.pagina_usuario(ctx, usuario, valores or {}, erros or {}, None if erros else _aviso(req))
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _usuario_perfil(self, req: Requisicao, sessao: str, ctx: p.Contexto, usuario_id: str) -> Resposta:
        valores = _valores(req, "perfil")
        try:
            self._s.acesso.alterar_perfil(sessao, usuario_id, _perfil(valores["perfil"]))
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._usuario(req, sessao, ctx, usuario_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/usuarios/{usuario_id}?aviso=perfil")

    def _usuario_inativacao(self, req: Requisicao, sessao: str, ctx: p.Contexto, usuario_id: str) -> Resposta:
        try:
            self._s.acesso.inativar_usuario(sessao, usuario_id)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._usuario(req, sessao, ctx, usuario_id, {}, _erros(recusa))
        return Resposta.redirecionar(f"/usuarios/{usuario_id}?aviso=inativacao")

    def _usuario_ativacao(self, req: Requisicao, sessao: str, ctx: p.Contexto, usuario_id: str) -> Resposta:
        try:
            self._s.acesso.ativar_usuario(sessao, usuario_id)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._usuario(req, sessao, ctx, usuario_id, {}, _erros(recusa))
        return Resposta.redirecionar(f"/usuarios/{usuario_id}?aviso=ativacao")

    def _permissoes(self, req: Requisicao, sessao: str, ctx: p.Contexto, aviso=None, status: int = 200) -> Resposta:
        pagina = pu.pagina_permissoes(ctx, self._s.acesso.matriz(sessao), aviso or _aviso(req))
        return Resposta.pagina(pagina, status)

    def _permissao(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        perfil = _perfil(req.campo("perfil"))
        operacao = Operacao[req.campo("operacao")] if req.campo("operacao") in Operacao.__members__ else None
        alterar = self._s.acesso.conceder_permissao if req.campo("acao") == "conceder" else self._s.acesso.retirar_permissao
        try:
            alterar(sessao, perfil, operacao)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._permissoes(req, sessao, ctx, ("erro", recusa.motivo), 400)
        return Resposta.redirecionar("/permissoes?aviso=permissao")
