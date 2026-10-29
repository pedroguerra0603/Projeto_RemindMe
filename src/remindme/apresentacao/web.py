"""Aplicação web (WSGI). Recebe a requisição, chama `Sistema` e devolve HTML.

Nenhuma regra de negócio mora aqui (ADR-001): a página só converte a entrada, chama a aplicação, que
autoriza e executa, e apresenta o resultado ou o motivo da recusa.
"""

import base64
import hashlib
import hmac
import logging
import secrets
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from remindme.aplicacao.portas import FiltroAuditoria
from remindme.aplicacao.servico_titulos import FiltroTitulos
from remindme.aplicacao.sistema import Sistema
from remindme.apresentacao import formatos as fmt
from remindme.apresentacao import paginas as pg
from remindme.apresentacao.http import Requisicao, Resposta, Rotas
from remindme.apresentacao.paginas import e
from remindme.dominio.acesso import Operacao, regra_que_fixa
from remindme.dominio.erros import AcessoNegado, EntradaInvalida, OperacaoRecusada
from remindme.dominio.titulo import ESTADOS_QUE_ACEITAM_CANCELAMENTO, ESTADOS_QUE_ACEITAM_PAGAMENTO, EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario

COOKIE_SESSAO = "remindme_sessao"
COOKIE_AVISO = "remindme_aviso"
ESTATICOS = Path(__file__).resolve().parent.joinpath("estatico")
TIPOS_ESTATICOS = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8"}
CABECALHOS_SEGURANCA = [
    (
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'self'",
    ),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Referrer-Policy", "same-origin"),
]

log = logging.getLogger("remindme.web")


class SemSessao(Exception):
    pass


class Contexto:
    """O que cada página autenticada precisa: token, usuário, operações permitidas e CSRF."""

    def __init__(self, web: "AplicacaoWeb", requisicao: Requisicao):
        self.requisicao = requisicao
        self.token = requisicao.cookies.get(COOKIE_SESSAO)
        try:
            self.usuario: Usuario = web.sistema.usuario(self.token)
        except AcessoNegado:
            raise SemSessao() from None
        self.operacoes = web.sistema.acesso.operacoes_permitidas(self.usuario.perfil)
        self.csrf = web.csrf(self.token)
        self.aviso = web.ler_aviso(requisicao)

    def pode(self, *operacoes: Operacao) -> bool:
        return any(op in self.operacoes for op in operacoes)


