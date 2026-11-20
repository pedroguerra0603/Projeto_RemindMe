"""Aplicação WSGI da interface web (Spec 017, ADR-006).

A apresentação recebe a requisição, confere a sessão e a proteção do formulário, chama os serviços da
aplicação e devolve a página. Permissões e regras ficam nos serviços e no domínio (INV-1, DT-06).
"""

import logging
import re
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from typing import Dict, Optional

from remindme.aplicacao.acesso import SessaoInvalida
from remindme.aplicacao.portas import RegistroErro, RegistroErros, Relogio
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_auditoria import FiltroAuditoria, ServicoAuditoria
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_contas_pagar import ServicoContasPagar
from remindme.aplicacao.servico_empresa import ServicoEmpresa
from remindme.aplicacao.servico_fornecedores import ServicoFornecedores
from remindme.aplicacao.servico_mensagens import ServicoMensagens
from remindme.aplicacao.servico_obrigacoes import ServicoObrigacoes
from remindme.aplicacao.servico_orcamentos import ServicoOrcamentos
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.aplicacao.tempo import data_local
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web.requisicao import (
    ARQUIVOS_ESTATICOS,
    COOKIE_SESSAO,
    CorpoGrandeDemais,
    ESTATICO,
    ID,
    Manipulador,
    POLITICA_DE_CONTEUDO,
    Requisicao,
    Resposta,
    _CORRELACAO,
    _confere,
    _sessao_encerrada,
)
from remindme.apresentacao.web.rotas_acesso import RotasAcesso
from remindme.apresentacao.web.rotas_auditoria import RotasAuditoria
from remindme.apresentacao.web.rotas_clientes import RotasClientes
from remindme.apresentacao.web.rotas_empresa import RotasEmpresa
from remindme.apresentacao.web.rotas_obrigacoes import RotasObrigacoes
from remindme.apresentacao.web.rotas_orcamentos import RotasOrcamentos
from remindme.apresentacao.web.rotas_pagar import RotasPagar
from remindme.apresentacao.web.rotas_titulos import RotasTitulos
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao


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
    obrigacoes: Optional[ServicoObrigacoes] = None


class AplicacaoWeb(
    RotasAcesso, RotasAuditoria, RotasClientes, RotasEmpresa, RotasObrigacoes, RotasOrcamentos, RotasPagar, RotasTitulos
):
    """Aplicação WSGI: tabela de rotas, despacho, sessão, cabeçalhos e erros. Os manipuladores de cada módulo ficam nas
    classes `Rotas<Módulo>` (`rotas_<módulo>.py`); a tabela de rotas fica aqui, num só lugar, na ordem em que é testada."""

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
        r.append(("GET", "/obrigacoes", self._obrigacoes, protegida))
        r.append(("GET", "/obrigacoes/nova", self._obrigacao_nova_pagina, protegida))
        r.append(("POST", "/obrigacoes/nova", self._obrigacao_nova, protegida))
        r.append(("GET", f"/obrigacoes/(?P<obrigacao_id>{ID})", self._obrigacao, protegida))
        r.append(("POST", f"/obrigacoes/(?P<obrigacao_id>{ID})/prazo", self._obrigacao_prazo, protegida))
        r.append(("POST", f"/obrigacoes/(?P<obrigacao_id>{ID})/responsavel", self._obrigacao_responsavel, protegida))
        r.append(("POST", f"/obrigacoes/(?P<obrigacao_id>{ID})/cumprimento", self._obrigacao_cumprimento, protegida))
        r.append(("POST", f"/obrigacoes/(?P<obrigacao_id>{ID})/evidencias", self._obrigacao_evidencia, protegida))
        r.append(("GET", f"/obrigacoes/(?P<obrigacao_id>{ID})/evidencias/(?P<evidencia_id>{ID})", self._evidencia, protegida))
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

    # Rotas da própria aplicação: início, ícone, arquivos estáticos e robots

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

    def _robots(self, req: Requisicao) -> Resposta:
        """SEO: só a entrada e a criação de conta são públicas; o resto exige sessão."""
        texto = "User-agent: *\nAllow: /entrar\nAllow: /criar-conta\nDisallow: /\n"
        return Resposta(200, texto.encode("utf-8"), "text/plain; charset=utf-8")

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


