"""Conta a pagar a um fornecedor e seus pagamentos (Spec 018). Regras RB-31 e RB-32.

Espelha o título a receber (Spec 006), com os próprios estados; o pagamento é o mesmo `Pagamento`.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.titulo import Pagamento, PedidoDePagamentoRepetido
from remindme.dominio.valores import ZERO, exigir_decimal, exigir_motivo, exigir_valor_monetario, recusar

TAMANHO_DA_DESCRICAO = 200


class EstadoContaPagar(Enum):
    ABERTA = "Aberta"
    VENCIDA = "Vencida"
    PAGA = "Paga"
    CANCELADA = "Cancelada"


ESTADOS_EM_ABERTO = (EstadoContaPagar.ABERTA, EstadoContaPagar.VENCIDA)


@dataclass
class ContaPagar:
    id: str
    fornecedor_id: str
    descricao: str
    valor: Decimal
    vencimento: date
    condicao_pagamento: Optional[str]
    estado: EstadoContaPagar
    pagamentos: List[Pagamento] = field(default_factory=list)

    @classmethod
    def cadastrar(
        cls,
        id: str,
        fornecedor_id: str,
        descricao: object,
        valor: Decimal,
        vencimento: Optional[date],
        condicao_pagamento: Optional[str] = None,
    ) -> "ContaPagar":
        """RF-88: nasce Aberta, com saldo igual ao valor."""
        texto = " ".join(descricao.split()) if isinstance(descricao, str) else ""
        if not texto:
            recusar("descricao", "Informe o que foi comprado ou o motivo da conta.")
        if len(texto) > TAMANHO_DA_DESCRICAO:
            recusar("descricao", f"A descrição tem no máximo {TAMANHO_DA_DESCRICAO} caracteres.")
        if not isinstance(vencimento, date):
            recusar("vencimento", "O vencimento é obrigatório.")
        exigir_decimal(valor, "O valor da conta deve ser um número decimal finito.")
        exigir_valor_monetario(valor, "da conta")
        if valor <= ZERO:
            recusar("valor", "O valor da conta deve ser maior que zero.")
        return cls(id, fornecedor_id, texto, valor, vencimento, condicao_pagamento, EstadoContaPagar.ABERTA)

    @property
    def saldo(self) -> Decimal:
        """INV-1: valor menos a soma dos pagamentos não estornados."""
        return self.valor - sum((p.valor for p in self.pagamentos if not p.estornado), ZERO)

    def registrar_pagamento(
        self,
        pagamento_id: str,
        valor: Decimal,
        data: date,
        hoje: Optional[date] = None,
        pedido_id: Optional[str] = None,
    ) -> Pagamento:
        """RF-91. RB-31: só Aberta ou Vencida aceita pagamento. RB-32: 0 < valor <= saldo. OPEN-17 e OPEN-25
        valem como no título: data futura é recusada e o pedido repetido é reconhecido antes de tudo."""
        if pedido_id is not None and any(p.pedido_id == pedido_id for p in self.pagamentos):
            raise PedidoDePagamentoRepetido("Este pagamento já foi registrado.")
        if self.estado not in ESTADOS_EM_ABERTO:
            raise OperacaoRecusada(f"Conta {self.estado.value} não aceita pagamento (RB-31).")
        exigir_decimal(valor, "O valor do pagamento deve ser um número decimal finito (RB-32).")
        exigir_valor_monetario(valor, "do pagamento")
        if valor <= ZERO:
            recusar("valor", "O valor do pagamento deve ser maior que zero (RB-32).")
        if valor > self.saldo:
            recusar("valor", f"O valor do pagamento é maior que o saldo de {self.saldo} (RB-32).")
        if not isinstance(data, date):
            recusar("data", "A data do pagamento é obrigatória.")
        if hoje is not None and data > hoje:
            recusar("data", "A data do pagamento não pode ser posterior a hoje.")
        pagamento = Pagamento(id=pagamento_id, valor=valor, data=data, pedido_id=pedido_id)
        self.pagamentos.append(pagamento)
        if self.saldo == ZERO:  # RB-31, INV-2: Paga se, e somente se, o saldo é zero.
            self.estado = EstadoContaPagar.PAGA
        return pagamento

    def marcar_vencida(self, data_referencia: date) -> bool:
        """RF-90: Aberta com vencimento anterior à data de referência passa a Vencida."""
        if self.estado is EstadoContaPagar.ABERTA and self.vencimento < data_referencia:
            self.estado = EstadoContaPagar.VENCIDA
            return True
        return False

    def estornar_pagamento(self, pagamento_id: str, motivo: Optional[str], data_referencia: date) -> Pagamento:
        """RF-92. A permissão (RB-33) é verificada antes, pela camada de aplicação."""
        exigir_motivo(motivo, "estorno", "RF-92")
        if self.estado is EstadoContaPagar.CANCELADA:
            raise OperacaoRecusada("Conta Cancelada não aceita estorno.")
        pagamento = next((p for p in self.pagamentos if p.id == pagamento_id), None)
        if pagamento is None:
            raise OperacaoRecusada("Pagamento não encontrado nesta conta.")
        if pagamento.estornado:
            raise OperacaoRecusada("O pagamento já foi estornado.")
        pagamento.estornado = True
        pagamento.motivo_estorno = motivo
        if self.estado is EstadoContaPagar.PAGA:
            vencida = self.vencimento < data_referencia
            self.estado = EstadoContaPagar.VENCIDA if vencida else EstadoContaPagar.ABERTA
        return pagamento

    def cancelar(self, motivo: Optional[str]) -> None:
        """RF-93. Só Aberta ou Vencida pode ser cancelada."""
        exigir_motivo(motivo, "cancelamento", "RF-93")
        if self.estado not in ESTADOS_EM_ABERTO:
            raise OperacaoRecusada(
                f"Conta {self.estado.value} não pode ser cancelada (RB-31)."
                + (" Estorne os pagamentos antes." if self.estado is EstadoContaPagar.PAGA else "")
            )
        self.estado = EstadoContaPagar.CANCELADA
