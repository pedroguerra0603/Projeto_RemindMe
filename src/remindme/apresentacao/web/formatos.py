"""Formatos brasileiros de exibição e leitura dos campos dos formulários. Nenhuma regra de negócio aqui."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from remindme.aplicacao.tempo import horario_local

_VALOR = re.compile(r"(?P<sinal>-?)(?P<inteiro>[0-9][0-9.]*)(?:,(?P<decimais>[0-9]+))?")
_MILHARES = re.compile(r"[1-9][0-9]{0,2}(?:\.[0-9]{3})+")
_PONTO_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def moeda(valor: Decimal) -> str:
    """R$ 1.234,56."""
    sinal = "-" if valor < 0 else ""
    inteiro, centavos = f"{abs(valor):.2f}".split(".")
    grupos = []
    while inteiro:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    return f"{sinal}R$ {'.'.join(grupos)},{centavos}"


def moeda_curta(valor: Decimal) -> str:
    """Para rótulos apertados de gráfico: R$ 850, R$ 1,2 mil."""
    if abs(valor) >= 1000:
        return "R$ " + f"{valor.scaleb(-3):.1f}".replace(".", ",") + " mil"
    return f"R$ {valor:.0f}"


def valor_para_campo(valor: Optional[Decimal]) -> str:
    """O valor como o usuário o digitaria: 1234,56."""
    return "" if valor is None else f"{valor:.2f}".replace(".", ",")


def numero(quantidade: Decimal) -> str:
    """Quantidade sem zeros sobrando: 2, 1,5, 0,25."""
    texto = f"{quantidade:f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def numero_para_campo(quantidade: Decimal) -> str:
    return numero(quantidade)


def percentual(valor: Decimal) -> str:
    """7,5%."""
    return numero(valor) + "%"


def ler_valor(texto: str) -> Optional[Decimal]:
    """Lê "1.234,56", "1234,56", "1.000" (mil) ou "1234.56". Devolve None quando o texto não é um valor.

    O ponto é de milhar quando separa grupos de três algarismos, como no Brasil; agrupamento malformado é recusado.
    """
    limpo = texto.replace("R$", "").replace(" ", "").strip()
    casamento = _VALOR.fullmatch(limpo)
    if not casamento:
        return None
    sinal, inteiro, decimais = casamento.group("sinal"), casamento.group("inteiro"), casamento.group("decimais")
    if decimais is None and not _MILHARES.fullmatch(inteiro) and _PONTO_DECIMAL.fullmatch(inteiro):
        return Decimal(sinal + inteiro)
    if "." in inteiro and not _MILHARES.fullmatch(inteiro):
        return None
    return Decimal(sinal + inteiro.replace(".", "") + ("." + decimais if decimais else ""))


MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
DIAS_DA_SEMANA = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")


def data_por_extenso(dia: date) -> str:
    """quarta-feira, 29 de outubro de 2026."""
    return f"{DIAS_DA_SEMANA[dia.weekday()]}, {dia.day} de {MESES[dia.month - 1]} de {dia.year}"


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
