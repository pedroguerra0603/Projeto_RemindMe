"""Manipuladores do painel e da página da empresa (Spec 017, OPEN-54). Regras e permissões ficam nos serviços (INV-1, DT-06)."""

from typing import Dict, Optional

from remindme.aplicacao.servico_auditoria import FiltroAuditoria
from remindme.aplicacao.servico_titulos import FiltroTitulos
from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import paginas as p
from remindme.apresentacao.web import paginas_empresa as pem
from remindme.apresentacao.web import paginas_painel as ppa
from remindme.apresentacao.web.requisicao import Requisicao, Resposta, _aviso, _erros, _valores
from remindme.dominio.empresa import CAMPOS as CAMPOS_DA_EMPRESA
from remindme.dominio.erros import OperacaoNegada, OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.usuario import Perfil


class RotasEmpresa:
    """Rotas do painel e da empresa; usa os serviços e os auxiliares de `AplicacaoWeb`."""

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
