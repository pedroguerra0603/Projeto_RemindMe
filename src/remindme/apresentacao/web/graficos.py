"""Gráficos do painel em SVG, desenhados aqui mesmo, sem biblioteca e sem JavaScript.

Cada função recebe uma lista de (rótulo, valor, cor) e devolve o SVG. `cor` é o nome de uma classe do
`estilo.css` (azul, laranja, vermelho, verde, cinza), para o gráfico seguir o tema claro ou escuro.
O valor de cada item também aparece escrito, para não depender só da cor.

As divisões daqui calculam só a escala do desenho, nunca dinheiro (exceção registrada no teste RF-25).
"""

from decimal import Decimal
from typing import Callable, List, Tuple

from remindme.apresentacao.web.html import Html, h, juntar

Item = Tuple[str, Decimal, str]
Formato = Callable[[Decimal], str]
SEM_DADOS = "Ainda não há dados para este gráfico."


def _n(numero) -> str:
    """Número para coordenada do SVG, com duas casas."""
    return f"{numero:.2f}"


def _porcentagem(valor: Decimal, maximo: Decimal) -> Decimal:
    return valor * 100 / maximo if maximo > 0 else Decimal(0)


def colunas(itens: List[Item], formatar: Formato, titulo: str) -> Html:
    """Colunas verticais lado a lado, com o valor em cima e o rótulo embaixo (ex.: recebido por mês)."""
    maximo = max((valor for _, valor, _ in itens), default=Decimal(0))
    if maximo <= 0:
        return h('<p class="vazio">{t}</p>', t=SEM_DADOS)
    passo = Decimal(100) / len(itens)
    partes = []
    for posicao, (rotulo, valor, cor) in enumerate(itens):
        altura = _porcentagem(valor, maximo) * Decimal("0.38")
        meio = passo * posicao + passo / 2
        partes.append(
            h(
                '<rect class="{cor}" x="{x}" y="{y}" width="{l}" height="{a}" rx="1"><title>{r}: {v}</title></rect>'
                '<text class="valor" x="{m}" y="{ty}">{v}</text><text class="rotulo" x="{m}" y="57">{r}</text>',
                cor=cor, x=_n(meio - passo * Decimal("0.3")), y=_n(50 - altura), l=_n(passo * Decimal("0.6")),
                a=_n(altura), r=rotulo, v=formatar(valor), m=_n(meio), ty=_n(48 - altura),
            )
        )
    return h(
        '<svg class="grafico" viewBox="0 0 100 60" role="img" aria-label="{t}">'
        '<line class="eixo" x1="0" y1="50" x2="100" y2="50"/>{p}</svg>',
        t=titulo, p=juntar(partes),
    )


def barras(itens: List[Item], formatar: Formato, titulo: str) -> Html:
    """Barras horizontais, uma por linha, com o rótulo à esquerda e o valor à direita."""
    maximo = max((valor for _, valor, _ in itens), default=Decimal(0))
    if maximo <= 0:
        return h('<p class="vazio">{t}</p>', t=SEM_DADOS)
    linhas = [
        h(
            '<li><span class="rotulo">{r}</span>'
            '<svg class="barra" viewBox="0 0 100 6" preserveAspectRatio="none" aria-hidden="true">'
            '<rect class="trilho" width="100" height="6" rx="3"/><rect class="{cor}" width="{w}" height="6" rx="3"/></svg>'
            '<span class="valor">{v}</span></li>',
            r=rotulo, cor=cor, w=_n(max(_porcentagem(valor, maximo), Decimal(1)) if valor > 0 else 0), v=formatar(valor),
        )
        for rotulo, valor, cor in itens
    ]
    return h('<ul class="grafico-barras" aria-label="{t}">{l}</ul>', t=titulo, l=juntar(linhas))


def anel(itens: List[Item], formatar: Formato, titulo: str) -> Html:
    """Anel (rosca) com a parte de cada item no total, e a legenda ao lado.

    Cada fatia é um círculo com `pathLength="100"`: o traço desenha só a porcentagem da fatia, a partir de
    onde a anterior terminou. Assim não é preciso trigonometria.
    """
    total = sum((valor for _, valor, _ in itens), Decimal(0))
    if total <= 0:
        return h('<p class="vazio">{t}</p>', t=SEM_DADOS)
    fatias, inicio = [], Decimal(0)
    for rotulo, valor, cor in itens:
        parte = _porcentagem(valor, total)
        fatias.append(
            h(
                '<circle class="{cor}" cx="21" cy="21" r="15.9" pathLength="100" stroke-dasharray="{p} {resto}" '
                'stroke-dashoffset="{o}"><title>{r}: {v}</title></circle>',
                cor=cor, p=_n(parte), resto=_n(100 - parte), o=_n(25 - inicio), r=rotulo, v=formatar(valor),
            )
        )
        inicio += parte
    legenda = juntar(
        h('<li><span class="marcador {cor}"></span>{r} <strong>{v}</strong></li>', cor=cor, r=rotulo, v=formatar(valor))
        for rotulo, valor, cor in itens
    )
    return h(
        '<div class="grafico-anel"><svg viewBox="0 0 42 42" role="img" aria-label="{t}">{f}</svg>'
        '<ul class="legenda">{l}</ul></div>',
        t=titulo, f=juntar(fatias), l=legenda,
    )
