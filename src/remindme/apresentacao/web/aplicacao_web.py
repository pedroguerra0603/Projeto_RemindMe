"""Aplicação WSGI da interface web (Spec 017, ADR-006).

A apresentação recebe a requisição, confere a sessão e a proteção do formulário, chama os serviços da
aplicação e devolve a página. Permissões e regras ficam nos serviços e no domínio (INV-1, DT-06).
"""

import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from typing import Dict, Optional

from remindme.aplicacao.acesso import SessaoInvalida
from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_auditoria import FiltroAuditoria, ServicoAuditoria
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_contas_pagar import FiltroContas, ServicoContasPagar
from remindme.aplicacao.servico_empresa import ServicoEmpresa
from remindme.aplicacao.servico_fornecedores import ServicoFornecedores
from remindme.aplicacao.servico_mensagens import ServicoMensagens
from remindme.aplicacao.servico_orcamentos import ServicoOrcamentos
from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos
from remindme.aplicacao.tempo import data_local
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_auditoria as pa
from remindme.apresentacao.web import paginas_empresa as pem
from remindme.apresentacao.web import paginas_entrada as pe
from remindme.apresentacao.web import paginas_pagar as pp
from remindme.apresentacao.web import paginas_painel as ppa
from remindme.apresentacao.web import paginas_usuarios as pu
from remindme.apresentacao.web.requisicao import (
    ARQUIVOS_ESTATICOS,
    AVISOS,
    COOKIE_ENTRADA,
    COOKIE_SESSAO,
    CorpoGrandeDemais,
    ESTATICO,
    ID,
    Manipulador,
    POLITICA_DE_CONTEUDO,
    Requisicao,
    Resposta,
    _CORRELACAO,
    _aviso,
    _confere,
    _data_do_filtro,
    _erros,
    _perfil,
    _sessao_encerrada,
    _valor_do_formulario,
    _valores,
    _volta,
)
from remindme.apresentacao.web.rotas_clientes import RotasClientes
from remindme.apresentacao.web.rotas_orcamentos import RotasOrcamentos
from remindme.apresentacao.web.rotas_titulos import RotasTitulos
from remindme.dominio.conta_pagar import EstadoContaPagar
from remindme.dominio.empresa import CAMPOS as CAMPOS_DA_EMPRESA
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Perfil


@dataclass
class Servicos:
    acesso: ServicoAcesso
    clientes: ServicoClientes
    titulos: ServicoTitulos
    auditoria: ServicoAuditoria
    orcamentos: Optional[ServicoOrcamentos] = None
    empresa: Optional[ServicoEmpresa] = None
    fornecedores: Optional[ServicoFornecedores] = None
    contas_pagar: Optional[ServicoContasPagar] = None
    mensagens: Optional[ServicoMensagens] = None


