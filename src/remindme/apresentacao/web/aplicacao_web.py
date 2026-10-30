"""Aplicação WSGI da interface web (Spec 017, ADR-006).

A apresentação recebe a requisição, confere a sessão e a proteção do formulário, chama os serviços da
aplicação e devolve a página. Permissões e regras ficam nos serviços e no domínio (INV-1, DT-06).
"""

import hmac
import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode

from remindme.aplicacao.acesso import SessaoInvalida
from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_auditoria import FiltroAuditoria, ServicoAuditoria
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_empresa import ServicoEmpresa
from remindme.aplicacao.servico_orcamentos import FiltroOrcamentos, ServicoOrcamentos
from remindme.aplicacao.servico_titulos import ANTECEDENCIA_PADRAO_DIAS, FiltroTitulos, ServicoTitulos
from remindme.aplicacao.tempo import data_local
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web.html import Html
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.empresa import CAMPOS as CAMPOS_DA_EMPRESA
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil

COOKIE_SESSAO = "remindme_sessao"
COOKIE_ENTRADA = "remindme_entrada"
LIMITE_DO_CORPO = 64 * 1024
ESTATICO = Path(__file__).resolve().parent.joinpath("estatico")
ARQUIVOS_ESTATICOS = {
    "estilo.css": "text/css; charset=utf-8",
    "icone.svg": "image/svg+xml",
    "tema.js": "text/javascript; charset=utf-8",
    "plex-sans-400.woff2": "font/woff2",
    "plex-sans-600.woff2": "font/woff2",
}
ID = "[0-9a-f]{32}"

POLITICA_DE_CONTEUDO = (
    "default-src 'none'; style-src 'self'; img-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; "
    "frame-ancestors 'none'; base-uri 'none'"
)

AVISOS = {
    "saiu": ("info", "Você saiu do sistema."),
    "cliente": ("sucesso", "Cliente cadastrado."),
    "cliente-alterado": ("sucesso", "Dados do cliente atualizados."),
    "titulo": ("sucesso", "Título cadastrado em Aberto."),
    "pagamento": ("sucesso", "Pagamento registrado."),
    "estorno": ("sucesso", "Pagamento estornado."),
    "cancelamento": ("sucesso", "Título cancelado."),
    "usuario": ("sucesso", "Usuário cadastrado. Informe a senha provisória a ele."),
    "perfil": ("sucesso", "Perfil alterado. Vale na próxima operação do usuário."),
    "inativacao": ("sucesso", "Usuário inativado. As sessões dele foram encerradas."),
    "permissao": ("sucesso", "Permissão atualizada. Vale na próxima operação dos usuários do perfil."),
    "orcamento": ("sucesso", "Orçamento criado em Rascunho. Inclua os itens."),
    "item": ("sucesso", "Item incluído. Os valores foram recalculados."),
    "item-alterado": ("sucesso", "Item alterado. Os valores foram recalculados."),
    "item-removido": ("sucesso", "Item removido. Os valores foram recalculados."),
    "desconto": ("sucesso", "Desconto aplicado. Os valores foram recalculados."),
    "desconto-pendente": ("info", "O desconto passa da sua alçada: o orçamento aguarda a decisão do Dono."),
    "condicao": ("sucesso", "Condição de pagamento atualizada."),
    "decisao": ("sucesso", "Decisão registrada. O orçamento voltou a Rascunho."),
    "orcamento-cancelado": ("sucesso", "Orçamento cancelado."),
    "empresa": ("sucesso", "Dados da empresa salvos."),
    "ativacao": ("sucesso", "Usuário ativado. Ele já pode entrar."),
}

_CORRELACAO = re.compile(r"Identificador de correlação: ([0-9a-f]+)")


@dataclass
class Servicos:
    acesso: ServicoAcesso
    clientes: ServicoClientes
    titulos: ServicoTitulos
    auditoria: ServicoAuditoria
    orcamentos: Optional[ServicoOrcamentos] = None
    empresa: Optional[ServicoEmpresa] = None


class CorpoGrandeDemais(Exception):
    pass


class Requisicao:
    def __init__(self, ambiente: dict):
        self.metodo = ambiente.get("REQUEST_METHOD", "GET").upper()
        self.caminho = ambiente.get("PATH_INFO", "") or "/"
        self.consulta = _primeiros(parse_qs(ambiente.get("QUERY_STRING", ""), keep_blank_values=True))
        self.https = ambiente.get("wsgi.url_scheme") == "https"
        try:
            self.cookies = {nome: m.value for nome, m in SimpleCookie(ambiente.get("HTTP_COOKIE", "")).items()}
        except CookieError:
            self.cookies = {}
        self.formulario: Dict[str, str] = {}
        if self.metodo == "POST":
            try:
                tamanho = int(ambiente.get("CONTENT_LENGTH") or 0)
            except ValueError:
                tamanho = 0
            if tamanho > LIMITE_DO_CORPO:
                raise CorpoGrandeDemais()
            corpo = ambiente["wsgi.input"].read(tamanho) if tamanho > 0 else b""
            if ambiente.get("CONTENT_TYPE", "").startswith("application/x-www-form-urlencoded"):
                texto = corpo.decode("utf-8", errors="replace")
                self.formulario = _primeiros(parse_qs(texto, keep_blank_values=True))

    def campo(self, nome: str) -> str:
        return self.formulario.get(nome, "").strip()


