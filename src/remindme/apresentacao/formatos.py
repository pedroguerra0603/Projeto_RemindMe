"""Conversão entre o que o usuário digita ou vê e os tipos do domínio."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

# Provisório, até OPEN-20 e OPEN-24: no máximo duas casas e quinze dígitos inteiros.
CASAS_DECIMAIS = 2
DIGITOS_INTEIROS = 15


class ValorInvalido(ValueError):
    pass


def ler_dinheiro(texto: Optional[str]) -> Decimal:
    """Aceita `1.234,56`, `1234,56`, `1234.56` e `R$ 1.234,56`."""
    bruto = re.sub(r"[R$\s]", "", texto or "")
    if not bruto:
        raise ValorInvalido("obrigatório")
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif bruto.count(".") > 1:
        bruto = bruto.replace(".", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", bruto):
        raise ValorInvalido("use um número, como 1.234,56")
    try:
        valor = Decimal(bruto)
    except InvalidOperation:
        raise ValorInvalido("use um número, como 1.234,56") from None
    if "." in bruto and len(bruto.split(".")[1]) > CASAS_DECIMAIS:
        raise ValorInvalido(f"use no máximo {CASAS_DECIMAIS} casas decimais")
    if len(bruto.split(".")[0].lstrip("-")) > DIGITOS_INTEIROS:
        raise ValorInvalido("valor acima do limite aceito")
    return valor


def ler_data(texto: Optional[str]) -> Optional[date]:
    """Aceita `aaaa-mm-dd` (campo de data do navegador) e `dd/mm/aaaa`. Vazio devolve None."""
    texto = (texto or "").strip()
    if not texto:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValorInvalido("data inválida")


def dinheiro(valor: Decimal) -> str:
    texto = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def data(dia: Optional[date]) -> str:
    return dia.strftime("%d/%m/%Y") if dia else ""


def data_hora(momento: datetime) -> str:
    return momento.strftime("%d/%m/%Y %H:%M")


def iso(dia: Optional[date]) -> str:
    return dia.isoformat() if dia else ""
