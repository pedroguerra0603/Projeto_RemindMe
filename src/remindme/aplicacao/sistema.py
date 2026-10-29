"""Porta de entrada única da aplicação para a interface web.

Toda operação recebe o token da sessão e passa por `ServicoAcesso.autorizar` antes de chegar ao serviço do
caso de uso (Spec 002, INV-2 e INV-5). Nenhuma interface chama os serviços diretamente.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Dict, FrozenSet, List, Optional

from remindme.aplicacao.auditoria import RegistroErrosNoLog
from remindme.aplicacao.portas import (
    FiltroAuditoria,
    RegistroErros,
    Relogio,
    UnidadeDeTrabalhoCompleta,
)
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_titulos import FiltroTitulos, ServicoTitulos, VisaoTitulo
from remindme.dominio.acesso import Operacao
from remindme.dominio.auditoria import RegistroAuditoria
from remindme.dominio.cliente import Cliente
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import ZERO, EstadoTitulo, Titulo
from remindme.dominio.usuario import Usuario

ROTINA_VENCIMENTOS = "verificação de vencimento"


@dataclass(frozen=True)
class Painel:
    """RNF-15 e RNF-17: o que o perfil vê ao entrar, sem navegação adicional."""

    hoje: date
    operacoes: FrozenSet[Operacao]
    vencidos: List[VisaoTitulo] = field(default_factory=list)
    proximos: List[VisaoTitulo] = field(default_factory=list)
    quantidade_abertos: int = 0
    total_a_receber: Decimal = ZERO
    total_vencido: Decimal = ZERO
    recebido_no_mes: Decimal = ZERO
    quantidade_clientes: int = 0
    usuarios_ativos: int = 0


class _ClientesDaTransacao:
    """`ConsultaClientes` sobre a transação aberta pelo serviço de títulos."""

    def __init__(self, uow: UnidadeDeTrabalhoCompleta):
        self._uow = uow

    def existe(self, cliente_id: str) -> bool:
        return self._uow.clientes.existe(cliente_id)


class Sistema:
    def __init__(
        self,
        uow: UnidadeDeTrabalhoCompleta,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        antecedencia_dias: int = 5,
    ):
        erros = erros or RegistroErrosNoLog()
        self._uow = uow
        self._relogio = relogio
        self.antecedencia_dias = antecedencia_dias
        self.acesso = ServicoAcesso(uow, relogio, erros)
        self._titulos = ServicoTitulos(uow, _ClientesDaTransacao(uow), relogio, erros)
        self._clientes = ServicoClientes(uow, relogio, erros)

    def ha_usuarios(self) -> bool:
        with self._uow as uow:
            return bool(uow.usuarios.listar())

    def hoje(self) -> date:
        return self._relogio.agora().date()

    # Painel

    def painel(self, token: Optional[str]) -> Painel:
        usuario = self.acesso.usuario_da_sessao(token)
        operacoes = self.acesso.operacoes_permitidas(usuario.perfil)
        hoje = self.hoje()
        dados = {}
        if Operacao.CONSULTAR_TITULOS in operacoes:
            with self._uow as uow:
                titulos = uow.titulos.listar()
            visoes = self._titulos.consultar_titulos(FiltroTitulos(), hoje, self.antecedencia_dias)
            em_aberto = [v for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)]
            vencidos = [v for v in em_aberto if v.estado is EstadoTitulo.VENCIDO]
            dados.update(
                vencidos=sorted(vencidos, key=lambda v: v.vencimento),
                proximos=sorted((v for v in visoes if v.proximo_do_vencimento), key=lambda v: v.vencimento),
                quantidade_abertos=len(em_aberto),
                total_a_receber=sum((v.saldo for v in em_aberto), ZERO),
                total_vencido=sum((v.saldo for v in vencidos), ZERO),
                recebido_no_mes=sum(
                    (
                        p.valor
                        for t in titulos
                        for p in t.pagamentos
                        if not p.estornado and (p.data.year, p.data.month) == (hoje.year, hoje.month)
                    ),
                    ZERO,
                ),
            )
        if Operacao.MANTER_CLIENTES in operacoes or Operacao.CONSULTAR_TITULOS in operacoes:
            with self._uow as uow:
                dados["quantidade_clientes"] = len(uow.clientes.listar())
        if Operacao.ADMINISTRAR_USUARIOS in operacoes:
            with self._uow as uow:
                dados["usuarios_ativos"] = sum(1 for u in uow.usuarios.listar() if u.ativo)
        return Painel(hoje=hoje, operacoes=operacoes, **dados)

    # Títulos (Spec 006)

    def consultar_titulos(self, token: Optional[str], filtro: FiltroTitulos) -> List[VisaoTitulo]:
        self.acesso.autorizar(token, Operacao.CONSULTAR_TITULOS)
        visoes = self._titulos.consultar_titulos(filtro, self.hoje(), self.antecedencia_dias)
        return sorted(visoes, key=lambda v: (v.vencimento, v.id))

    def obter_titulo(self, token: Optional[str], titulo_id: str) -> Titulo:
        self.acesso.autorizar(token, Operacao.CONSULTAR_TITULOS, Operacao.MANTER_TITULOS)
        with self._uow as uow:
            titulo = uow.titulos.obter(titulo_id)
        if titulo is None:
            raise OperacaoRecusada("Título não encontrado.")
        return titulo

    def cadastrar_titulo(
        self,
        token: Optional[str],
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> Titulo:
        usuario = self.acesso.autorizar(token, Operacao.MANTER_TITULOS)
        return self._titulos.cadastrar_titulo(usuario, cliente_id, valor, vencimento, condicao_pagamento)

    def registrar_pagamento(
        self, token: Optional[str], titulo_id: str, valor: Decimal, data: date
    ) -> Titulo:
        usuario = self.acesso.autorizar(token, Operacao.MANTER_TITULOS)
        return self._titulos.registrar_pagamento(usuario, titulo_id, valor, data)

    def estornar_pagamento(
        self, token: Optional[str], titulo_id: str, pagamento_id: str, motivo: Optional[str]
    ) -> Titulo:
        usuario = self.acesso.autorizar(token, Operacao.ESTORNAR_PAGAMENTO)
        return self._titulos.estornar_pagamento(usuario, titulo_id, pagamento_id, motivo, self.hoje())

    def cancelar_titulo(self, token: Optional[str], titulo_id: str, motivo: Optional[str]) -> Titulo:
        usuario = self.acesso.autorizar(token, Operacao.CANCELAR_TITULO)
        return self._titulos.cancelar_titulo(usuario, titulo_id, motivo)

    def verificar_vencimentos(self, token: Optional[str]) -> List[str]:
        usuario = self.acesso.autorizar(token, Operacao.VERIFICAR_VENCIMENTOS)
        return self._titulos.verificar_vencimentos(usuario, self.hoje())

    def verificar_vencimentos_automaticamente(self) -> List[str]:
        """Entrada do agendador (DT-07): operação automática, sem usuário (OPEN-30)."""
        return self._titulos.verificar_vencimentos(None, self.hoje())

    # Clientes (Spec 003)

    def listar_clientes(self, token: Optional[str], busca: Optional[str] = None) -> List[Cliente]:
        self.acesso.autorizar(token, Operacao.MANTER_CLIENTES, Operacao.CONSULTAR_TITULOS)
        return self._clientes.listar_clientes(busca)

    def obter_cliente(self, token: Optional[str], cliente_id: str) -> Cliente:
        self.acesso.autorizar(token, Operacao.MANTER_CLIENTES, Operacao.CONSULTAR_TITULOS)
        return self._clientes.obter_cliente(cliente_id)

    def cadastrar_cliente(self, token: Optional[str], **dados) -> Cliente:
        usuario = self.acesso.autorizar(token, Operacao.MANTER_CLIENTES)
        return self._clientes.cadastrar_cliente(usuario, **dados)

    def alterar_cliente(self, token: Optional[str], cliente_id: str, **dados) -> Cliente:
        usuario = self.acesso.autorizar(token, Operacao.MANTER_CLIENTES)
        return self._clientes.alterar_cliente(usuario, cliente_id, **dados)

    # Auditoria (UC-12)

    def consultar_auditoria(
        self, token: Optional[str], filtro: FiltroAuditoria, limite: int = 500
    ) -> List[RegistroAuditoria]:
        self.acesso.autorizar(token, Operacao.CONSULTAR_AUDITORIA)
        with self._uow as uow:
            return uow.consulta_auditoria.consultar(filtro, limite)

    def nomes_dos_usuarios(self, token: Optional[str]) -> Dict[str, str]:
        self.acesso.usuario_da_sessao(token)
        return self.acesso.nomes_dos_usuarios()

    def usuario(self, token: Optional[str]) -> Usuario:
        return self.acesso.usuario_da_sessao(token)