class Resposta:
    def __init__(self, status: int = 200, corpo: bytes = b"", tipo: str = "text/html; charset=utf-8"):
        self.status = status
        self.corpo = corpo
        self.cabecalhos: List[Tuple[str, str]] = [("Content-Type", tipo)]
        self.cache = "no-store"

    @classmethod
    def pagina(cls, html: Html, status: int = 200) -> "Resposta":
        return cls(status, html.encode("utf-8"))

    @classmethod
    def redirecionar(cls, destino: str) -> "Resposta":
        resposta = cls(303)
        resposta.cabecalhos.append(("Location", destino))
        return resposta

    def cookie(self, nome: str, conteudo: str, https: bool, apagar: bool = False) -> "Resposta":
        partes = [f"{nome}={'' if apagar else conteudo}", "Path=/", "HttpOnly", "SameSite=Lax"]
        if apagar:
            partes.append("Max-Age=0")
        if https:
            partes.append("Secure")
        self.cabecalhos.append(("Set-Cookie", "; ".join(partes)))
        return self


Manipulador = Callable[..., Resposta]


class AplicacaoWeb:
    def __init__(self, servicos: Servicos, relogio: Relogio, erros: RegistroErros):
        self._s = servicos
        self._relogio = relogio
        self._erros = erros
        r = self._rotas = []
        publica, protegida = False, True
        r.append(("GET", "/", self._inicio, publica))
        r.append(("GET", "/favicon.ico", self._favicon, publica))
        r.append(("GET", "/estatico/(?P<nome>[a-z0-9.-]+)", self._estatico, publica))
        r.append(("GET", "/entrar", self._entrar_pagina, publica))
        r.append(("POST", "/entrar", self._entrar, publica))
        r.append(("GET", "/criar-conta", self._criar_conta_pagina, publica))
        r.append(("POST", "/criar-conta", self._criar_conta, publica))
        r.append(("GET", "/robots.txt", self._robots, publica))
        r.append(("POST", "/sair", self._sair, protegida))
        r.append(("GET", "/painel", self._painel, protegida))
        r.append(("GET", "/clientes", self._clientes, protegida))
        r.append(("GET", "/clientes/novo", self._cliente_novo_pagina, protegida))
        r.append(("POST", "/clientes/novo", self._cliente_novo, protegida))
        r.append(("GET", f"/clientes/(?P<cliente_id>{ID})", self._cliente, protegida))
        r.append(("GET", f"/clientes/(?P<cliente_id>{ID})/editar", self._cliente_editar_pagina, protegida))
        r.append(("POST", f"/clientes/(?P<cliente_id>{ID})/editar", self._cliente_editar, protegida))
        r.append(("GET", "/titulos", self._titulos, protegida))
        r.append(("GET", "/titulos/novo", self._titulo_novo_pagina, protegida))
        r.append(("POST", "/titulos/novo", self._titulo_novo, protegida))
        r.append(("POST", "/titulos/verificar-vencimentos", self._verificar_vencimentos, protegida))
        r.append(("GET", f"/titulos/(?P<titulo_id>{ID})", self._titulo, protegida))
        r.append(("POST", f"/titulos/(?P<titulo_id>{ID})/pagamentos", self._pagamento, protegida))
        r.append(("GET", f"/titulos/(?P<titulo_id>{ID})/pagamentos/(?P<pagamento_id>{ID})/estorno", self._estorno_pagina, protegida))
        r.append(("POST", f"/titulos/(?P<titulo_id>{ID})/pagamentos/(?P<pagamento_id>{ID})/estorno", self._estorno, protegida))
        r.append(("GET", f"/titulos/(?P<titulo_id>{ID})/cancelamento", self._cancelamento_pagina, protegida))
        r.append(("POST", f"/titulos/(?P<titulo_id>{ID})/cancelamento", self._cancelamento, protegida))
        r.append(("GET", "/orcamentos", self._orcamentos, protegida))
        r.append(("GET", "/orcamentos/novo", self._orcamento_novo_pagina, protegida))
        r.append(("POST", "/orcamentos/novo", self._orcamento_novo, protegida))
        r.append(("GET", f"/orcamentos/(?P<orcamento_id>{ID})", self._orcamento, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/itens", self._item_novo, protegida))
        r.append(("GET", f"/orcamentos/(?P<orcamento_id>{ID})/itens/(?P<item_id>{ID})", self._item_pagina, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/itens/(?P<item_id>{ID})", self._item_alterar, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/itens/(?P<item_id>{ID})/remocao", self._item_remover, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/desconto", self._desconto, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/condicao", self._condicao, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/decisao", self._decisao, protegida))
        r.append(("GET", f"/orcamentos/(?P<orcamento_id>{ID})/cancelamento", self._orcamento_cancelamento_pagina, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/cancelamento", self._orcamento_cancelamento, protegida))
        r.append(("GET", "/empresa", self._empresa, protegida))
        r.append(("POST", "/empresa", self._empresa_salvar, protegida))
        r.append(("GET", "/auditoria", self._auditoria, protegida))
        r.append(("GET", "/usuarios", self._usuarios, protegida))
        r.append(("GET", "/usuarios/novo", self._usuario_novo_pagina, protegida))
        r.append(("POST", "/usuarios/novo", self._usuario_novo, protegida))
        r.append(("GET", f"/usuarios/(?P<usuario_id>{ID})", self._usuario, protegida))
        r.append(("POST", f"/usuarios/(?P<usuario_id>{ID})/perfil", self._usuario_perfil, protegida))
        r.append(("POST", f"/usuarios/(?P<usuario_id>{ID})/inativacao", self._usuario_inativacao, protegida))
        r.append(("POST", f"/usuarios/(?P<usuario_id>{ID})/ativacao", self._usuario_ativacao, protegida))
        r.append(("GET", "/permissoes", self._permissoes, protegida))
        r.append(("POST", "/permissoes", self._permissao, protegida))
        self._rotas = [(metodo, re.compile(padrao), funcao, privada) for metodo, padrao, funcao, privada in r]

    # WSGI

    def __call__(self, ambiente: dict, start_response):
        https = ambiente.get("wsgi.url_scheme") == "https"
        try:
            requisicao = Requisicao(ambiente)
            resposta = self._despachar(requisicao)
        except CorpoGrandeDemais:
            resposta = self._erro(413, "Envio grande demais", "O formulário enviado passa do tamanho aceito.")
        except Exception as erro:
            resposta = self._erro_inesperado(ambiente, erro)
        cabecalhos = list(resposta.cabecalhos) + [
            ("Content-Length", str(len(resposta.corpo))),
            ("Cache-Control", resposta.cache),
            ("Content-Security-Policy", POLITICA_DE_CONTEUDO),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "same-origin"),
            ("Cross-Origin-Opener-Policy", "same-origin"),
        ]
        if https:
            cabecalhos.append(("Strict-Transport-Security", "max-age=31536000"))
        start_response(f"{resposta.status} {HTTPStatus(resposta.status).phrase}", cabecalhos)
        return [resposta.corpo]

    def _despachar(self, req: Requisicao) -> Resposta:
        caminho_existe = False
        for metodo, padrao, funcao, privada in self._rotas:
            casamento = padrao.fullmatch(req.caminho)
            if not casamento:
                continue
            caminho_existe = True
            if metodo != req.metodo:
                continue
            if not privada:
                return funcao(req, **casamento.groupdict())
            return self._protegida(req, funcao, casamento.groupdict())
        if caminho_existe:
            return self._erro(405, "Método não permitido", "Esta página não aceita esse tipo de envio.")
        return self._erro(404, "Página não encontrada", "O endereço não existe no RemindMe.")

    def _protegida(self, req: Requisicao, funcao: Manipulador, parametros: Dict[str, str]) -> Resposta:
        """RNF-01: sem sessão válida, volta à entrada. INV-3: todo envio confere a proteção da sessão."""
        sessao = req.cookies.get(COOKIE_SESSAO)
        try:
            ativa = self._s.acesso.sessao_ativa(sessao)
        except SessaoInvalida:
            return Resposta.redirecionar("/entrar").cookie(COOKIE_SESSAO, "", req.https, apagar=True)
        if req.metodo == "POST" and not _confere(req.formulario.get("protecao", ""), ativa.protecao):
            return self._erro(
                403,
                "Formulário recusado",
                "Este formulário expirou ou não veio do RemindMe. Volte, recarregue a página e tente de novo.",
            )
        ctx = p.Contexto(ativa.usuario, ativa.operacoes, ativa.protecao, data_local(self._relogio.agora()))
        try:
            return funcao(req, sessao, ctx, **parametros)
        except SessaoInvalida:
            return Resposta.redirecionar("/entrar").cookie(COOKIE_SESSAO, "", req.https, apagar=True)
        except OperacaoNegada as negada:
            return self._erro(403, "Acesso negado", negada.motivo)
        except OperacaoRecusada as recusa:
            return self._erro(400, "Operação recusada", recusa.motivo)

    # Entrada

    def _inicio(self, req: Requisicao) -> Resposta:
        return Resposta.redirecionar("/painel")

    def _favicon(self, req: Requisicao) -> Resposta:
        resposta = Resposta(301)
        resposta.cabecalhos.append(("Location", "/estatico/icone.svg"))
        return resposta

    def _estatico(self, req: Requisicao, nome: str) -> Resposta:
        if nome not in ARQUIVOS_ESTATICOS:
            return self._erro(404, "Página não encontrada", "O arquivo não existe.")
        resposta = Resposta(200, ESTATICO.joinpath(nome).read_bytes(), ARQUIVOS_ESTATICOS[nome])
        resposta.cache = "public, max-age=3600"
        return resposta

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
        pagina = p.pagina_entrar(protecao, email=email, erro=erro, aviso="" if erro else aviso)
        return Resposta.pagina(pagina, status).cookie(COOKIE_ENTRADA, protecao, req.https)

    def _entrar(self, req: Requisicao) -> Resposta:
        """RF-65, RF-66. O formulário de entrada também tem proteção, guardada em cookie próprio."""
        if not _confere(req.formulario.get("protecao", ""), req.cookies.get(COOKIE_ENTRADA, "")):
            return self._entrar_pagina(req, "A página de entrada expirou. Tente de novo.", req.campo("email"), 400)
        try:
            aberta = self._s.acesso.entrar(req.campo("email"), req.formulario.get("senha", ""))
        except OperacaoRecusada as recusa:
            return self._entrar_pagina(req, recusa.motivo, req.campo("email"), 401)
        resposta = Resposta.redirecionar("/painel").cookie(COOKIE_SESSAO, aberta.identificador, req.https)
        return resposta.cookie(COOKIE_ENTRADA, "", req.https, apagar=True)

    def _criar_conta_pagina(
        self, req: Requisicao, valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
        criada: bool = False,
    ) -> Resposta:
        """OPEN-55. Usa a mesma proteção de formulário da entrada."""
        protecao = req.cookies.get(COOKIE_ENTRADA) or secrets.token_urlsafe(24)
        pagina = p.pagina_criar_conta(protecao, valores or {}, erros or {}, criada)
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

    def _robots(self, req: Requisicao) -> Resposta:
        """SEO: só a entrada e a criação de conta são públicas; o resto exige sessão."""
        texto = "User-agent: *\nAllow: /entrar\nAllow: /criar-conta\nDisallow: /\n"
        return Resposta(200, texto.encode("utf-8"), "text/plain; charset=utf-8")

    def _sair(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.sair(sessao)
        return Resposta.redirecionar("/entrar?aviso=saiu").cookie(COOKIE_SESSAO, "", req.https, apagar=True)

    # Painel

    def _painel(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        visoes = (
            self._s.titulos.consultar_titulos(sessao, FiltroTitulos(), ctx.hoje)
            if ctx.pode(Operacao.CONSULTAR_TITULOS)
            else None
        )
        registros = (
            self._s.auditoria.consultar(sessao, FiltroAuditoria()) if ctx.pode(Operacao.CONSULTAR_AUDITORIA) else None
        )
        usuarios = self._s.acesso.listar_usuarios(sessao) if ctx.pode(Operacao.ADMINISTRAR_USUARIOS) else None
        pendentes = (
            self._s.orcamentos.pendentes_de_decisao(sessao)
            if self._s.orcamentos and ctx.pode(Operacao.APROVAR_DESCONTO)
            else None
        )
        # Dados só dos gráficos (o resto o painel já busca acima).
        pagamentos = self._s.titulos.pagamentos_recebidos(sessao) if ctx.usuario.perfil is Perfil.DONO else None
        orcamentos = (
            self._s.orcamentos.consultar_orcamentos(sessao)
            if self._s.orcamentos and ctx.usuario.perfil is Perfil.OPERADOR_FINANCEIRO
            else None
        )
        pagina = p.pagina_painel(
            ctx, visoes, self._nomes_clientes(sessao, ctx), registros, usuarios, _aviso(req), pendentes, pagamentos, orcamentos
        )
        return Resposta.pagina(pagina)

    # Clientes (Spec 003)

    def _clientes(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        termo = req.consulta.get("q", "").strip()
        clientes = self._s.clientes.consultar_clientes(sessao, termo)
        return Resposta.pagina(p.pagina_clientes(ctx, clientes, termo, _aviso(req)))

    def _cliente_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_CLIENTES)
        return Resposta.pagina(p.pagina_cliente_formulario(ctx, {}, {}))

    def _cliente_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            cliente = self._s.clientes.cadastrar_cliente(sessao, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(p.pagina_cliente_formulario(ctx, valores, _erros(recusa)), 400)
        return Resposta.redirecionar(f"/clientes/{cliente.id}?aviso=cliente")

    def _cliente(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        cliente = self._s.clientes.obter_cliente(sessao, cliente_id)
        visoes = (
            self._s.titulos.consultar_titulos(sessao, FiltroTitulos(cliente_id=cliente.id), ctx.hoje)
            if ctx.pode(Operacao.CONSULTAR_TITULOS)
            else []
        )
        historico = self._historico(sessao, ctx, f"cliente {cliente.id}")
        return Resposta.pagina(p.pagina_cliente(ctx, cliente, visoes, historico, _aviso(req)))

    def _cliente_editar_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_CLIENTES)
        cliente = self._s.clientes.obter_cliente(sessao, cliente_id)
        valores = {"nome": cliente.nome, "documento": f.documento(cliente.documento), "contato": f.contato(cliente.contato)}
        return Resposta.pagina(p.pagina_cliente_formulario(ctx, valores, {}, cliente.id))

    def _cliente_editar(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            self._s.clientes.alterar_cliente(sessao, cliente_id, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(p.pagina_cliente_formulario(ctx, valores, _erros(recusa), cliente_id), 400)
        return Resposta.redirecionar(f"/clientes/{cliente_id}?aviso=cliente-alterado")

    # Títulos (Spec 006)

    def _titulos(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("cliente", "estado", "de", "ate")}
        erros: Dict[str, str] = {}
        de = _data_do_filtro(valores, "de", erros)
        ate = _data_do_filtro(valores, "ate", erros)
        estado = EstadoTitulo[valores["estado"]] if valores["estado"] in EstadoTitulo.__members__ else None
        filtro = FiltroTitulos(cliente_id=valores["cliente"] or None, estado=estado, vencimento_de=de, vencimento_ate=ate)
        visoes = self._s.titulos.consultar_titulos(sessao, filtro, ctx.hoje)
        pagina = p.pagina_titulos(ctx, visoes, self._nomes_clientes(sessao, ctx), valores, erros, _aviso(req))
        return Resposta.pagina(pagina)

    def _titulo_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CADASTRAR_TITULO)
        valores = {"cliente": req.consulta.get("cliente", "")}
        return Resposta.pagina(p.pagina_titulo_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, {}))

    def _titulo_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "cliente", "valor", "vencimento", "condicao")
        erros: Dict[str, str] = {}
        valor = _valor_do_formulario(valores, erros)
        vencimento = f.ler_data(valores["vencimento"]) if valores["vencimento"] else None
        if valores["vencimento"] and vencimento is None:
            erros["vencimento"] = "Informe uma data válida."
        if not erros:
            try:
                titulo = self._s.titulos.cadastrar_titulo(sessao, valores["cliente"], valor, vencimento, valores["condicao"])
                return Resposta.redirecionar(f"/titulos/{titulo.id}?aviso=titulo")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return Resposta.pagina(p.pagina_titulo_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, erros), 400)

    def _titulo(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None, pedido: str = "",
    ) -> Resposta:
        titulo = self._s.titulos.obter_titulo(sessao, titulo_id)
        nomes = self._nomes_clientes(sessao, ctx)
        pagina = p.pagina_titulo(
            ctx,
            titulo,
            nomes.get(titulo.cliente_id, "Cliente"),
            titulo.proximo_do_vencimento(ctx.hoje, ANTECEDENCIA_PADRAO_DIAS),
            pedido or secrets.token_urlsafe(16),
            valores if valores is not None else {"data": ctx.hoje.isoformat()},
            erros or {},
            self._historico(sessao, ctx, f"titulo {titulo.id}"),
            None if erros else _aviso(req),
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _pagamento(self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str) -> Resposta:
        """UC-06. OPEN-25: o identificador do pedido nasce com o formulário e acompanha o envio."""
        valores = _valores(req, "valor", "data", "pedido")
        erros: Dict[str, str] = {}
        valor = _valor_do_formulario(valores, erros)
        data = f.ler_data(valores["data"]) if valores["data"] else None
        if valores["data"] and data is None:
            erros["data"] = "Informe uma data válida."
        pedido = valores["pedido"] or None
        if not erros:
            try:
                self._s.titulos.registrar_pagamento(sessao, titulo_id, valor, data, pedido_id=pedido)
                return Resposta.redirecionar(f"/titulos/{titulo_id}?aviso=pagamento")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return self._titulo(req, sessao, ctx, titulo_id, valores, erros, valores["pedido"])

    def _estorno_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str, pagamento_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.ESTORNAR_PAGAMENTO)
        titulo = self._s.titulos.obter_titulo(sessao, titulo_id)
        pagamento = next((pg for pg in titulo.pagamentos if pg.id == pagamento_id), None)
        if pagamento is None:
            return self._erro(404, "Pagamento não encontrado", "O pagamento não existe neste título.")
        pagina = p.pagina_motivo(
            ctx,
            "Estornar pagamento",
            f"Pagamento de {f.moeda(pagamento.valor)} em {f.data(pagamento.data)}. O estorno restaura o saldo do título.",
            f"/titulos/{titulo_id}/pagamentos/{pagamento_id}/estorno",
            f"/titulos/{titulo_id}",
            "Estornar pagamento",
            valores or {},
            erros or {},
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _estorno(self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str, pagamento_id: str) -> Resposta:
        valores = _valores(req, "motivo")
        try:
            self._s.titulos.estornar_pagamento(sessao, titulo_id, pagamento_id, valores["motivo"], ctx.hoje)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._estorno_pagina(req, sessao, ctx, titulo_id, pagamento_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/titulos/{titulo_id}?aviso=estorno")

    def _cancelamento_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CANCELAR_TITULO)
        titulo = self._s.titulos.obter_titulo(sessao, titulo_id)
        pagina = p.pagina_motivo(
            ctx,
            "Cancelar título",
            f"Título de {f.moeda(titulo.valor)}, com vencimento em {f.data(titulo.vencimento)}. O cancelamento é definitivo.",
            f"/titulos/{titulo_id}/cancelamento",
            f"/titulos/{titulo_id}",
            "Cancelar título",
            valores or {},
            erros or {},
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _cancelamento(self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str) -> Resposta:
        valores = _valores(req, "motivo")
        try:
            self._s.titulos.cancelar_titulo(sessao, titulo_id, valores["motivo"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._cancelamento_pagina(req, sessao, ctx, titulo_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/titulos/{titulo_id}?aviso=cancelamento")

    def _verificar_vencimentos(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        vencidos = self._s.titulos.verificar_vencimentos(sessao, ctx.hoje)
        return Resposta.redirecionar("/titulos?" + urlencode({"aviso": "vencimentos", "quantidade": len(vencidos)}))

    # Orçamentos (Spec 004)

    def _orcamentos(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("cliente", "estado", "de", "ate")}
        erros: Dict[str, str] = {}
        de = _data_do_filtro(valores, "de", erros)
        ate = _data_do_filtro(valores, "ate", erros)
        estado = EstadoOrcamento[valores["estado"]] if valores["estado"] in EstadoOrcamento.__members__ else None
        filtro = FiltroOrcamentos(cliente_id=valores["cliente"] or None, estado=estado, criado_de=de, criado_ate=ate)
        orcamentos = self._s.orcamentos.consultar_orcamentos(sessao, filtro)
        pagina = p.pagina_orcamentos(ctx, orcamentos, self._nomes_clientes(sessao, ctx), valores, erros, _aviso(req))
        return Resposta.pagina(pagina)

    def _orcamento_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CONDUZIR_ORCAMENTO)
        valores = {"cliente": req.consulta.get("cliente", "")}
        return Resposta.pagina(p.pagina_orcamento_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, {}))

    def _orcamento_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "cliente", "condicao")
        try:
            orcamento = self._s.orcamentos.criar_orcamento(sessao, valores["cliente"], valores["condicao"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            pagina = p.pagina_orcamento_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, _erros(recusa))
            return Resposta.pagina(pagina, 400)
        return Resposta.redirecionar(f"/orcamentos/{orcamento.id}?aviso=orcamento")

    def _orcamento(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str,
        formulario: str = "", valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        orcamento = self._s.orcamentos.obter_orcamento(sessao, orcamento_id)
        nomes = self._nomes_clientes(sessao, ctx)
        pagina = p.pagina_orcamento(
            ctx,
            orcamento,
            nomes.get(orcamento.cliente_id, "Cliente"),
            self._nomes_usuarios(sessao, ctx),
            formulario,
            valores or {},
            erros or {},
            self._historico(sessao, ctx, f"orcamento {orcamento.id}"),
            None if erros else _aviso(req),
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _item_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        valores = _valores(req, "descricao", "quantidade", "valor_unitario")
        erros: Dict[str, str] = {}
        quantidade = _numero_do_formulario(valores, "quantidade", "Informe a quantidade, por exemplo 2 ou 1,5.", erros)
        valor = _numero_do_formulario(valores, "valor_unitario", "Informe um valor em reais, por exemplo 1.234,56.", erros)
        try:
            # Mesmo com número ilegível, o domínio confere os demais campos: a recusa mostra todos (RNF-14).
            self._s.orcamentos.incluir_item(sessao, orcamento_id, valores["descricao"], quantidade, valor)
            return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=item")
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            erros = {**_erros(recusa), **erros}
        return self._orcamento(req, sessao, ctx, orcamento_id, "item", valores, erros)

    def _item_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str, item_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CONDUZIR_ORCAMENTO)
        orcamento = self._s.orcamentos.obter_orcamento(sessao, orcamento_id)
        item = next((i for i in orcamento.itens if i.id == item_id), None)
        if item is None:
            return self._erro(404, "Item não encontrado", "O item não existe neste orçamento.")
        if valores is None:
            valores = {
                "descricao": item.descricao,
                "quantidade": f.numero_para_campo(item.quantidade),
                "valor_unitario": f.valor_para_campo(item.valor_unitario),
            }
        return Resposta.pagina(p.pagina_item_formulario(ctx, orcamento, item, valores, erros or {}), 400 if erros else 200)

    def _item_alterar(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str, item_id: str) -> Resposta:
        valores = _valores(req, "descricao", "quantidade", "valor_unitario")
        erros: Dict[str, str] = {}
        quantidade = _numero_do_formulario(valores, "quantidade", "Informe a quantidade, por exemplo 2 ou 1,5.", erros)
        valor = _numero_do_formulario(valores, "valor_unitario", "Informe um valor em reais, por exemplo 1.234,56.", erros)
        try:
            self._s.orcamentos.alterar_item(sessao, orcamento_id, item_id, valores["descricao"], quantidade, valor)
            return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=item-alterado")
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            erros = {**_erros(recusa), **erros}
        return self._item_pagina(req, sessao, ctx, orcamento_id, item_id, valores, erros)

    def _item_remover(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str, item_id: str) -> Resposta:
        try:
            self._s.orcamentos.remover_item(sessao, orcamento_id, item_id)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._orcamento(req, sessao, ctx, orcamento_id, "item", {}, _erros(recusa))
        return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=item-removido")

    def _desconto(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        valores = _valores(req, "percentual")
        erros: Dict[str, str] = {}
        percentual = _numero_do_formulario(valores, "percentual", "Informe o desconto em percentual, por exemplo 5 ou 7,5.", erros)
        if not erros:
            try:
                orcamento = self._s.orcamentos.informar_desconto(sessao, orcamento_id, percentual)
                aviso = "desconto-pendente" if orcamento.estado is EstadoOrcamento.PENDENTE_DE_ALCADA else "desconto"
                return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso={aviso}")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return self._orcamento(req, sessao, ctx, orcamento_id, "desconto", valores, erros)

    def _condicao(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        valores = _valores(req, "condicao")
        try:
            self._s.orcamentos.alterar_condicao(sessao, orcamento_id, valores["condicao"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._orcamento(req, sessao, ctx, orcamento_id, "condicao", valores, _erros(recusa))
        return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=condicao")

    def _decisao(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        valores = _valores(req, "acao", "percentual")
        erros: Dict[str, str] = {}
        percentual = None
        if valores["percentual"]:
            percentual = _numero_do_formulario(valores, "percentual", "Informe o desconto em percentual, por exemplo 5 ou 7,5.", erros)
        if not erros:
            try:
                self._s.orcamentos.decidir_desconto(sessao, orcamento_id, valores["acao"] == "aprovar", percentual)
                return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=decisao")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return self._orcamento(req, sessao, ctx, orcamento_id, "decisao", valores, erros)

    def _orcamento_cancelamento_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CONDUZIR_ORCAMENTO)
        orcamento = self._s.orcamentos.obter_orcamento(sessao, orcamento_id)
        pagina = p.pagina_motivo(
            ctx,
            "Cancelar orçamento",
            f"Orçamento de {f.moeda(orcamento.valor_liquido)}, criado em {f.data(orcamento.criado_em)}. O cancelamento é definitivo.",
            f"/orcamentos/{orcamento_id}/cancelamento",
            f"/orcamentos/{orcamento_id}",
            "Cancelar orçamento",
            valores or {},
            erros or {},
            "orcamentos",
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _orcamento_cancelamento(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        valores = _valores(req, "motivo")
        try:
            self._s.orcamentos.cancelar_orcamento(sessao, orcamento_id, valores["motivo"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._orcamento_cancelamento_pagina(req, sessao, ctx, orcamento_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=orcamento-cancelado")

    # Empresa (OPEN-54)

    def _empresa(
        self, req: Requisicao, sessao: str, ctx: p.Contexto,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        empresa = self._s.empresa.obter(sessao)
        if valores is None:
            valores = {c: getattr(empresa, c) for c in CAMPOS_DA_EMPRESA} if empresa else {}
            if empresa:
                valores["cnpj"], valores["telefone"] = f.documento(empresa.cnpj), f.contato(empresa.telefone)
        visoes = self._s.titulos.consultar_titulos(sessao, FiltroTitulos(), ctx.hoje) if ctx.pode(Operacao.CONSULTAR_TITULOS) else None
        clientes = len(self._s.clientes.consultar_clientes(sessao)) if ctx.pode(Operacao.CONSULTAR_CLIENTES) else None
        pagina = p.pagina_empresa(ctx, empresa, visoes, clientes, valores, erros or {}, None if erros else _aviso(req))
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _empresa_salvar(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, *CAMPOS_DA_EMPRESA)
        try:
            self._s.empresa.salvar(sessao, **valores)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._empresa(req, sessao, ctx, valores, _erros(recusa))
        return Resposta.redirecionar("/empresa?aviso=empresa")

    # Auditoria (Spec 013)

    def _auditoria(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("usuario", "operacao", "de", "fim", "registro")}
        erros: Dict[str, str] = {}
        inicio = _data_do_filtro(valores, "de", erros)
        fim = _data_do_filtro(valores, "fim", erros)
        opcoes = self._s.auditoria.opcoes_de_filtro(sessao)
        filtro = FiltroAuditoria(
            usuario_id=valores["usuario"] or None,
            inicio=inicio,
            fim=fim,
            operacao=valores["operacao"] or None,
            registro=valores["registro"] or None,
        )
        try:
            registros = self._s.auditoria.consultar(sessao, filtro)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            registros, erros = [], {**erros, **_erros(recusa)}
        return Resposta.pagina(p.pagina_auditoria(ctx, registros, opcoes, valores, erros), 400 if erros else 200)

    # Usuários e permissões (Spec 002)

    def _usuarios(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        return Resposta.pagina(p.pagina_usuarios(ctx, self._s.acesso.listar_usuarios(sessao), _aviso(req)))

    def _usuario_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.ADMINISTRAR_USUARIOS)
        return Resposta.pagina(p.pagina_usuario_formulario(ctx, {}, {}))

    def _usuario_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "email", "perfil")
        senha = req.formulario.get("senha", "")
        try:
            usuario = self._s.acesso.cadastrar_usuario(sessao, valores["nome"], valores["email"], _perfil(valores["perfil"]), senha)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(p.pagina_usuario_formulario(ctx, valores, _erros(recusa)), 400)
        return Resposta.redirecionar(f"/usuarios/{usuario.id}?aviso=usuario")

    def _usuario(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, usuario_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        usuario = self._s.acesso.obter_usuario(sessao, usuario_id)
        pagina = p.pagina_usuario(ctx, usuario, valores or {}, erros or {}, None if erros else _aviso(req))
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
        pagina = p.pagina_permissoes(ctx, self._s.acesso.matriz(sessao), aviso or _aviso(req))
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

    # Apoio

    def _nomes_clientes(self, sessao: str, ctx: p.Contexto) -> Dict[str, str]:
        if not ctx.pode(Operacao.CONSULTAR_CLIENTES):
            return {}
        return {c.id: c.nome for c in self._s.clientes.consultar_clientes(sessao)}

    def _nomes_usuarios(self, sessao: str, ctx: p.Contexto) -> Dict[str, str]:
        """Quem elaborou e quem decidiu. Os nomes vêm dos responsáveis da auditoria, quando o perfil a consulta."""
        if not ctx.pode(Operacao.CONSULTAR_AUDITORIA):
            return {ctx.usuario.id: ctx.usuario.nome}
        return dict(self._s.auditoria.opcoes_de_filtro(sessao).responsaveis)

    def _historico(self, sessao: str, ctx: p.Contexto, registro: str):
        if not ctx.pode(Operacao.CONSULTAR_AUDITORIA):
            return None
        return self._s.auditoria.consultar(sessao, FiltroAuditoria(registro=registro))

    def _erro(self, status: int, titulo: str, mensagem: str, correlacao: Optional[str] = None) -> Resposta:
        return Resposta.pagina(p.pagina_erro(status, titulo, mensagem, correlacao), status)

    def _erro_inesperado(self, ambiente: dict, erro: Exception) -> Resposta:
        """RNF-21, E2: a página mostra só o identificador de correlação; o detalhe vai para o registro de erro."""
        notas = " ".join(getattr(erro, "__notes__", []))
        encontrado = _CORRELACAO.search(notas)
        if encontrado:
            correlacao = encontrado.group(1)
        else:
            correlacao = uuid.uuid4().hex
            operacao = f"{ambiente.get('REQUEST_METHOD', '')} {ambiente.get('PATH_INFO', '')}".strip()
            try:
                self._erros.registrar(
                    RegistroErro(self._relogio.agora(), operacao, None, correlacao, f"{type(erro).__name__}: {erro}")
                )
            except Exception:
                logging.getLogger("remindme").exception("Falha ao registrar o erro %s", correlacao)
        logging.getLogger("remindme").error("Erro não tratado (correlação %s)", correlacao, exc_info=erro)
        return self._erro(500, "Algo deu errado", "A operação não foi concluída e nada foi alterado. Tente de novo.", correlacao)


def _primeiros(valores: Dict[str, List[str]]) -> Dict[str, str]:
    return {chave: lista[0] for chave, lista in valores.items() if lista}


def _confere(enviado: str, esperado: str) -> bool:
    return bool(enviado) and bool(esperado) and hmac.compare_digest(enviado.encode(), esperado.encode())


def _valores(req: Requisicao, *nomes: str) -> Dict[str, str]:
    return {nome: req.campo(nome) for nome in nomes}


def _erros(recusa: OperacaoRecusada) -> Dict[str, str]:
    """RNF-14: os campos da recusa; sem campo, a mensagem vai para o topo do formulário."""
    return dict(recusa.campos) if recusa.campos else {"_": recusa.motivo}


def _valor_do_formulario(valores: Dict[str, str], erros: Dict[str, str]):
    if not valores["valor"]:
        erros["valor"] = "Informe o valor."
        return None
    valor = f.ler_valor(valores["valor"])
    if valor is None:
        erros["valor"] = "Informe um valor em reais, por exemplo 1.234,56."
    return valor


def _numero_do_formulario(valores: Dict[str, str], chave: str, mensagem: str, erros: Dict[str, str]):
    """Quantidade, valor unitário ou percentual no formato brasileiro (1.234,56). A regra fica no domínio."""
    if not valores[chave]:
        return None
    numero = f.ler_valor(valores[chave].replace("%", ""))
    if numero is None:
        erros[chave] = mensagem
    return numero


def _data_do_filtro(valores: Dict[str, str], chave: str, erros: Dict[str, str]):
    if not valores[chave]:
        return None
    lida = f.ler_data(valores[chave])
    if lida is None:
        erros[chave] = "Informe uma data válida."
    return lida


def _perfil(nome: str) -> Optional[Perfil]:
    return Perfil[nome] if nome in Perfil.__members__ else None


def _aviso(req: Requisicao) -> Optional[Tuple[str, str]]:
    codigo = req.consulta.get("aviso", "")
    if codigo == "vencimentos":
        quantidade = req.consulta.get("quantidade", "0")
        n = int(quantidade) if quantidade.isdigit() else 0
        return ("sucesso", f"Verificação concluída: {n} título(s) passaram a Vencido.")
    return AVISOS.get(codigo)
