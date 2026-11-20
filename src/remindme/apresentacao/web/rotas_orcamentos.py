"""Manipuladores das páginas de orçamentos: itens, desconto, decisão, envio, resposta do cliente e mensagens enviadas (Specs 004 e 005). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

from typing import Dict, Optional

from remindme.aplicacao.servico_orcamentos import FiltroOrcamentos
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_mensagens as pm
from remindme.apresentacao.web import paginas_orcamentos as po
from remindme.apresentacao.web.requisicao import (
    Requisicao,
    Resposta,
    _aviso,
    _data_do_filtro,
    _erros,
    _numero_do_formulario,
    _valores,
)
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento


class RotasOrcamentos:
    """Rotas de orçamentos e mensagens; usa os serviços e os auxiliares de `AplicacaoWeb`."""

    def _orcamentos(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = {chave: req.consulta.get(chave, "").strip() for chave in ("cliente", "estado", "de", "ate")}
        erros: Dict[str, str] = {}
        de = _data_do_filtro(valores, "de", erros)
        ate = _data_do_filtro(valores, "ate", erros)
        estado = EstadoOrcamento[valores["estado"]] if valores["estado"] in EstadoOrcamento.__members__ else None
        filtro = FiltroOrcamentos(cliente_id=valores["cliente"] or None, estado=estado, criado_de=de, criado_ate=ate)
        orcamentos = self._s.orcamentos.consultar_orcamentos(sessao, filtro)
        pagina = po.pagina_orcamentos(ctx, orcamentos, self._nomes_clientes(sessao, ctx), valores, erros, _aviso(req))
        return Resposta.pagina(pagina)

    def _orcamento_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.CONDUZIR_ORCAMENTO)
        valores = {"cliente": req.consulta.get("cliente", "")}
        return Resposta.pagina(po.pagina_orcamento_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, {}))

    def _orcamento_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "cliente", "condicao")
        try:
            orcamento = self._s.orcamentos.criar_orcamento(sessao, valores["cliente"], valores["condicao"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            pagina = po.pagina_orcamento_formulario(ctx, self._nomes_clientes(sessao, ctx), valores, _erros(recusa))
            return Resposta.pagina(pagina, 400)
        return Resposta.redirecionar(f"/orcamentos/{orcamento.id}?aviso=orcamento")

    def _orcamento(
        self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str,
        formulario: str = "", valores: Optional[Dict[str, str]] = None, erros: Optional[Dict[str, str]] = None,
    ) -> Resposta:
        orcamento = self._s.orcamentos.obter_orcamento(sessao, orcamento_id)
        nomes = self._nomes_clientes(sessao, ctx)
        pagina = po.pagina_orcamento(
            ctx,
            orcamento,
            nomes.get(orcamento.cliente_id, "Cliente"),
            self._nomes_usuarios(sessao, ctx),
            formulario,
            valores or {},
            erros or {},
            self._historico(sessao, ctx, f"orcamento {orcamento.id}"),
            None if erros else _aviso(req),
            self._mensagens_de(sessao, ctx, f"orcamento {orcamento.id}"),
        )
        return Resposta.pagina(pagina, 400 if erros else 200)

    def _mensagens_de(self, sessao: str, ctx: p.Contexto, origem: str) -> Optional[list]:
        """Spec 005: os envios deste registro, para quem pode ver a caixa de saída."""
        if not self._s.mensagens or not ctx.pode(Operacao.CONSULTAR_MENSAGENS):
            return None
        return [m for m in self._s.mensagens.consultar(sessao) if m.origem == origem]

    def _envio(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        """RF-08. Se o canal falhar, a recusa aparece na página e a tentativa fica na caixa de saída (E2)."""
        try:
            self._s.orcamentos.enviar_orcamento(sessao, orcamento_id)
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return self._orcamento(req, sessao, ctx, orcamento_id, "envio", {}, {"_": recusa.motivo})
        return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso=orcamento-enviado")

    def _resposta_do_cliente(self, req: Requisicao, sessao: str, ctx: p.Contexto, orcamento_id: str) -> Resposta:
        """RF-09 (OPEN-57): o usuário registra o que o cliente decidiu; a aprovação gera o título (RF-11)."""
        valores = _valores(req, "decisao", "data", "motivo")
        erros: Dict[str, str] = {}
        if valores["decisao"] not in ("aprovar", "rejeitar"):
            erros["_"] = "Escolha registrar a aprovação ou a rejeição."
        data = f.ler_data(valores["data"]) if valores["data"] else None
        if valores["data"] and data is None:
            erros["data"] = "Informe uma data válida."
        if not erros:
            aprovado = valores["decisao"] == "aprovar"
            try:
                self._s.orcamentos.registrar_decisao_do_cliente(sessao, orcamento_id, aprovado, data, valores["motivo"])
                aviso = "orcamento-convertido" if aprovado else "orcamento-rejeitado"
                return Resposta.redirecionar(f"/orcamentos/{orcamento_id}?aviso={aviso}")
            except OperacaoNegada:
                raise
            except OperacaoRecusada as recusa:
                erros = _erros(recusa)
        return self._orcamento(req, sessao, ctx, orcamento_id, "resposta", valores, erros)

    def _mensagens(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        mensagens = self._s.mensagens.consultar(sessao)
        usuarios = self._nomes_para_obrigacoes(sessao, ctx)  # Spec 010: destinatário dos alertas
        return Resposta.pagina(pm.pagina_mensagens(ctx, mensagens, self._nomes_clientes(sessao, ctx), usuarios))

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
        return Resposta.pagina(po.pagina_item_formulario(ctx, orcamento, item, valores, erros or {}), 400 if erros else 200)

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
        """Prazo para pagamento (OPEN-61) e condição. O prazo vem primeiro: inválido, nada é gravado."""
        valores = _valores(req, "condicao", "prazo")
        try:
            self._s.orcamentos.alterar_prazo(sessao, orcamento_id, valores["prazo"])
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
