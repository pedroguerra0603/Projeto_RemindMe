"""Manipuladores das páginas de títulos: cadastro, pagamento, estorno, cancelamento e verificação de vencimentos (Specs 006 e 017). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

import secrets
from typing import Dict, Optional
from urllib.parse import urlencode

from remindme.aplicacao.servico_titulos import ANTECEDENCIA_PADRAO_DIAS, FiltroTitulos
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_titulos as pt
from remindme.apresentacao.web.requisicao import (
    Requisicao,
    Resposta,
    _aviso,
    _data_do_filtro,
    _erros,
    _valor_do_formulario,
    _valores,
)
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo


class RotasTitulos:
    """Rotas de títulos; usa os serviços e os auxiliares de `AplicacaoWeb`."""

    def _titulos(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("cliente", "estado", "de", "ate")}
        erros: Dict[str, str] = {}
        de = _data_do_filtro(valores, "de", erros)
        ate = _data_do_filtro(valores, "ate", erros)
        estado = EstadoTitulo[valores["estado"]] if valores["estado"] in EstadoTitulo.__members__ else None
        filtro = FiltroTitulos(cliente_id=valores["cliente"] or None, estado=estado, vencimento_de=de, vencimento_ate=ate)
        visoes = self._s.titulos.consultar_titulos(sessao, filtro, ctx.hoje)
        pagina = pt.pagina_titulos(ctx, visoes, self._nomes_clientes(sessao, ctx), valores, erros, _aviso(req))
        return Resposta.pagina(pagina)

    def _titulo_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CADASTRAR_TITULO)
        valores = {"cliente": req.consulta.get("cliente", "")}
        return Resposta.pagina(pt.pagina_titulo_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, {}))

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
        return Resposta.pagina(pt.pagina_titulo_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, erros), 400)

    def _titulo(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, titulo_id: str,
        valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None, pedido: str = "",
    ) -> Resposta:
        titulo = self._s.titulos.obter_titulo(sessao, titulo_id)
        nomes = self._nomes_clientes(sessao, ctx)
        pagina = pt.pagina_titulo(
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
