"""Manipuladores das páginas de clientes (Specs 003 e 017). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

from remindme.aplicacao.servico_titulos import FiltroTitulos
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_clientes as pc
from remindme.apresentacao.web.requisicao import Requisicao, Resposta, _aviso, _erros, _valores
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao


class RotasClientes:
    """Rotas de clientes; usa os serviços e os auxiliares de `AplicacaoWeb`."""

    def _clientes(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        termo = req.consulta.get("q", "").strip()
        clientes = self._s.clientes.consultar_clientes(sessao, termo)
        return Resposta.pagina(pc.pagina_clientes(ctx, clientes, termo, _aviso(req)))

    def _cliente_novo_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_CLIENTES)
        return Resposta.pagina(pc.pagina_cliente_formulario(ctx, {}, {}))

    def _cliente_novo(self, req: Requisicao, sessao: str, ctx: p.Contexto) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            cliente = self._s.clientes.cadastrar_cliente(sessao, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(pc.pagina_cliente_formulario(ctx, valores, _erros(recusa)), 400)
        return Resposta.redirecionar(f"/clientes/{cliente.id}?aviso=cliente")

    def _cliente(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        cliente = self._s.clientes.obter_cliente(sessao, cliente_id)
        visoes = (
            self._s.titulos.consultar_titulos(sessao, FiltroTitulos(cliente_id=cliente.id), ctx.hoje)
            if ctx.pode(Operacao.CONSULTAR_TITULOS)
            else []
        )
        historico = self._historico(sessao, ctx, f"cliente {cliente.id}")
        return Resposta.pagina(pc.pagina_cliente(ctx, cliente, visoes, historico, _aviso(req)))

    def _cliente_editar_pagina(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        self._s.acesso.exigir(sessao, Operacao.MANTER_CLIENTES)
        cliente = self._s.clientes.obter_cliente(sessao, cliente_id)
        valores = {"nome": cliente.nome, "documento": f.documento(cliente.documento), "contato": f.contato(cliente.contato)}
        return Resposta.pagina(pc.pagina_cliente_formulario(ctx, valores, {}, cliente.id))

    def _cliente_editar(self, req: Requisicao, sessao: str, ctx: p.Contexto, cliente_id: str) -> Resposta:
        valores = _valores(req, "nome", "documento", "contato")
        try:
            self._s.clientes.alterar_cliente(sessao, cliente_id, valores["nome"], valores["documento"], valores["contato"])
        except OperacaoNegada:
            raise
        except OperacaoRecusada as recusa:
            return Resposta.pagina(pc.pagina_cliente_formulario(ctx, valores, _erros(recusa), cliente_id), 400)
        return Resposta.redirecionar(f"/clientes/{cliente_id}?aviso=cliente-alterado")
