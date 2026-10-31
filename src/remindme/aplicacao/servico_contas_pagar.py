"""Casos de uso da Spec 018: conta a pagar, pagamento, vencimento, estorno, cancelamento e consulta (UC-15).

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
from remindme.aplicacao.portas import RegistroErros, Relogio, UnidadeDeTrabalho
from remindme.aplicacao.tempo import data_local
from remindme.dominio.conta_pagar import ContaPagar, EstadoContaPagar
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import PedidoDePagamentoRepetido

ROTINA_DE_VENCIMENTO = "verificação de vencimento"


@dataclass(frozen=True)
class FiltroContas:
    """RF-89. O período filtra pelo vencimento, como nos títulos (OPEN-19)."""

    fornecedor_id: Optional[str] = None
    estado: Optional[EstadoContaPagar] = None
    vencimento_de: Optional[date] = None
    vencimento_ate: Optional[date] = None


@dataclass(frozen=True)
class VisaoConta:
    """A5: o que a consulta apresenta de cada conta."""

    id: str
    fornecedor_id: str
    descricao: str
    valor: Decimal
    saldo: Decimal
    vencimento: date
    estado: EstadoContaPagar


class ServicoContasPagar:
    def __init__(
        self,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        erros: Optional[RegistroErros] = None,
        autorizacao: Optional[Autorizacao] = None,
    ):
        self._relogio = relogio
        self._execucao = Execucao(
            uow, relogio, erros or RegistroErrosNoLog(), autorizacao or Autorizacao(relogio)
        )

    def cadastrar_conta(
        self,
        sessao: Optional[str],
        fornecedor_id: str,
        descricao: object,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> ContaPagar:
        """RF-88."""
        with self._execucao.operacao("cadastrar conta a pagar", sessao, Operacao.CADASTRAR_CONTA_PAGAR) as op:
            if not isinstance(fornecedor_id, str) or not op.uow.fornecedores.existe(fornecedor_id):
                raise OperacaoRecusada("Fornecedor inexistente.", {"fornecedor": "Escolha um fornecedor cadastrado."})
            conta = ContaPagar.cadastrar(
                _novo_id(), fornecedor_id, descricao, valor, vencimento, _texto_opcional(condicao_pagamento)
            )
            op.registrar(_ref(conta), "estado", None, conta.estado.value)
            op.uow.contas_pagar.salvar(conta)
        return conta

    def registrar_pagamento(
        self, sessao: Optional[str], conta_id: str, valor: Decimal, data: date, pedido_id: Optional[str] = None
    ) -> ContaPagar:
        """RF-91. OPEN-25: o pedido repetido é ignorado, e a conta é devolvida como está, sem nova auditoria."""
        with self._execucao.operacao("registrar pagamento de conta", sessao, Operacao.PAGAR_CONTA) as op:
            conta = _obter(op, conta_id)
            anterior = conta.estado
            try:
                pagamento = conta.registrar_pagamento(
                    _novo_id(), valor, data, hoje=data_local(self._relogio.agora()), pedido_id=pedido_id
                )
            except PedidoDePagamentoRepetido:
                return conta
            op.registrar(_ref(conta, pagamento.id), "valor", None, str(valor))
            _auditar_estado(op, conta, anterior)
            op.uow.contas_pagar.salvar(conta)
        return conta

    def estornar_pagamento(
        self, sessao: Optional[str], conta_id: str, pagamento_id: str, motivo: Optional[str], data_referencia: date
    ) -> ContaPagar:
        """RF-92, RB-33."""
        with self._execucao.operacao("estornar pagamento de conta", sessao, Operacao.ESTORNAR_PAGAMENTO_CONTA) as op:
            conta = _obter(op, conta_id)
            anterior = conta.estado
            conta.estornar_pagamento(pagamento_id, motivo, data_referencia)
            op.registrar(_ref(conta, pagamento_id), "estornado", "não", "sim", motivo)
            _auditar_estado(op, conta, anterior, motivo)
            op.uow.contas_pagar.salvar(conta)
        return conta

    def cancelar_conta(self, sessao: Optional[str], conta_id: str, motivo: Optional[str]) -> ContaPagar:
        """RF-93, RB-33."""
        with self._execucao.operacao("cancelar conta a pagar", sessao, Operacao.CANCELAR_CONTA_PAGAR) as op:
            conta = _obter(op, conta_id)
            anterior = conta.estado
            conta.cancelar(motivo)
            _auditar_estado(op, conta, anterior, motivo)
            op.uow.contas_pagar.salvar(conta)
        return conta

    def verificar_vencimentos_automaticamente(self, data_referencia: date) -> List[str]:
        """RF-90, pelo agendador, sem usuário (Spec 001, A4; OPEN-13)."""
        with self._execucao.automatica("verificar vencimentos de contas", ROTINA_DE_VENCIMENTO) as op:
            vencidas = []
            for conta in op.uow.contas_pagar.listar():
                if conta.marcar_vencida(data_referencia):
                    _auditar_estado(op, conta, EstadoContaPagar.ABERTA)
                    op.uow.contas_pagar.salvar(conta)
                    vencidas.append(conta.id)
            return vencidas

    def consultar_contas(self, sessao: Optional[str], filtro: FiltroContas = FiltroContas()) -> List[VisaoConta]:
        """RF-89, ordenadas por vencimento."""
        with self._execucao.operacao("consultar contas a pagar", sessao, Operacao.CONSULTAR_CONTAS_PAGAR) as op:
            contas = op.uow.contas_pagar.listar()
        return [
            VisaoConta(c.id, c.fornecedor_id, c.descricao, c.valor, c.saldo, c.vencimento, c.estado)
            for c in sorted(contas, key=lambda c: (c.vencimento, c.id))
            if _atende(c, filtro)
        ]

    def obter_conta(self, sessao: Optional[str], conta_id: str) -> ContaPagar:
        """A conta com seus pagamentos, para a tela da conta."""
        with self._execucao.operacao("consultar contas a pagar", sessao, Operacao.CONSULTAR_CONTAS_PAGAR) as op:
            return _obter(op, conta_id)


def _atende(conta: ContaPagar, filtro: FiltroContas) -> bool:
    return (
        (filtro.fornecedor_id is None or conta.fornecedor_id == filtro.fornecedor_id)
        and (filtro.estado is None or conta.estado is filtro.estado)
        and (filtro.vencimento_de is None or conta.vencimento >= filtro.vencimento_de)
        and (filtro.vencimento_ate is None or conta.vencimento <= filtro.vencimento_ate)
    )


def _obter(op: OperacaoAuditada, conta_id: str) -> ContaPagar:
    conta = op.uow.contas_pagar.obter(conta_id) if isinstance(conta_id, str) else None
    if conta is None:
        raise OperacaoRecusada("Conta a pagar não encontrada.")
    return conta


def _auditar_estado(
    op: OperacaoAuditada, conta: ContaPagar, anterior: EstadoContaPagar, motivo: Optional[str] = None
) -> None:
    if conta.estado is not anterior:
        op.registrar(_ref(conta), "estado", anterior.value, conta.estado.value, motivo, operacao="mudar estado")


def _ref(conta: ContaPagar, pagamento_id: Optional[str] = None) -> str:
    """O pagamento existe dentro da conta, e a referência nomeia os dois, como no título."""
    if pagamento_id is None:
        return f"conta_pagar {conta.id}"
    return f"conta_pagar {conta.id}, pagamento {pagamento_id}"


def _texto_opcional(texto: Optional[str]) -> Optional[str]:
    if not isinstance(texto, str):
        return None
    return texto.strip() or None


def _novo_id() -> str:
    return uuid.uuid4().hex
