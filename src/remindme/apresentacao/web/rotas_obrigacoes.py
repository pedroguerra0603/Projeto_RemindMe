"""Manipuladores do calendário de obrigações (Spec 010). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

from typing import Dict, Optional
from urllib.parse import quote

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_obrigacoes as po
from remindme.apresentacao.web.requisicao import Requisicao, Resposta, _aviso, _erros, _valores
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.obrigacao import ArquivoDeEvidencia, EstadoObrigacao
from remindme.dominio.operacoes import Operacao


class RotasObrigacoes:
    """Rotas das obrigações; usa os serviços e os auxiliares de `AplicacaoWeb`."""

    def _nomes_para_obrigacoes(self, sessao: str, ctx: p.Contexto) -> Dict[str, str]:
        if not self._s.obrigacoes or not ctx.pode(Operacao.GERENCIAR_OBRIGACOES):
            return {}
        return self._s.obrigacoes.nomes_dos_usuarios(sessao)

    def _obrigacoes(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        filtro = req.consulta.get("estado", "")
        visoes = self._s.obrigacoes.consultar_calendario(sessao)
        if filtro in EstadoObrigacao.__members__:
            visoes = [v for v in visoes if v.estado is EstadoObrigacao[filtro]]
        elif filtro != "todas":
            filtro = ""
            visoes = [v for v in visoes if v.estado is not EstadoObrigacao.CUMPRIDA]
        return Resposta.pagina(po.pagina_calendario(ctx, visoes, filtro, _aviso(req)))

    def _obrigacao_nova_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        responsaveis = self._s.obrigacoes.responsaveis_possiveis(sessao)
        valores = {"responsavel": ctx.usuario.id, "exige_evidencia": "nao"}
        return Resposta.pagina(po.pagina_obrigacao_formulario(ctx, responsaveis, valores, {}))

    def _obrigacao_nova(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "tipo", "periodicidade", "prazo", "responsavel", "exige_evidencia")
        erros: Dict[str, str] = {}
        prazo = f.ler_data(valores["prazo"]) if valores["prazo"] else None
        if valores["prazo"] and prazo is None:
            erros["prazo"] = "Informe uma data válida."
        try:
            obrigacao = self._s.obrigacoes.cadastrar_obrigacao(
                sessao, valores["nome"], valores["tipo"], valores["periodicidade"], prazo, valores["responsavel"],
                valores["exige_evidencia"] == "sim",
            )
            if not erros:
                return Resposta.redirecionar(f"/obrigacoes/{obrigacao.id}?aviso=obrigacao")
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            erros = {**_erros(recusa), **erros}
        responsaveis = self._s.obrigacoes.responsaveis_possiveis(sessao)
        return Resposta.pagina(po.pagina_obrigacao_formulario(ctx, responsaveis, valores, erros), 400)

    def _obrigacao(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None, formulario: str = "",
    ) -> Resposta:
        servico = self._s.obrigacoes
        obrigacao = servico.obter_obrigacao(sessao, obrigacao_id)
        responsaveis = servico.responsaveis_possiveis(sessao)
        pagina = po.pagina_obrigacao(
            ctx, obrigacao, servico.ocorrencias_da_serie(sessao, obrigacao.serie), servico.nomes_dos_usuarios(sessao),
            responsaveis, any(u.id == obrigacao.responsavel_id for u in responsaveis), valores or {}, erros or {},
            formulario, None if erros else _aviso(req),
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _obrigacao_prazo(self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str) -> Resposta:
        valores = _valores(req, "prazo")
        prazo = f.ler_data(valores["prazo"]) if valores["prazo"] else None
        try:
            if valores["prazo"] and prazo is None:
                raise OperacaoRecusada("Informe uma data válida.", {"prazo": "Informe uma data válida."})
            self._s.obrigacoes.alterar_prazo(sessao, obrigacao_id, prazo)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._obrigacao(req, sessao, ctx, obrigacao_id, valores, _erros(recusa), "prazo")
        return Resposta.redirecionar(f"/obrigacoes/{obrigacao_id}?aviso=obrigacao-alterada")

    def _obrigacao_responsavel(self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str) -> Resposta:
        valores = _valores(req, "responsavel")
        try:
            self._s.obrigacoes.alterar_responsavel(sessao, obrigacao_id, valores["responsavel"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._obrigacao(req, sessao, ctx, obrigacao_id, valores, _erros(recusa), "responsavel")
        return Resposta.redirecionar(f"/obrigacoes/{obrigacao_id}?aviso=obrigacao-alterada")

    def _obrigacao_cumprimento(self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str) -> Resposta:
        valores = _valores(req, "data", "descricao")
        data = f.ler_data(valores["data"]) if valores["data"] else None
        enviado = req.arquivos.get("arquivo")
        arquivo = ArquivoDeEvidencia(enviado.nome, enviado.conteudo) if enviado else None
        try:
            if valores["data"] and data is None:
                raise OperacaoRecusada("Informe uma data válida.", {"data": "Informe uma data válida."})
            obrigacao = self._s.obrigacoes.registrar_cumprimento(sessao, obrigacao_id, data, arquivo, valores["descricao"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._obrigacao(req, sessao, ctx, obrigacao_id, valores, _erros(recusa), "cumprimento")
        aviso = "cumprimento-sem-evidencia" if obrigacao.aguarda_evidencia else "cumprimento"
        return Resposta.redirecionar(f"/obrigacoes/{obrigacao_id}?aviso={aviso}")

    def _obrigacao_evidencia(self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str) -> Resposta:
        valores = _valores(req, "descricao")
        enviado = req.arquivos.get("arquivo")
        try:
            if enviado is None:
                raise OperacaoRecusada("Escolha o arquivo da evidência.", {"arquivo": "Escolha o arquivo da evidência."})
            self._s.obrigacoes.anexar_evidencia(
                sessao, obrigacao_id, ArquivoDeEvidencia(enviado.nome, enviado.conteudo), valores["descricao"]
            )
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._obrigacao(req, sessao, ctx, obrigacao_id, valores, _erros(recusa), "evidencia")
        return Resposta.redirecionar(f"/obrigacoes/{obrigacao_id}?aviso=evidencia")

    def _evidencia(self, req: Requisicao, sessao: str, ctx: p.Contexto, obrigacao_id: str, evidencia_id: str) -> Resposta:
        """Foco de revisão 1: sempre como anexo, com o tipo conferido no upload e o nome em UTF-8."""
        evidencia, conteudo = self._s.obrigacoes.conteudo_da_evidencia(sessao, obrigacao_id, evidencia_id)
        resposta = Resposta(200, conteudo, evidencia.tipo_arquivo)
        simples = "".join(c if c.isascii() and c.isprintable() and c not in '"\\;' else "_" for c in evidencia.nome_arquivo)
        resposta.cabecalhos.append(
            ("Content-Disposition", f"attachment; filename=\"{simples}\"; filename*=UTF-8''{quote(evidencia.nome_arquivo, safe='')}")
        )
        return resposta