class AplicacaoWeb(RotasClientes, RotasOrcamentos, RotasTitulos):
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
        r.append(("GET", "/trocar-senha", self._trocar_senha_pagina, protegida))
        r.append(("POST", "/trocar-senha", self._trocar_senha, protegida))
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
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/envio", self._envio, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/resposta-do-cliente", self._resposta_do_cliente, protegida))
        r.append(("GET", "/mensagens", self._mensagens, protegida))
        r.append(("GET", f"/orcamentos/(?P<orcamento_id>{ID})/cancelamento", self._orcamento_cancelamento_pagina, protegida))
        r.append(("POST", f"/orcamentos/(?P<orcamento_id>{ID})/cancelamento", self._orcamento_cancelamento, protegida))
        r.append(("GET", "/fornecedores", self._fornecedores, protegida))
        r.append(("GET", "/fornecedores/novo", self._fornecedor_novo_pagina, protegida))
        r.append(("POST", "/fornecedores/novo", self._fornecedor_novo, protegida))
        r.append(("GET", f"/fornecedores/(?P<fornecedor_id>{ID})", self._fornecedor, protegida))
        r.append(("GET", f"/fornecedores/(?P<fornecedor_id>{ID})/editar", self._fornecedor_editar_pagina, protegida))
        r.append(("POST", f"/fornecedores/(?P<fornecedor_id>{ID})/editar", self._fornecedor_editar, protegida))
        r.append(("GET", "/contas-a-pagar", self._contas, protegida))
        r.append(("GET", "/contas-a-pagar/nova", self._conta_nova_pagina, protegida))
        r.append(("POST", "/contas-a-pagar/nova", self._conta_nova, protegida))
        r.append(("GET", f"/contas-a-pagar/(?P<conta_id>{ID})", self._conta, protegida))
        r.append(("POST", f"/contas-a-pagar/(?P<conta_id>{ID})/pagamentos", self._conta_pagamento, protegida))
        conta_estorno = f"/contas-a-pagar/(?P<conta_id>{ID})/pagamentos/(?P<pagamento_id>{ID})/estorno"
        r.append(("GET", conta_estorno, self._conta_estorno_pagina, protegida))
        r.append(("POST", conta_estorno, self._conta_estorno, protegida))
        r.append(("GET", f"/contas-a-pagar/(?P<conta_id>{ID})/cancelamento", self._conta_cancelamento_pagina, protegida))
        r.append(("POST", f"/contas-a-pagar/(?P<conta_id>{ID})/cancelamento", self._conta_cancelamento, protegida))
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
            return _sessao_encerrada(req)
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
            return _sessao_encerrada(req)
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
        contas = (
            self._s.contas_pagar.consultar_contas(sessao)
            if self._s.contas_pagar and ctx.pode(Operacao.CONSULTAR_CONTAS_PAGAR)
            else None
        )
        pagina = ppa.pagina_painel(
            ctx, visoes, self._nomes_clientes(sessao, ctx), registros, usuarios, _aviso(req), pendentes, pagamentos, orcamentos,
            contas,
        )
        return Resposta.pagina(pagina)

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
        pagina = pem.pagina_empresa(ctx, empresa, visoes, clientes, valores, erros or {}, None if erros else _aviso(req))
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
        return Resposta.pagina(pa.pagina_auditoria(ctx, registros, opcoes, valores, erros), 400 if erros else 200)

    # Usuários e permissões (Spec 002)

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

    # Fornecedores (Spec 018)

    def _fornecedores(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        termo = req.consulta.get("q", "").strip()
        fornecedores = self._s.fornecedores.consultar_fornecedores(sessao, termo)
        return Resposta.pagina(pp.pagina_fornecedores(ctx, fornecedores, termo, _aviso(req)))

    def _fornecedor_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_FORNECEDORES)
        return Resposta.pagina(pp.pagina_fornecedor_formulario(ctx, {}, {}))

    def _fornecedor_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            fornecedor = self._s.fornecedores.cadastrar_fornecedor(sessao, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(pp.pagina_fornecedor_formulario(ctx, valores, _erros(recusa)), 400)
        return Resposta.redirecionar(f"/fornecedores/{fornecedor.id}?aviso=fornecedor")

    def _fornecedor(self, req: Requisicao, sessao: str, ctx: p.Contexto, fornecedor_id: str) -> Resposta:
        fornecedor = self._s.fornecedores.obter_fornecedor(sessao, fornecedor_id)
        visoes = (
            self._s.contas_pagar.consultar_contas(sessao, FiltroContas(fornecedor_id=fornecedor.id))
            if ctx.pode(Operacao.CONSULTAR_CONTAS_PAGAR)
            else []
        )
        historico = self._historico(sessao, ctx, f"fornecedor {fornecedor.id}")
        return Resposta.pagina(pp.pagina_fornecedor(ctx, fornecedor, visoes, historico, _aviso(req)))

    def _fornecedor_editar_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto, fornecedor_id: str) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_FORNECEDORES)
        x = self._s.fornecedores.obter_fornecedor(sessao, fornecedor_id)
        valores = {"nome": x.nome, "documento": f.documento(x.documento), "contato": f.contato(x.contato)}
        return Resposta.pagina(pp.pagina_fornecedor_formulario(ctx, valores, {}, x.id))

    def _fornecedor_editar(self, req: Requisicao, sessao: str, ctx: p.Contexto, fornecedor_id: str) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            self._s.fornecedores.alterar_fornecedor(sessao, fornecedor_id, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(pp.pagina_fornecedor_formulario(ctx, valores, _erros(recusa), fornecedor_id), 400)
        return Resposta.redirecionar(f"/fornecedores/{fornecedor_id}?aviso=fornecedor-alterado")

    # Contas a pagar (Spec 018)

    def _contas(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("fornecedor", "estado", "de", "ate")}
        erros: Dict[str, str] = {}
        de = _data_do_filtro(valores, "de", erros)
        ate = _data_do_filtro(valores, "ate", erros)
        estado = EstadoContaPagar[valores["estado"]] if valores["estado"] in EstadoContaPagar.__members__ else None
        filtro = FiltroContas(fornecedor_id=valores["fornecedor"] or None, estado=estado, vencimento_de=de, vencimento_ate=ate)
        visoes = self._s.contas_pagar.consultar_contas(sessao, filtro)
        return Resposta.pagina(pp.pagina_contas(ctx, visoes, self._nomes_fornecedores(sessao, ctx), valores, erros, _aviso(req)))

    def _conta_nova_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CADASTRAR_CONTA_PAGAR)
        valores = {"fornecedor": req.consulta.get("fornecedor", "")}
        return Resposta.pagina(pp.pagina_conta_formulario(ctx, self._nomes_fornecedores(sessao, ctx), valores, {}))

    def _conta_nova(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "fornecedor", "descricao", "valor", "vencimento", "condicao")
        erros: Dict[str, str] = {}
        valor = _valor_do_formulario(valores, erros)
        vencimento = f.ler_data(valores["vencimento"]) if valores["vencimento"] else None
        if valores["vencimento"] and vencimento is None:
            erros["vencimento"] = "Informe uma data válida."
        if not valores["descricao"]:
            erros["descricao"] = "Informe o que foi comprado ou o motivo da conta."
        if not erros:
            try:
                conta = self._s.contas_pagar.cadastrar_conta(
                    sessao, valores["fornecedor"], valores["descricao"], valor, vencimento, valores["condicao"]
                )
                return Resposta.redirecionar(f"/contas-a-pagar/{conta.id}?aviso=conta")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        pagina = pp.pagina_conta_formulario(ctx, self._nomes_fornecedores(sessao, ctx), valores, erros)
        return Resposta.pagina(pagina, 400)

    def _conta(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None, pedido: str = "",
    ) -> Resposta:
        conta = self._s.contas_pagar.obter_conta(sessao, conta_id)
        pagina = pp.pagina_conta(
            ctx,
            conta,
            self._nomes_fornecedores(sessao, ctx).get(conta.fornecedor_id, "Fornecedor"),
            pedido or secrets.token_urlsafe(16),
            valores if valores is not None else {"data": ctx.hoje.isoformat()},
            erros or {},
            self._historico(sessao, ctx, f"conta_pagar {conta.id}"),
            None if erros else _aviso(req),
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _conta_pagamento(self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str) -> Resposta:
        """OPEN-25: o identificador do pedido nasce com o formulário e acompanha o envio."""
        valores = _valores(req, "valor", "data", "pedido")
        erros: Dict[str, str] = {}
        valor = _valor_do_formulario(valores, erros)
        data = f.ler_data(valores["data"]) if valores["data"] else None
        if valores["data"] and data is None:
            erros["data"] = "Informe uma data válida."
        if not erros:
            try:
                self._s.contas_pagar.registrar_pagamento(sessao, conta_id, valor, data, pedido_id=valores["pedido"] or None)
                return Resposta.redirecionar(f"/contas-a-pagar/{conta_id}?aviso=pagamento-conta")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return self._conta(req, sessao, ctx, conta_id, valores, erros, valores["pedido"])

    def _conta_estorno_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str, pagamento_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.ESTORNAR_PAGAMENTO_CONTA)
        conta = self._s.contas_pagar.obter_conta(sessao, conta_id)
        pagamento = next((pg for pg in conta.pagamentos if pg.id == pagamento_id), None)
        if pagamento is None:
            return self._erro(404, "Pagamento não encontrado", "O pagamento não existe nesta conta.")
        pagina = p.pagina_motivo(
            ctx,
            "Estornar pagamento",
            f"Pagamento de {f.moeda(pagamento.valor)} em {f.data(pagamento.data)}. O estorno restaura o saldo da conta.",
            f"/contas-a-pagar/{conta_id}/pagamentos/{pagamento_id}/estorno",
            f"/contas-a-pagar/{conta_id}",
            "Estornar pagamento",
            valores or {},
            erros or {},
            secao="contas",
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _conta_estorno(self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str, pagamento_id: str) -> Resposta:
        valores = _valores(req, "motivo")
        try:
            self._s.contas_pagar.estornar_pagamento(sessao, conta_id, pagamento_id, valores["motivo"], ctx.hoje)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._conta_estorno_pagina(req, sessao, ctx, conta_id, pagamento_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/contas-a-pagar/{conta_id}?aviso=estorno-conta")

    def _conta_cancelamento_pagina(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CANCELAR_CONTA_PAGAR)
        conta = self._s.contas_pagar.obter_conta(sessao, conta_id)
        pagina = p.pagina_motivo(
            ctx,
            "Cancelar conta a pagar",
            f"{conta.descricao}: {f.moeda(conta.valor)}, com vencimento em {f.data(conta.vencimento)}. O cancelamento é definitivo.",
            f"/contas-a-pagar/{conta_id}/cancelamento",
            f"/contas-a-pagar/{conta_id}",
            "Cancelar conta",
            valores or {},
            erros or {},
            secao="contas",
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _conta_cancelamento(self, req: Requisicao, sessao: str, ctx: p.Contexto, conta_id: str) -> Resposta:
        valores = _valores(req, "motivo")
        try:
            self._s.contas_pagar.cancelar_conta(sessao, conta_id, valores["motivo"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._conta_cancelamento_pagina(req, sessao, ctx, conta_id, valores, _erros(recusa))
        return Resposta.redirecionar(f"/contas-a-pagar/{conta_id}?aviso=cancelamento-conta")

    # Apoio

    def _nomes_fornecedores(self, sessao: str, ctx: p.Contexto) -> Dict[str, str]:
        if not ctx.pode(Operacao.CONSULTAR_FORNECEDORES):
            return {}
        return {x.id: x.nome for x in self._s.fornecedores.consultar_fornecedores(sessao)}

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


