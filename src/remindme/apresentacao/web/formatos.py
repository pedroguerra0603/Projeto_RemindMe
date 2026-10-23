"""Formatos brasileiros de exibição e leitura dos campos dos formulários. Nenhuma regra de negócio aqui."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from remindme.aplicacao.tempo import horario_local

_SO_VALOR = re.compile(r"^-?[0-9.,]+$")


def moeda(valor: Decimal) -> str:
    """R$ 1.234,56."""
    sinal = "-" if valor < 0 else ""
    inteiro, centavos = f"{abs(valor):.2f}".split(".")
    grupos = []
    while inteiro:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    return f"{sinal}R$ {'.'.join(grupos)},{centavos}"


def valor_para_campo(valor: Optional[Decimal]) -> str:
    """O valor como o usuário o digitaria: 1234,56."""
    return "" if valor is None else f"{valor:.2f}".replace(".", ",")


def ler_valor(texto: str) -> Optional[Decimal]:
    """Lê "1.234,56", "1234,56" ou "1234.56". Devolve None quando o texto não é um valor."""
    limpo = texto.replace("R$", "").replace(" ", "").strip()
    if not limpo or not _SO_VALOR.match(limpo):
        return None
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    elif limpo.count(".") > 1:
        limpo = limpo.replace(".", "")
    try:
        return Decimal(limpo)
    except InvalidOperation:
        return None


def data(dia: Optional[date]) -> str:
    return dia.strftime("%d/%m/%Y") if dia else ""


def data_hora(momento: datetime) -> str:
    return horario_local(momento).strftime("%d/%m/%Y %H:%M")


def ler_data(texto: str) -> Optional[date]:
    """O campo de data do navegador envia AAAA-MM-DD; também aceita DD/MM/AAAA digitado."""
    texto = texto.strip()
    try:
        if "/" in texto:
            dia, mes, ano = texto.split("/")
            return date(int(ano), int(mes), int(dia))
        return date.fromisoformat(texto)
    except ValueError:
        return None


def documento(texto: str) -> str:
    if len(texto) == 11:
        return f"{texto[:3]}.{texto[3:6]}.{texto[6:9]}-{texto[9:]}"
    if len(texto) == 14:
        return f"{texto[:2]}.{texto[2:5]}.{texto[5:8]}/{texto[8:12]}-{texto[12:]}"
    return texto


def contato(texto: str) -> str:
    if texto.isdigit() and len(texto) == 11:
        return f"({texto[:2]}) {texto[2:7]}-{texto[7:]}"
    if texto.isdigit() and len(texto) == 10:
        return f"({texto[:2]}) {texto[2:6]}-{texto[6:]}"
    return texto
