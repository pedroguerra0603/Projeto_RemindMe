"""Título a receber e seus pagamentos. Regras RB-21, RB-22 e RB-23."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from remindme.dominio.erros import OperacaoRecusada

ZERO = Decimal("0.00")


class EstadoTitulo(Enum):
    # Em Renegociação (RB-21) entra com a Spec 009.
    ABERTO = "Aberto"
    VENCIDO = "Vencido"
    BAIXADO = "Baixado"
    CANCELADO = "Cancelado"


ESTADOS_QUE_ACEITAM_PAGAMENTO = (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)
ESTADOS_QUE_ACEITAM_CANCELAMENTO = (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)


@dataclass
class Pagamento:
    id: str
    valor: Decimal
    data: date
    estornado: bool = False
    motivo_estorno: Optional[str] = None


@dataclass
class Titulo:
    id: str
    cliente_id: str
    valor: Decimal
    vencimento: date
    origem: str
    condicao_pagamento: Optional[str]
    estado: EstadoTitulo
    pagamentos: List[Pagamento] = field(default_factory=list)

    @classmethod
    def cadastrar_manual(
        cls,
        id: str,
        cliente_id: str,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> "Titulo":
        """RF-20, RF-21: o título nasce Aberto, com origem manual e saldo igual ao valor."""
        if vencimento is None:
            raise OperacaoRecusada("O vencimento é obrigatório.")
        _exigir_decimal(valor, "O valor do título deve ser um número decimal finito.")
        if valor <= ZERO:
            raise OperacaoRecusada("O valor do título deve ser maior que zero.")
        return cls(
            id=id,
            cliente_id=cliente_id,
            valor=valor,
            vencimento=vencimento,
            origem="manual",
            condicao_pagamento=condicao_pagamento,
            estado=EstadoTitulo.ABERTO,
        )

    @property
    def saldo(self) -> Decimal:
        """Valor do título menos a soma dos pagamentos não estornados (INV-1)."""
        pago = sum((p.valor for p in self.pagamentos if not p.estornado), ZERO)
        return self.valor - pago

    def registrar_pagamento(self, pagamento_id: str, valor: Decimal, data: date) -> Pagamento:
        """RF-25, RF-26, RF-27. RB-21: só Aberto ou Vencido aceita pagamento. RB-23: 0 < valor <= saldo."""
        if self.estado not in ESTADOS_QUE_ACEITAM_PAGAMENTO:
            raise OperacaoRecusada(
                f"Título {self.estado.value} não aceita pagamento (RB-21)."
            )
        _exigir_decimal(valor, "O valor do pagamento deve ser um número decimal finito (RB-23).")
        if valor <= ZERO:
            raise OperacaoRecusada("O valor do pagamento deve ser maior que zero (RB-23).")
        if valor > self.saldo:
            raise OperacaoRecusada(
                f"O valor do pagamento é maior que o saldo de {self.saldo} (RB-23)."
            )
        pagamento = Pagamento(id=pagamento_id, valor=valor, data=data)
        self.pagamentos.append(pagamento)
        # RB-22: Baixado se, e somente se, o saldo é zero.
        if self.saldo == ZERO:
            self.estado = EstadoTitulo.BAIXADO
        return pagamento

    def marcar_vencido(self, data_referencia: date) -> bool:
        """RF-24: Aberto com vencimento anterior à data de referência passa a Vencido."""
        if self.estado is EstadoTitulo.ABERTO and self.vencimento < data_referencia:
            self.estado = EstadoTitulo.VENCIDO
            return True
        return False

    def estornar_pagamento(self, pagamento_id: str, motivo: Optional[str], data_referencia: date) -> Pagamento:
        """RF-30. A permissão (RB-02) é verificada antes, pela camada de aplicação."""
        _exigir_motivo(motivo, "estorno")
        if self.estado is EstadoTitulo.CANCELADO:
            # Comportamento provisório: OPEN-18.
            raise OperacaoRecusada("Título Cancelado não aceita estorno (OPEN-18).")
        pagamento = self._pagamento(pagamento_id)
        if pagamento.estornado:
            raise OperacaoRecusada("O pagamento já foi estornado.")
        pagamento.estornado = True
        pagamento.motivo_estorno = motivo
        if self.estado is EstadoTitulo.BAIXADO:
            self.estado = (
                EstadoTitulo.ABERTO
                if self.vencimento >= data_referencia
                else EstadoTitulo.VENCIDO
            )
        return pagamento

    def cancelar(self, motivo: Optional[str]) -> None:
        """RF-31. RB-21: só Aberto ou Vencido pode ser cancelado."""
        _exigir_motivo(motivo, "cancelamento")
        if self.estado not in ESTADOS_QUE_ACEITAM_CANCELAMENTO:
            raise OperacaoRecusada(
                f"Título {self.estado.value} não pode ser cancelado (RB-21)."
                + (" Estorne os pagamentos antes." if self.estado is EstadoTitulo.BAIXADO else "")
            )
        self.estado = EstadoTitulo.CANCELADO

    def proximo_do_vencimento(self, data_referencia: date, antecedencia_dias: int) -> bool:
        """RF-23: sinalização calculada, não é estado."""
        if self.estado is not EstadoTitulo.ABERTO:
            return False
        dias = (self.vencimento - data_referencia).days
        return 0 <= dias <= antecedencia_dias

    def _pagamento(self, pagamento_id: str) -> Pagamento:
        for pagamento in self.pagamentos:
            if pagamento.id == pagamento_id:
                return pagamento
        raise OperacaoRecusada("Pagamento não encontrado neste título.")


def _exigir_decimal(valor: Decimal, mensagem: str) -> None:
    """E1, E7: NaN, infinito, float ou texto não são valor monetário (defeitos D-01 a D-04)."""
    if not isinstance(valor, Decimal) or not valor.is_finite():
        raise OperacaoRecusada(mensagem)


def _exigir_motivo(motivo: Optional[str], operacao: str) -> None:
    if not isinstance(motivo, str) or not motivo.strip():
        raise OperacaoRecusada(f"O motivo do {operacao} é obrigatório (RF-31).")
