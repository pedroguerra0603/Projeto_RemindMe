"""Validações comuns de valores monetários e de motivo: título (Spec 006) e conta a pagar (Spec 018)."""

from decimal import Decimal
from typing import NoReturn, Optional

from remindme.dominio.erros import OperacaoRecusada

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")
# OPEN-24, decidida em 2026-10-23: no máximo 15 dígitos inteiros, longe do limite da aritmética (D-06).
LIMITE_VALOR = Decimal(10) ** 15


def recusar(campo: str, mensagem: str) -> NoReturn:
    """Recusa ligada ao campo que a causou (RNF-14)."""
    raise OperacaoRecusada(mensagem, {campo: mensagem})


def exigir_decimal(valor: Decimal, mensagem: str) -> None:
    """NaN, infinito, float ou texto não são valor monetário (defeitos D-01 a D-04)."""
    if not isinstance(valor, Decimal) or not valor.is_finite():
        recusar("valor", mensagem)


def exigir_valor_monetario(valor: Decimal, sujeito: str) -> None:
    """OPEN-20 e OPEN-24, decididas em 2026-10-23: até duas casas decimais e até 15 dígitos inteiros.

    Valor fora disso é recusado, sem arredondamento.
    """
    if abs(valor) >= LIMITE_VALOR:
        recusar("valor", f"O valor {sujeito} deve ter no máximo 15 dígitos inteiros.")
    if valor != valor.quantize(CENTAVO):
        recusar("valor", f"O valor {sujeito} deve ter no máximo duas casas decimais.")


def exigir_motivo(motivo: Optional[str], operacao: str, regra: str) -> None:
    if not isinstance(motivo, str) or not motivo.strip():
        recusar("motivo", f"O motivo do {operacao} é obrigatório ({regra}).")
