"""Manipuladores das páginas de fornecedores e contas a pagar (Spec 018). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

import secrets
from typing import Dict, Optional

from remindme.aplicacao.servico_contas_pagar import FiltroContas
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_pagar as pp
from remindme.apresentacao.web.requisicao import (
    Requisicao,
    Resposta,
    _aviso,
    _data_do_filtro,
    _erros,
    _valor_do_formulario,
    _valores,
)
from remindme.dominio.conta_pagar import EstadoContaPagar
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao


class RotasPagar:
    """Rotas de fornecedores e contas a pagar; usa os serviços e os auxiliares de `AplicacaoWeb`."""

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
