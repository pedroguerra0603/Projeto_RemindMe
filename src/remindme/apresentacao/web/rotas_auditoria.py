"""Manipulador da consulta de auditoria (Specs 013 e 017). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

from typing import Dict

from remindme.aplicacao.servico_auditoria import FiltroAuditoria
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_auditoria as pa
from remindme.apresentacao.web.requisicao import Requisicao, Resposta, _data_do_filtro, _erros
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada


class RotasAuditoria:
    """Rota da auditoria; usa os serviços e os auxiliares de `AplicacaoWeb`."""

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