class AplicacaoWeb:
    def __init__(self, sistema: Sistema, segredo: Optional[bytes] = None, cookies_seguros: bool = False):
        self.sistema = sistema
        self._segredo = segredo or secrets.token_bytes(32)
        self._seguro = cookies_seguros
        self.rotas = Rotas()
        r = self.rotas.adicionar
        r("GET", "/login", self.login_formulario)
        r("POST", "/login", self.login)
        r("POST", "/sair", self.sair)
        r("GET", "/saude", lambda req: Resposta(b"ok", tipo="text/plain; charset=utf-8"))
        r("GET", "/static/{arquivo}.{ext}", self.estatico)
        r("GET", "/", self.autenticada(self.painel))
        r("GET", "/titulos", self.autenticada(self.titulos))
        r("GET", "/titulos/novo", self.autenticada(self.titulo_novo))
        r("POST", "/titulos/novo", self.autenticada(self.titulo_criar))
        r("POST", "/titulos/verificar-vencimentos", self.autenticada(self.verificar_vencimentos))
        r("GET", "/titulos/{id}", self.autenticada(self.titulo))
        r("POST", "/titulos/{id}/pagamentos", self.autenticada(self.pagamento_registrar))
        r("POST", "/titulos/{id}/pagamentos/{pagamento}/estorno", self.autenticada(self.pagamento_estornar))
        r("POST", "/titulos/{id}/cancelamento", self.autenticada(self.titulo_cancelar))
        r("GET", "/clientes", self.autenticada(self.clientes))
        r("GET", "/clientes/novo", self.autenticada(self.cliente_novo))
        r("POST", "/clientes/novo", self.autenticada(self.cliente_criar))
        r("GET", "/clientes/{id}", self.autenticada(self.cliente))
        r("POST", "/clientes/{id}", self.autenticada(self.cliente_alterar))
        r("GET", "/auditoria", self.autenticada(self.auditoria))
        r("GET", "/usuarios", self.autenticada(self.usuarios))
        r("GET", "/usuarios/novo", self.autenticada(self.usuario_novo))
        r("POST", "/usuarios/novo", self.autenticada(self.usuario_criar))
        r("GET", "/usuarios/{id}", self.autenticada(self.usuario_detalhe))
        r("POST", "/usuarios/{id}/perfil", self.autenticada(self.usuario_perfil))
        r("POST", "/usuarios/{id}/inativacao", self.autenticada(self.usuario_inativar))
        r("POST", "/usuarios/{id}/reativacao", self.autenticada(self.usuario_reativar))
        r("GET", "/permissoes", self.autenticada(self.permissoes))
        r("POST", "/permissoes", self.autenticada(self.permissoes_salvar))

    # WSGI

    def __call__(self, ambiente, iniciar):
        requisicao = Requisicao(ambiente)
        resposta = self.responder(requisicao)
        cabecalhos = [("Content-Type", resposta.tipo), ("Content-Length", str(len(resposta.corpo)))]
        cabecalhos += CABECALHOS_SEGURANCA + resposta.cabecalhos
        if resposta.tipo.startswith("text/html"):
            cabecalhos.append(("Cache-Control", "no-store"))
        iniciar(resposta.linha_de_status(), cabecalhos)
        return [resposta.corpo] if requisicao.metodo != "HEAD" else [b""]

    def responder(self, requisicao: Requisicao) -> Resposta:
        metodo = "GET" if requisicao.metodo == "HEAD" else requisicao.metodo
        caminho = requisicao.caminho.rstrip("/") or "/"
        manipulador, parametros, existe = self.rotas.encontrar(metodo, caminho)
        if manipulador is None:
            if existe:
                return Resposta.html(pg.pagina_erro(405, "Método não permitido", "Use o formulário da página."), 405)
            return Resposta.html(pg.pagina_erro(404, "Página não encontrada", "O endereço não existe."), 404)
        requisicao.parametros = parametros
        try:
            return manipulador(requisicao)
        except Exception as erro:  # RNF-21: a pessoa vê um identificador, e o detalhe fica no log.
            notas = " ".join(getattr(erro, "__notes__", []))
            log.exception("Erro ao atender %s %s %s", requisicao.metodo, requisicao.caminho, notas)
            mensagem = "Ocorreu um erro inesperado. Nada foi alterado."
            if notas:
                mensagem += f" {notas}."
            return Resposta.html(pg.pagina_erro(500, "Erro inesperado", mensagem), 500)

    def autenticada(self, manipulador: Callable[[Requisicao, Contexto], Resposta]):
        """RNF-01: toda página, exceto o login, exige sessão. POST exige o token CSRF."""

        def envolver(requisicao: Requisicao) -> Resposta:
            try:
                contexto = Contexto(self, requisicao)
            except SemSessao:
                resposta = Resposta.redirecionar("/login")
                if requisicao.cookies.get(COOKIE_SESSAO):
                    resposta.apagar_cookie(COOKIE_SESSAO, self._seguro)
                return resposta
            if requisicao.metodo == "POST" and not hmac.compare_digest(
                requisicao.campo("_csrf"), contexto.csrf
            ):
                return Resposta.html(
                    pg.pagina_erro(400, "Formulário expirado", "Recarregue a página e tente de novo."), 400
                )
            try:
                return manipulador(requisicao, contexto)
            except AcessoNegado as negado:
                return self.erro(contexto, 403, "Acesso negado", negado.motivo)
            except OperacaoRecusada as recusa:
                if requisicao.metodo == "POST":
                    return self.voltar(requisicao, "erro", recusa.motivo)
                return self.erro(contexto, 404, "Não encontrado", recusa.motivo)

        return envolver

    # Apoio

    def csrf(self, token: Optional[str]) -> str:
        return hmac.new(self._segredo, (token or "").encode(), hashlib.sha256).hexdigest()

    def com_aviso(self, resposta: Resposta, tipo: str, texto: str) -> Resposta:
        """O aviso sobrevive ao redirecionamento num cookie assinado, lido uma única vez."""
        dados = base64.urlsafe_b64encode(f"{tipo}|{texto}".encode()).decode()
        assinatura = hmac.new(self._segredo, dados.encode(), hashlib.sha256).hexdigest()[:32]
        resposta.definir_cookie(COOKIE_AVISO, f"{dados}.{assinatura}", self._seguro, max_age=60)
        return resposta

    def ler_aviso(self, requisicao: Requisicao) -> Optional[Tuple[str, str]]:
        bruto = requisicao.cookies.get(COOKIE_AVISO)
        if not bruto or "." not in bruto:
            return None
        dados, assinatura = bruto.rsplit(".", 1)
        esperada = hmac.new(self._segredo, dados.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(assinatura, esperada):
            return None
        try:
            tipo, texto = base64.urlsafe_b64decode(dados.encode()).decode().split("|", 1)
        except (ValueError, UnicodeDecodeError):
            return None
        return tipo, texto

    def ir(self, destino: str, tipo: str, texto: str) -> Resposta:
        return self.com_aviso(Resposta.redirecionar(destino), tipo, texto)

    def voltar(self, requisicao: Requisicao, tipo: str, texto: str) -> Resposta:
        """Depois de um POST recusado, volta para a página do recurso com o motivo."""
        destino = requisicao.caminho
        for sufixo in ("/pagamentos", "/cancelamento", "/perfil", "/inativacao", "/reativacao"):
            if sufixo in destino:
                destino = destino[: destino.index(sufixo)]
        if destino == "/titulos/verificar-vencimentos":
            destino = "/titulos"
        return self.ir(destino, tipo, texto)

    def pagina(self, ctx: Contexto, titulo: str, conteudo: str, status: int = 200) -> Resposta:
        html = pg.layout(titulo, conteudo, ctx.usuario, ctx.operacoes, ctx.requisicao.caminho, ctx.csrf, ctx.aviso)
        resposta = Resposta.html(html, status)
        if ctx.aviso:
            resposta.apagar_cookie(COOKIE_AVISO, self._seguro)
        return resposta

    def erro(self, ctx: Contexto, status: int, titulo: str, motivo: str) -> Resposta:
        """RF-67: a negação informa o motivo."""
        conteudo = f"""<section class="cartao pagina-erro"><p class="codigo-erro">{status}</p><h1>{e(titulo)}</h1>
<p>{e(motivo)}</p><a class="botao botao-primario" href="/">Voltar ao painel</a></section>"""
        return self.pagina(ctx, titulo, conteudo, status)

    def nomes_clientes(self, ctx: Contexto) -> Dict[str, str]:
        return {c.id: c.nome for c in self.sistema.listar_clientes(ctx.token)}

    # Login (UC-01)

    def login_formulario(self, requisicao: Requisicao) -> Resposta:
        try:
            self.sistema.usuario(requisicao.cookies.get(COOKIE_SESSAO))
            return Resposta.redirecionar("/")
        except AcessoNegado:
            pass
        aviso = self.ler_aviso(requisicao)
        resposta = Resposta.html(pg.pagina_login(aviso=aviso[1] if aviso else None))
        if aviso:
            resposta.apagar_cookie(COOKIE_AVISO, self._seguro)
        return resposta

    def login(self, requisicao: Requisicao) -> Resposta:
        email = requisicao.campo("email")
        try:
            sessao = self.sistema.acesso.entrar(email, requisicao.campo("senha"))
        except AcessoNegado as negado:
            return Resposta.html(pg.pagina_login(negado.motivo, email), 401)
        resposta = Resposta.redirecionar("/")
        resposta.definir_cookie(COOKIE_SESSAO, sessao.token, self._seguro)
        return resposta

    def sair(self, requisicao: Requisicao) -> Resposta:
        token = requisicao.cookies.get(COOKIE_SESSAO)
        if token and hmac.compare_digest(requisicao.campo("_csrf"), self.csrf(token)):
            self.sistema.acesso.sair(token)
        resposta = self.ir("/login", "sucesso", "Sessão encerrada.")
        resposta.apagar_cookie(COOKIE_SESSAO, self._seguro)
        return resposta

    def estatico(self, requisicao: Requisicao) -> Resposta:
        nome = f"{requisicao.parametros['arquivo']}.{requisicao.parametros['ext']}"
        arquivo = ESTATICOS.joinpath(nome)
        tipo = TIPOS_ESTATICOS.get(arquivo.suffix)
        if tipo is None or arquivo.parent != ESTATICOS or not arquivo.is_file():
            return Resposta.html(pg.pagina_erro(404, "Não encontrado", "Arquivo inexistente."), 404)
        resposta = Resposta(arquivo.read_bytes(), tipo=tipo)
        resposta.cabecalhos.append(("Cache-Control", "public, max-age=3600"))
        return resposta

    # Painel (RNF-15, RNF-17)

    def painel(self, req: Requisicao, ctx: Contexto) -> Resposta:
        painel = self.sistema.painel(ctx.token)
        partes = [pg.cabecalho(f"Olá, {ctx.usuario.nome.split()[0]}", f"Hoje é {fmt.data(painel.hoje)}.", self._acoes_painel(ctx))]
        if ctx.pode(Operacao.CONSULTAR_TITULOS):
            nomes = self.nomes_clientes(ctx)
            partes.append(
                '<section class="indicadores">'
                + pg.cartao_indicador("A receber", fmt.dinheiro(painel.total_a_receber), detalhe=f"{painel.quantidade_abertos} título(s) em aberto")
                + pg.cartao_indicador("Vencido", fmt.dinheiro(painel.total_vencido), "perigo" if painel.vencidos else "", f"{len(painel.vencidos)} título(s)")
                + pg.cartao_indicador("Próximos do vencimento", str(len(painel.proximos)), "atencao" if painel.proximos else "", f"nos próximos {self.sistema.antecedencia_dias} dias")
                + pg.cartao_indicador("Recebido no mês", fmt.dinheiro(painel.recebido_no_mes), "sucesso" if painel.recebido_no_mes else "")
                + "</section>"
            )
            partes.append('<div class="grade-2">')
            partes.append(
                '<section class="cartao destaque-perigo"><h2>Títulos vencidos</h2>'
                + self._tabela_titulos(painel.vencidos, nomes, "Nenhum título vencido. Ótimo!", resumida=True)
                + "</section>"
            )
            partes.append(
                '<section class="cartao destaque-atencao"><h2>Próximos do vencimento</h2>'
                + self._tabela_titulos(painel.proximos, nomes, "Nenhum título vence nos próximos dias.", resumida=True)
                + "</section>"
            )
            partes.append("</div>")
        if ctx.pode(Operacao.ADMINISTRAR_USUARIOS):
            partes.append(
                '<section class="indicadores">'
                + pg.cartao_indicador("Usuários ativos", str(painel.usuarios_ativos))
                + "</section>"
                + '<section class="cartao"><h2>Administração</h2><p>Mantenha os usuários, os perfis e as permissões de cada perfil. '
                "As permissões fixadas por regra de negócio não podem ser alteradas.</p>"
                '<p class="acoes"><a class="botao botao-primario" href="/usuarios/novo">Cadastrar usuário</a> '
                '<a class="botao" href="/permissoes">Ver permissões</a></p></section>'
            )
        if len(partes) == 1:
            partes.append('<section class="cartao"><p>Seu perfil ainda não tem operações disponíveis nesta versão.</p></section>')
        return self.pagina(ctx, "Painel", "".join(partes))

    def _acoes_painel(self, ctx: Contexto) -> str:
        acoes = []
        if ctx.pode(Operacao.MANTER_TITULOS):
            acoes.append('<a class="botao botao-primario" href="/titulos/novo">Novo título</a>')
        if ctx.pode(Operacao.MANTER_CLIENTES):
            acoes.append('<a class="botao" href="/clientes/novo">Novo cliente</a>')
        return "".join(acoes)

    # Títulos (Spec 006)

    def _tabela_titulos(self, visoes, nomes: Dict[str, str], vazio: str, resumida: bool = False) -> str:
        linhas = []
        for v in visoes:
            estado = pg.selo_estado(v.estado)
            if v.proximo_do_vencimento:
                estado += " " + pg.selo("Próximo do vencimento", "proximo")
            link = f'<a href="/titulos/{e(v.id)}">{e(nomes.get(v.cliente_id, "—"))}</a>'
            if resumida:
                linhas.append([link, e(fmt.data(v.vencimento)), f'<span class="numero">{e(fmt.dinheiro(v.saldo))}</span>'])
            else:
                linhas.append([
                    link,
                    e(fmt.data(v.vencimento)),
                    f'<span class="numero">{e(fmt.dinheiro(v.valor))}</span>',
                    f'<span class="numero">{e(fmt.dinheiro(v.saldo))}</span>',
                    estado,
                ])
        colunas = ["Cliente", "Vencimento", "Saldo"] if resumida else ["Cliente", "Vencimento", "Valor", "Saldo", "Estado"]
        return pg.tabela(colunas, linhas, vazio)

    def titulos(self, req: Requisicao, ctx: Contexto) -> Resposta:
        q = req.consulta
        erros = {}
        try:
            de = fmt.ler_data(q.get("de"))
        except fmt.ValorInvalido:
            de, erros["vencimento de"] = None, "data inválida"
        try:
            ate = fmt.ler_data(q.get("ate"))
        except fmt.ValorInvalido:
            ate, erros["vencimento até"] = None, "data inválida"
        estado = next((s for s in EstadoTitulo if s.name == q.get("estado")), None)
        filtro = FiltroTitulos(cliente_id=q.get("cliente") or None, estado=estado, vencimento_de=de, vencimento_ate=ate)
        visoes = self.sistema.consultar_titulos(ctx.token, filtro)
        nomes = self.nomes_clientes(ctx)
        acoes = []
        if ctx.pode(Operacao.VERIFICAR_VENCIMENTOS):
            acoes.append(
                f'<form method="post" action="/titulos/verificar-vencimentos">{pg.campo_csrf(ctx.csrf)}'
                '<button class="botao">Verificar vencimentos</button></form>'
            )
        if ctx.pode(Operacao.MANTER_TITULOS):
            acoes.append('<a class="botao botao-primario" href="/titulos/novo">Novo título</a>')
        filtros = f"""
<form method="get" action="/titulos" class="filtros cartao">
  {pg.selecao("cliente", "Cliente", sorted(((i, n) for i, n in nomes.items()), key=lambda x: x[1].lower()), q.get("cliente", ""), vazio="Todos")}
  {pg.selecao("estado", "Estado", [(s.name, s.value) for s in EstadoTitulo], q.get("estado", ""), vazio="Todos")}
  {pg.entrada("de", "Vencimento de", q.get("de", ""), "date")}
  {pg.entrada("ate", "Vencimento até", q.get("ate", ""), "date")}
  <div class="filtros-acoes"><button class="botao botao-primario">Filtrar</button> <a class="botao botao-leve" href="/titulos">Limpar</a></div>
</form>"""
        total = sum((v.saldo for v in visoes if v.estado in ESTADOS_QUE_ACEITAM_PAGAMENTO), Decimal("0"))
        resumo = f'<p class="resumo">{len(visoes)} título(s) · saldo em aberto {e(fmt.dinheiro(total))}</p>'
        conteudo = (
            pg.cabecalho("Títulos", "Valores a receber dos clientes.", "".join(acoes))
            + pg.erros_formulario(erros)
            + filtros
            + '<section class="cartao">' + resumo
            + self._tabela_titulos(visoes, nomes, "Nenhum título encontrado com esses filtros.")
            + "</section>"
        )
        return self.pagina(ctx, "Títulos", conteudo)

    def titulo_novo(self, req: Requisicao, ctx: Contexto, erros=None, valores=None, status=200) -> Resposta:
        self.sistema.acesso.autorizar(ctx.token, Operacao.MANTER_TITULOS)
        erros = erros or {}
        v = valores or {"cliente": req.consulta.get("cliente", "")}
        clientes = self.sistema.listar_clientes(ctx.token)
        if not clientes:
            aviso_clientes = '<div class="aviso aviso-info">Cadastre um cliente antes de cadastrar títulos. <a href="/clientes/novo">Cadastrar cliente</a></div>'
        else:
            aviso_clientes = ""
        formulario = f"""
{aviso_clientes}
{pg.erros_formulario(erros)}
<form method="post" action="/titulos/novo" class="cartao formulario">
  {pg.campo_csrf(ctx.csrf)}
  {pg.selecao("cliente", "Cliente", [(c.id, f"{c.nome} · {c.documento_formatado}") for c in clientes], v.get("cliente", ""), erros.get("cliente"), True, vazio="Selecione")}
  <div class="linha">
    {pg.entrada("valor", "Valor (R$)", v.get("valor", ""), "text", erros.get("valor"), True, 'inputmode="decimal" placeholder="0,00"')}
    {pg.entrada("vencimento", "Vencimento", v.get("vencimento", ""), "date", erros.get("vencimento"), True)}
  </div>
  {pg.entrada("condicao", "Condição de pagamento", v.get("condicao", ""), "text", erros.get("condição de pagamento"), extra='placeholder="Ex.: PIX à vista"')}
  <div class="acoes"><button class="botao botao-primario">Cadastrar título</button> <a class="botao botao-leve" href="/titulos">Cancelar</a></div>
</form>"""
        return self.pagina(ctx, "Novo título", pg.cabecalho("Novo título", "O título nasce Aberto, com saldo igual ao valor.") + formulario, status)

    def titulo_criar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        valores = {k: req.campo(k) for k in ("cliente", "valor", "vencimento", "condicao")}
        erros = {}
        if not valores["cliente"]:
            erros["cliente"] = "obrigatório"
        valor = vencimento = None
        try:
            valor = fmt.ler_dinheiro(valores["valor"])
        except fmt.ValorInvalido as erro:
            erros["valor"] = str(erro)
        try:
            vencimento = fmt.ler_data(valores["vencimento"])
            if vencimento is None:
                erros["vencimento"] = "obrigatório"
        except fmt.ValorInvalido as erro:
            erros["vencimento"] = str(erro)
        if erros:
            return self.titulo_novo(req, ctx, erros, valores, 400)
        try:
            titulo = self.sistema.cadastrar_titulo(ctx.token, valores["cliente"], valor, vencimento, valores["condicao"].strip() or None)
        except AcessoNegado:
            raise
        except OperacaoRecusada as recusa:
            return self.titulo_novo(req, ctx, {"título": recusa.motivo}, valores, 400)
        return self.ir(f"/titulos/{titulo.id}", "sucesso", "Título cadastrado.")

    def titulo(self, req: Requisicao, ctx: Contexto) -> Resposta:
        titulo = self.sistema.obter_titulo(ctx.token, req.parametros["id"])
        try:
            cliente = self.sistema.obter_cliente(ctx.token, titulo.cliente_id)
            nome_cliente = f'<a href="/clientes/{e(cliente.id)}">{e(cliente.nome)}</a>'
        except OperacaoRecusada:
            nome_cliente = "—"
        hoje = self.sistema.hoje()
        proximo = titulo.proximo_do_vencimento(hoje, self.sistema.antecedencia_dias)
        estado = pg.selo_estado(titulo.estado) + (" " + pg.selo("Próximo do vencimento", "proximo") if proximo else "")
        dados = f"""
<section class="cartao">
  <dl class="dados">
    <div><dt>Cliente</dt><dd>{nome_cliente}</dd></div>
    <div><dt>Estado</dt><dd>{estado}</dd></div>
    <div><dt>Valor</dt><dd class="numero">{e(fmt.dinheiro(titulo.valor))}</dd></div>
    <div><dt>Saldo</dt><dd class="numero destaque">{e(fmt.dinheiro(titulo.saldo))}</dd></div>
    <div><dt>Vencimento</dt><dd>{e(fmt.data(titulo.vencimento))}</dd></div>
    <div><dt>Origem</dt><dd>{e(titulo.origem.capitalize())}</dd></div>
    <div><dt>Condição de pagamento</dt><dd>{e(titulo.condicao_pagamento or "—")}</dd></div>
    <div><dt>Referência</dt><dd><code>{e(titulo.id[:8])}</code></dd></div>
  </dl>
</section>"""
        pode_estornar = ctx.pode(Operacao.ESTORNAR_PAGAMENTO) and titulo.estado is not EstadoTitulo.CANCELADO
        linhas = []
        for p in titulo.pagamentos:
            situacao = pg.selo("Estornado", "cancelado") + f' <small>{e(p.motivo_estorno)}</small>' if p.estornado else pg.selo("Válido", "baixado")
            acao = ""
            if pode_estornar and not p.estornado:
                acao = f"""<details class="acao-inline"><summary class="botao botao-leve botao-pequeno">Estornar</summary>
<form method="post" action="/titulos/{e(titulo.id)}/pagamentos/{e(p.id)}/estorno" class="formulario-inline">
{pg.campo_csrf(ctx.csrf)}<input name="motivo" required placeholder="Motivo do estorno" aria-label="Motivo do estorno">
<button class="botao botao-perigo botao-pequeno">Confirmar estorno</button></form></details>"""
            linhas.append([e(fmt.data(p.data)), f'<span class="numero">{e(fmt.dinheiro(p.valor))}</span>', situacao, acao])
        pagamentos = '<section class="cartao"><h2>Pagamentos</h2>' + pg.tabela(["Data", "Valor", "Situação", ""], linhas, "Nenhum pagamento registrado.") + "</section>"
        acoes = []
        if ctx.pode(Operacao.MANTER_TITULOS) and titulo.estado in ESTADOS_QUE_ACEITAM_PAGAMENTO:
            acoes.append(f"""
<section class="cartao">
  <h2>Registrar pagamento</h2>
  <form method="post" action="/titulos/{e(titulo.id)}/pagamentos" class="formulario">
    {pg.campo_csrf(ctx.csrf)}
    <div class="linha">
      {pg.entrada("valor", "Valor (R$)", "", "text", obrigatorio=True, extra='inputmode="decimal" placeholder="0,00"', ajuda=f"Saldo: {fmt.dinheiro(titulo.saldo)}")}
      {pg.entrada("data", "Data do pagamento", fmt.iso(hoje), "date", obrigatorio=True)}
    </div>
    <div class="acoes"><button class="botao botao-primario">Registrar pagamento</button></div>
  </form>
</section>""")
        if ctx.pode(Operacao.CANCELAR_TITULO) and titulo.estado in ESTADOS_QUE_ACEITAM_CANCELAMENTO:
            acoes.append(f"""
<section class="cartao zona-perigo">
  <h2>Cancelar título</h2>
  <p>O cancelamento é definitivo. Títulos com pagamento integral precisam de estorno antes.</p>
  <form method="post" action="/titulos/{e(titulo.id)}/cancelamento" class="formulario">
    {pg.campo_csrf(ctx.csrf)}
    {pg.entrada("motivo", "Motivo do cancelamento", "", "text", obrigatorio=True)}
    <div class="acoes"><button class="botao botao-perigo">Cancelar título</button></div>
  </form>
</section>""")
        historico = ""
        if ctx.pode(Operacao.CONSULTAR_AUDITORIA):
            registros = self.sistema.consultar_auditoria(ctx.token, FiltroAuditoria(registro_afetado=f"titulo {titulo.id}"), 100)
            historico = '<section class="cartao"><h2>Histórico</h2>' + self._tabela_auditoria(registros, self.sistema.nomes_dos_usuarios(ctx.token), resumida=True) + "</section>"
        conteudo = (
            pg.cabecalho("Título", f"Vencimento em {fmt.data(titulo.vencimento)}", '<a class="botao botao-leve" href="/titulos">Voltar</a>')
            + dados
            + '<div class="grade-2">' + pagamentos + "".join(acoes) + "</div>"
            + historico
        )
        return self.pagina(ctx, "Título", conteudo)

    def pagamento_registrar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        titulo_id = req.parametros["id"]
        try:
            valor = fmt.ler_dinheiro(req.campo("valor"))
            data = fmt.ler_data(req.campo("data"))
        except fmt.ValorInvalido as erro:
            return self.ir(f"/titulos/{titulo_id}", "erro", f"Pagamento recusado: {erro}.")
        if data is None:
            return self.ir(f"/titulos/{titulo_id}", "erro", "Pagamento recusado: a data é obrigatória.")
        titulo = self.sistema.registrar_pagamento(ctx.token, titulo_id, valor, data)
        texto = "Pagamento registrado. Título baixado." if titulo.estado is EstadoTitulo.BAIXADO else f"Pagamento registrado. Saldo restante: {fmt.dinheiro(titulo.saldo)}."
        return self.ir(f"/titulos/{titulo_id}", "sucesso", texto)

    def pagamento_estornar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        titulo_id = req.parametros["id"]
        try:
            self.sistema.estornar_pagamento(ctx.token, titulo_id, req.parametros["pagamento"], req.campo("motivo"))
        except AcessoNegado:
            raise
        except OperacaoRecusada as recusa:
            return self.ir(f"/titulos/{titulo_id}", "erro", recusa.motivo)
        return self.ir(f"/titulos/{titulo_id}", "sucesso", "Pagamento estornado.")

    def titulo_cancelar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        titulo_id = req.parametros["id"]
        self.sistema.cancelar_titulo(ctx.token, titulo_id, req.campo("motivo"))
        return self.ir(f"/titulos/{titulo_id}", "sucesso", "Título cancelado.")

    def verificar_vencimentos(self, req: Requisicao, ctx: Contexto) -> Resposta:
        vencidos = self.sistema.verificar_vencimentos(ctx.token)
        texto = f"{len(vencidos)} título(s) passaram a Vencido." if vencidos else "Nenhum título mudou de estado."
        return self.ir("/titulos", "sucesso", texto)

    # Clientes (Spec 003)

    def clientes(self, req: Requisicao, ctx: Contexto) -> Resposta:
        busca = req.consulta.get("busca", "")
        clientes = self.sistema.listar_clientes(ctx.token, busca)
        linhas = [
            [f'<a href="/clientes/{e(c.id)}">{e(c.nome)}</a>', e(c.documento_formatado), e(c.email or "—"), e(c.telefone or "—")]
            for c in clientes
        ]
        acoes = '<a class="botao botao-primario" href="/clientes/novo">Novo cliente</a>' if ctx.pode(Operacao.MANTER_CLIENTES) else ""
        conteudo = (
            pg.cabecalho("Clientes", "Pessoas e empresas que devem títulos.", acoes)
            + f"""<form method="get" action="/clientes" class="filtros cartao">
{pg.entrada("busca", "Buscar por nome ou documento", busca, "search")}
<div class="filtros-acoes"><button class="botao botao-primario">Buscar</button> <a class="botao botao-leve" href="/clientes">Limpar</a></div></form>"""
            + '<section class="cartao">'
            + pg.tabela(["Nome", "Documento", "E-mail", "Telefone"], linhas, "Nenhum cliente encontrado.")
            + "</section>"
        )
        return self.pagina(ctx, "Clientes", conteudo)

    def _formulario_cliente(self, ctx: Contexto, acao: str, botao: str, valores: Dict[str, str], erros: Dict[str, str]) -> str:
        return f"""
{pg.erros_formulario(erros)}
<form method="post" action="{e(acao)}" class="cartao formulario">
  {pg.campo_csrf(ctx.csrf)}
  {pg.entrada("nome", "Nome ou razão social", valores.get("nome", ""), "text", erros.get("nome"), True)}
  {pg.entrada("documento", "CPF ou CNPJ", valores.get("documento", ""), "text", erros.get("documento"), True, 'inputmode="numeric"')}
  <div class="linha">
    {pg.entrada("email", "E-mail", valores.get("email", ""), "email", erros.get("e-mail"))}
    {pg.entrada("telefone", "Telefone", valores.get("telefone", ""), "tel", erros.get("telefone"))}
  </div>
  <div class="acoes"><button class="botao botao-primario">{e(botao)}</button> <a class="botao botao-leve" href="/clientes">Voltar</a></div>
</form>"""

    def cliente_novo(self, req: Requisicao, ctx: Contexto, erros=None, valores=None, status=200) -> Resposta:
        self.sistema.acesso.autorizar(ctx.token, Operacao.MANTER_CLIENTES)
        conteudo = pg.cabecalho("Novo cliente") + self._formulario_cliente(ctx, "/clientes/novo", "Cadastrar cliente", valores or {}, erros or {})
        return self.pagina(ctx, "Novo cliente", conteudo, status)

    def _dados_cliente(self, req: Requisicao) -> Dict[str, str]:
        return {k: req.campo(k) for k in ("nome", "documento", "email", "telefone")}

    def cliente_criar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        valores = self._dados_cliente(req)
        try:
            cliente = self.sistema.cadastrar_cliente(ctx.token, **valores)
        except EntradaInvalida as invalida:
            return self.cliente_novo(req, ctx, invalida.campos, valores, 400)
        return self.ir(f"/clientes/{cliente.id}", "sucesso", "Cliente cadastrado.")

    def cliente(self, req: Requisicao, ctx: Contexto, erros=None, valores=None, status=200) -> Resposta:
        cliente = self.sistema.obter_cliente(ctx.token, req.parametros["id"])
        partes = [pg.cabecalho(cliente.nome, cliente.documento_formatado, '<a class="botao botao-leve" href="/clientes">Voltar</a>')]
        if ctx.pode(Operacao.CONSULTAR_TITULOS):
            visoes = self.sistema.consultar_titulos(ctx.token, FiltroTitulos(cliente_id=cliente.id))
            novo = f' <a class="botao botao-pequeno" href="/titulos/novo?cliente={e(cliente.id)}">Novo título</a>' if ctx.pode(Operacao.MANTER_TITULOS) else ""
            partes.append(f'<section class="cartao"><h2>Títulos{novo}</h2>' + self._tabela_titulos(visoes, {cliente.id: cliente.nome}, "Este cliente não tem títulos.") + "</section>")
        if ctx.pode(Operacao.MANTER_CLIENTES):
            dados = valores or {
                "nome": cliente.nome,
                "documento": cliente.documento_formatado,
                "email": cliente.email,
                "telefone": cliente.telefone,
            }
            partes.append("<h2 class=\"secao\">Dados do cliente</h2>" + self._formulario_cliente(ctx, f"/clientes/{cliente.id}", "Salvar alterações", dados, erros or {}))
        else:
            partes.append(f"""<section class="cartao"><dl class="dados">
<div><dt>E-mail</dt><dd>{e(cliente.email or "—")}</dd></div><div><dt>Telefone</dt><dd>{e(cliente.telefone or "—")}</dd></div></dl></section>""")
        return self.pagina(ctx, cliente.nome, "".join(partes), status)

    def cliente_alterar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        valores = self._dados_cliente(req)
        try:
            self.sistema.alterar_cliente(ctx.token, req.parametros["id"], **valores)
        except EntradaInvalida as invalida:
            return self.cliente(req, ctx, invalida.campos, valores, 400)
        return self.ir(f"/clientes/{req.parametros['id']}", "sucesso", "Cliente atualizado.")

    # Auditoria (UC-12)

    def _tabela_auditoria(self, registros, nomes: Dict[str, str], resumida: bool = False) -> str:
        linhas = []
        for r in registros:
            quem = e(nomes.get(r.usuario_id, r.usuario_id)) if r.usuario_id else pg.selo(f"Automática · {r.rotina}", "auto")
            alteracao = ""
            if r.campo:
                antes = e(r.valor_anterior) if r.valor_anterior is not None else "—"
                alteracao = f"<strong>{e(r.campo)}</strong>: {antes} → {e(r.valor_novo) if r.valor_novo is not None else '—'}"
            linha = [e(fmt.data_hora(r.data_hora)), quem, e(r.operacao)]
            if not resumida:
                linha.append(self._link_registro(r.registro_afetado))
            linha += [alteracao, e(r.motivo or "")]
            linhas.append(linha)
        colunas = ["Data e hora", "Usuário", "Operação"] + ([] if resumida else ["Registro"]) + ["Alteração", "Motivo"]
        return pg.tabela(colunas, linhas, "Nenhum registro de auditoria.", "tabela-compacta")

    @staticmethod
    def _link_registro(referencia: str) -> str:
        partes = referencia.replace(",", "").split()
        if len(partes) >= 2 and partes[0] in ("titulo", "cliente", "usuario"):
            destino = {"titulo": "titulos", "cliente": "clientes", "usuario": "usuarios"}[partes[0]]
            rotulo = f"{partes[0]} {partes[1][:8]}" + (f" · pagamento {partes[3][:8]}" if len(partes) >= 4 else "")
            return f'<a href="/{destino}/{e(partes[1])}">{e(rotulo)}</a>'
        return e(referencia)

    def auditoria(self, req: Requisicao, ctx: Contexto) -> Resposta:
        q = req.consulta
        erros = {}
        try:
            de = fmt.ler_data(q.get("de"))
        except fmt.ValorInvalido:
            de, erros["de"] = None, "data inválida"
        try:
            ate = fmt.ler_data(q.get("ate"))
        except fmt.ValorInvalido:
            ate, erros["até"] = None, "data inválida"
        filtro = FiltroAuditoria(usuario_id=q.get("usuario") or None, de=de, ate=ate, operacao=q.get("operacao") or None)
        registros = self.sistema.consultar_auditoria(ctx.token, filtro)
        nomes = self.sistema.nomes_dos_usuarios(ctx.token)
        operacoes = sorted({
            "cadastrar título", "registrar pagamento", "mudar estado", "verificar vencimentos", "estornar pagamento",
            "cancelar título", "cadastrar cliente", "alterar cliente", "cadastrar usuário", "alterar perfil",
            "inativar usuário", "reativar usuário", "alterar permissão",
        })
        filtros = f"""
<form method="get" action="/auditoria" class="filtros cartao">
  {pg.selecao("usuario", "Usuário", sorted(nomes.items(), key=lambda x: x[1].lower()), q.get("usuario", ""), vazio="Todos")}
  {pg.selecao("operacao", "Operação", [(o, o) for o in operacoes], q.get("operacao", ""), vazio="Todas")}
  {pg.entrada("de", "De", q.get("de", ""), "date")}
  {pg.entrada("ate", "Até", q.get("ate", ""), "date")}
  <div class="filtros-acoes"><button class="botao botao-primario">Filtrar</button> <a class="botao botao-leve" href="/auditoria">Limpar</a></div>
</form>"""
        conteudo = (
            pg.cabecalho("Auditoria", "Registro imutável de quem fez o quê e quando. Mostra os 500 mais recentes.")
            + pg.erros_formulario(erros)
            + filtros
            + '<section class="cartao">' + self._tabela_auditoria(registros, nomes) + "</section>"
        )
        return self.pagina(ctx, "Auditoria", conteudo)

    # Usuários e permissões (UC-02, Spec 002)

    def usuarios(self, req: Requisicao, ctx: Contexto) -> Resposta:
        usuarios = self.sistema.acesso.listar_usuarios(ctx.token)
        linhas = [
            [
                f'<a href="/usuarios/{e(u.id)}">{e(u.nome)}</a>',
                e(u.email),
                e(u.perfil.value),
                pg.selo("Ativo", "baixado") if u.ativo else pg.selo("Inativo", "cancelado"),
            ]
            for u in usuarios
        ]
        conteudo = (
            pg.cabecalho("Usuários", "Cada usuário tem exatamente um perfil.", '<a class="botao botao-primario" href="/usuarios/novo">Novo usuário</a>')
            + '<section class="cartao">' + pg.tabela(["Nome", "E-mail", "Perfil", "Situação"], linhas, "Nenhum usuário.") + "</section>"
        )
        return self.pagina(ctx, "Usuários", conteudo)

    def usuario_novo(self, req: Requisicao, ctx: Contexto, erros=None, valores=None, status=200) -> Resposta:
        self.sistema.acesso.autorizar(ctx.token, Operacao.ADMINISTRAR_USUARIOS)
        erros, v = erros or {}, valores or {}
        perfis = [(p.value, p.value) for p in Perfil if p is not Perfil.CLIENTE]
        formulario = f"""
{pg.erros_formulario(erros)}
<form method="post" action="/usuarios/novo" class="cartao formulario">
  {pg.campo_csrf(ctx.csrf)}
  {pg.entrada("nome", "Nome", v.get("nome", ""), "text", erros.get("nome"), True)}
  {pg.entrada("email", "E-mail", v.get("email", ""), "email", erros.get("e-mail"), True, 'autocomplete="off"')}
  <div class="linha">
    {pg.entrada("senha", "Senha inicial", "", "password", erros.get("senha"), True, 'autocomplete="new-password" minlength="8"', "Mínimo de 8 caracteres. Informe-a ao usuário por um canal seguro.")}
    {pg.selecao("perfil", "Perfil", perfis, v.get("perfil", ""), erros.get("perfil"), True, vazio="Selecione")}
  </div>
  <div class="acoes"><button class="botao botao-primario">Cadastrar usuário</button> <a class="botao botao-leve" href="/usuarios">Voltar</a></div>
</form>"""
        return self.pagina(ctx, "Novo usuário", pg.cabecalho("Novo usuário") + formulario, status)

    def usuario_criar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        valores = {k: req.campo(k) for k in ("nome", "email", "perfil")}
        try:
            usuario = self.sistema.acesso.cadastrar_usuario(ctx.token, valores["nome"], valores["email"], req.campo("senha"), valores["perfil"])
        except EntradaInvalida as invalida:
            return self.usuario_novo(req, ctx, invalida.campos, valores, 400)
        return self.ir(f"/usuarios/{usuario.id}", "sucesso", "Usuário cadastrado.")

    def usuario_detalhe(self, req: Requisicao, ctx: Contexto) -> Resposta:
        usuario = self.sistema.acesso.obter_usuario(ctx.token, req.parametros["id"])
        proprio = usuario.id == ctx.usuario.id
        perfis = [(p.value, p.value) for p in Perfil if p is not Perfil.CLIENTE]
        situacao = pg.selo("Ativo", "baixado") if usuario.ativo else pg.selo("Inativo", "cancelado")
        partes = [
            pg.cabecalho(usuario.nome, usuario.email, '<a class="botao botao-leve" href="/usuarios">Voltar</a>'),
            f"""<section class="cartao"><dl class="dados"><div><dt>Perfil</dt><dd>{e(usuario.perfil.value)}</dd></div>
<div><dt>Situação</dt><dd>{situacao}</dd></div></dl></section>""",
        ]
        if proprio:
            partes.append('<div class="aviso aviso-info">Você não pode alterar o perfil nem inativar o próprio usuário.</div>')
        else:
            partes.append(f"""<div class="grade-2">
<section class="cartao"><h2>Alterar perfil</h2>
<form method="post" action="/usuarios/{e(usuario.id)}/perfil" class="formulario">{pg.campo_csrf(ctx.csrf)}
{pg.selecao("perfil", "Novo perfil", perfis, usuario.perfil.value, obrigatorio=True)}
<div class="acoes"><button class="botao botao-primario">Salvar perfil</button></div></form></section>""")
            if usuario.ativo:
                partes.append(f"""<section class="cartao zona-perigo"><h2>Inativar usuário</h2>
<p>As sessões abertas deixam de valer na hora. O histórico na auditoria é preservado.</p>
<form method="post" action="/usuarios/{e(usuario.id)}/inativacao">{pg.campo_csrf(ctx.csrf)}
<button class="botao botao-perigo">Inativar usuário</button></form></section></div>""")
            else:
                partes.append(f"""<section class="cartao"><h2>Reativar usuário</h2>
<form method="post" action="/usuarios/{e(usuario.id)}/reativacao">{pg.campo_csrf(ctx.csrf)}
<button class="botao botao-primario">Reativar usuário</button></form></section></div>""")
        return self.pagina(ctx, usuario.nome, "".join(partes))

    def usuario_perfil(self, req: Requisicao, ctx: Contexto) -> Resposta:
        usuario = self.sistema.acesso.alterar_perfil(ctx.token, req.parametros["id"], req.campo("perfil"))
        return self.ir(f"/usuarios/{usuario.id}", "sucesso", f"Perfil alterado para {usuario.perfil.value}.")

    def usuario_inativar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        self.sistema.acesso.inativar_usuario(ctx.token, req.parametros["id"])
        return self.ir(f"/usuarios/{req.parametros['id']}", "sucesso", "Usuário inativado.")

    def usuario_reativar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        self.sistema.acesso.reativar_usuario(ctx.token, req.parametros["id"])
        return self.ir(f"/usuarios/{req.parametros['id']}", "sucesso", "Usuário reativado.")

    def permissoes(self, req: Requisicao, ctx: Contexto) -> Resposta:
        matriz = self.sistema.acesso.matriz(ctx.token)
        perfis = list(Perfil)
        cabecalho = "".join(f"<th>{e(p.value)}</th>" for p in perfis)
        linhas = []
        for operacao in Operacao:
            celulas = []
            for perfil in perfis:
                marcado = " checked" if operacao in matriz[perfil] else ""
                regra = regra_que_fixa(perfil, operacao)
                nome = f"{perfil.name}:{operacao.name}"
                if regra:
                    celulas.append(
                        f'<td class="fixada" title="Fixada por {e(regra)}"><input type="checkbox" disabled{marcado} aria-label="{e(operacao.value)} — {e(perfil.value)} (fixada por {e(regra)})"><small>{e(regra)}</small></td>'
                    )
                else:
                    celulas.append(f'<td><input type="checkbox" name="permitida" value="{e(nome)}"{marcado} aria-label="{e(operacao.value)} — {e(perfil.value)}"></td>')
            linhas.append(f"<tr><th scope=\"row\">{e(operacao.value)}</th>{''.join(celulas)}</tr>")
        conteudo = (
            pg.cabecalho("Permissões por perfil", "Tudo o que não está marcado é negado. Células cinza são fixadas por regra de negócio.")
            + f"""<form method="post" action="/permissoes" class="cartao">
{pg.campo_csrf(ctx.csrf)}
<div class="tabela-rolagem"><table class="tabela matriz"><thead><tr><th>Operação</th>{cabecalho}</tr></thead><tbody>{''.join(linhas)}</tbody></table></div>
<div class="acoes"><button class="botao botao-primario">Salvar permissões</button></div>
</form>"""
        )
        return self.pagina(ctx, "Permissões", conteudo)

    def permissoes_salvar(self, req: Requisicao, ctx: Contexto) -> Resposta:
        matriz = self.sistema.acesso.matriz(ctx.token)
        marcadas = set(req.campos("permitida"))
        alteradas = 0
        for perfil in Perfil:
            for operacao in Operacao:
                if regra_que_fixa(perfil, operacao):
                    continue
                desejada = f"{perfil.name}:{operacao.name}" in marcadas
                if desejada != (operacao in matriz[perfil]):
                    self.sistema.acesso.alterar_permissao(ctx.token, perfil, operacao, desejada)
                    alteradas += 1
        texto = f"{alteradas} permissão(ões) alterada(s)." if alteradas else "Nenhuma permissão foi alterada."
        return self.ir("/permissoes", "sucesso", texto)
