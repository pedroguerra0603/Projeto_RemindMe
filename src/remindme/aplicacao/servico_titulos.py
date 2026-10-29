"""Casos de uso da Spec 006: cadastro manual, pagamento, vencimento, estorno, cancelamento e consulta.

Toda operação recebe a sessão de quem a solicita e passa pela autorização da Spec 002.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import OperacaoAuditada, RegistroErrosNoLog
from remindme.aplicacao.execucao import Execucao
from remindme.aplicacao.portas import ConsultaClientes, RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo, Pagamento, PedidoDePagamentoRepetido, Titulo

# OPEN-37, decidida em 2026-10-23: até a Spec 014, a antecedência de próximo do vencimento é de 5 dias.
ANTECEDENCIA_PADRAO_DIAS = 5
ROTINA_DE_VENCIMENTO = "verificação de vencimento"


@dataclass(frozen=True)
class FiltroTitulos:
    """RF-22. O período filtra pelo vencimento (OPEN-19)."""

    cliente_id: Optional[str] = None
    estado: Optional[EstadoTitulo] = None
    vencimento_de: Optional[date] = None
    vencimento_ate: Optional[date] = None


@dataclass(frozen=True)
class VisaoTitulo:
    """A6: o que a consulta apresenta de cada título."""

    id: str
    cliente_id: str
    valor: Decimal
    saldo: Decimal
    vencimento: date
    estado: EstadoTitulo
    proximo_do_vencimento: bool


class ServicoTitulos:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        clientes: ConsultaClientes,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._uow = uow
        self._clientes = clientes
        self._relogio = relogio
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    def cadastrar_titulo(
        self,
        sessao: Optional[str],
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> Titulo:
        with self._execucao.operacao("cadastrar título", sessao, Operacao.CADASTRAR_TITULO) as op:
            if not isinstance(cliente_id, str) or not self._clientes.existe(cliente_id):
                raise OperacaoRecusada("Cliente inexistente.", {"cliente": "Escolha um cliente cadastrado."})
            titulo = Titulo.cadastrar_manual(
                _novo_id(), cliente_id, valor, vencimento, _texto_opcional(condicao_pagamento)
            )
            op.registrar(_ref(titulo), "estado", None, titulo.estado.value)
            op.uow.titulos.salvar(titulo)
        return titulo

    def registrar_pagamento(
        self,
        sessao: Optional[str],
        titulo_id: str,
        valor: Decimal,
        data: date,
        pedido_id: Optional[str] = None,
    ) -> Titulo:
        """OPEN-25: o pedido repetido é ignorado, e o título é devolvido como está, sem nova auditoria."""
        with self._execucao.operacao("registrar pagamento", sessao, Operacao.REGISTRAR_PAGAMENTO) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            try:
                pagamento = titulo.registrar_pagamento(
                    _novo_id(), valor, data, hoje=data_local(self._relogio.agora()), pedido_id=pedido_id
                )
            except PedidoDePagamentoRepetido:
                return titulo
            op.registrar(_ref(titulo, pagamento.id), "valor", None, str(valor))
            _auditar_estado(op, titulo, estado_anterior)
            op.uow.titulos.salvar(titulo)
        return titulo

    def verificar_vencimentos(self, sessao: Optional[str], data_referencia: date) -> List[str]:
        """A3, solicitada por um usuário."""
        with self._execucao.operacao("verificar vencimentos", sessao, Operacao.VERIFICAR_VENCIMENTOS) as op:
            return self._marcar_vencidos(op, data_referencia)

    def verificar_vencimentos_automaticamente(self, data_referencia: date) -> List[str]:
        """A3, disparada pelo agendador, sem usuário (Spec 001, A4; OPEN-13)."""
        with self._execucao.automatica("verificar vencimentos", ROTINA_DE_VENCIMENTO) as op:
            return self._marcar_vencidos(op, data_referencia)

    def estornar_pagamento(
        self,
        sessao: Optional[str],
        titulo_id: str,
        pagamento_id: str,
        motivo: Optional[str],
        data_referencia: date,
    ) -> Titulo:
        with self._execucao.operacao("estornar pagamento", sessao, Operacao.ESTORNAR_PAGAMENTO) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.estornar_pagamento(pagamento_id, motivo, data_referencia)
            op.registrar(_ref(titulo, pagamento_id), "estornado", "não", "sim", motivo)
            _auditar_estado(op, titulo, estado_anterior, motivo)
            op.uow.titulos.salvar(titulo)
        return titulo

    def cancelar_titulo(self, sessao: Optional[str], titulo_id: str, motivo: Optional[str]) -> Titulo:
        with self._execucao.operacao("cancelar título", sessao, Operacao.CANCELAR_TITULO) as op:
            titulo = self._obter(titulo_id)
            estado_anterior = titulo.estado
            titulo.cancelar(motivo)
            _auditar_estado(op, titulo, estado_anterior, motivo)
            op.uow.titulos.salvar(titulo)
        return titulo

    def consultar_titulos(
        self,
        sessao: Optional[str],
        filtro: FiltroTitulos,
        data_referencia: date,
        antecedencia_dias: int = ANTECEDENCIA_PADRAO_DIAS,
    ) -> List[VisaoTitulo]:
        """A6. A antecedência vem da configuração (Spec 014); até lá, OPEN-37."""
        with self._execucao.operacao("consultar títulos", sessao, Operacao.CONSULTAR_TITULOS) as op:
            titulos = op.uow.titulos.listar()
        return [
            VisaoTitulo(
                id=t.id,
                cliente_id=t.cliente_id,
                valor=t.valor,
                saldo=t.saldo,
                vencimento=t.vencimento,
                estado=t.estado,
                proximo_do_vencimento=t.proximo_do_vencimento(data_referencia, antecedencia_dias),
            )
            for t in sorted(titulos, key=lambda t: (t.vencimento, t.id))
            if _atende(t, filtro)
        ]

    def pagamentos_recebidos(self, sessao: Optional[str]) -> List[Pagamento]:
        """Os pagamentos não estornados de todos os títulos, para o gráfico de recebimento do painel."""
        with self._execucao.operacao("consultar títulos", sessao, Operacao.CONSULTAR_TITULOS) as op:
            return [p for t in op.uow.titulos.listar() for p in t.pagamentos if not p.estornado]

    def obter_titulo(self, sessao: Optional[str], titulo_id: str) -> Titulo:
        """O título com seus pagamentos, para a tela do título (RNF-16)."""
        with self._execucao.operacao("consultar títulos", sessao, Operacao.CONSULTAR_TITULOS):
            return self._obter(titulo_id)

    def _marcar_vencidos(self, op: OperacaoAuditada, data_referencia: date) -> List[str]:
        vencidos = []
        for titulo in op.uow.titulos.listar():
            if titulo.marcar_vencido(data_referencia):
                _auditar_estado(op, titulo, EstadoTitulo.ABERTO)
                op.uow.titulos.salvar(titulo)
                vencidos.append(titulo.id)
        return vencidos

    def _obter(self, titulo_id: str) -> Titulo:
        titulo = self._uow.titulos.obter(titulo_id) if isinstance(titulo_id, str) else None
        if titulo is None:
            raise OperacaoRecusada("Título não encontrado.")
        return titulo


def _atende(titulo: Titulo, filtro: FiltroTitulos) -> bool:
    return (
        (filtro.cliente_id is None or titulo.cliente_id == filtro.cliente_id)
        and (filtro.estado is None or titulo.estado is filtro.estado)
        and (filtro.vencimento_de is None or titulo.vencimento >= filtro.vencimento_de)
        and (filtro.vencimento_ate is None or titulo.vencimento <= filtro.vencimento_ate)
    )


def _auditar_estado(
    op: OperacaoAuditada, titulo: Titulo, anterior: EstadoTitulo, motivo: Optional[str] = None
) -> None:
    if titulo.estado is not anterior:
        op.registrar(
            _ref(titulo), "estado", anterior.value, titulo.estado.value, motivo, operacao="mudar estado"
        )


def _ref(titulo: Titulo, pagamento_id: Optional[str] = None) -> str:
    """O pagamento existe dentro do título, e a referência nomeia os dois (Spec 006, CA-22)."""
    if pagamento_id is None:
        return f"titulo {titulo.id}"
    return f"titulo {titulo.id}, pagamento {pagamento_id}"


def _texto_opcional(texto: Optional[str]) -> Optional[str]:
    if not isinstance(texto, str):
        return None
    return texto.strip() or None


def _novo_id() -> str:
    return uuid.uuid4().hex
