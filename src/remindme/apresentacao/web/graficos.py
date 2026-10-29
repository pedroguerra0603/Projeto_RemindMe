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
    """Colunas verticais lado a lado, com o valor em cima e o rótulo embaixo (ex.: recebido por mês).
    Coluna com valor zero mostra só o rótulo, para o gráfico ficar limpo."""
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
                '<text class="valor" x="{m}" y="{ty}">{escrito}</text><text class="rotulo" x="{m}" y="57">{r}</text>',
                cor=cor, x=_n(meio - passo * Decimal("0.3")), y=_n(50 - altura), l=_n(passo * Decimal("0.6")),
                a=_n(altura), r=rotulo, v=formatar(valor), escrito=formatar(valor) if valor > 0 else "", m=_n(meio), ty=_n(48 - altura),
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


# Régua do caixa: os títulos numa linha do tempo, com o hoje no meio.

DIAS_ANTES, DIAS_DEPOIS = 30, 15
Marco = Tuple[str, int, Decimal, str, str]  # cliente, dias até o vencimento (negativo = vencido), saldo, cor, link


def regua(marcos: List[Marco], formatar: Formato, hoje: str) -> Html:
    """Vencidos à esquerda do hoje, a vencer à direita. Cada título é um alfinete clicável com o saldo.

    Vencido há mais de 30 dias fica na ponta esquerda. Quando dois alfinetes ficam perto demais para os
    valores caberem, o seguinte sobe uma linha (a primeira linha livre, da esquerda para a direita).
    """
    if not marcos:
        return h('<p class="vazio">{t}</p>', t="Nenhum título vencido nem a vencer nos próximos 15 dias.")
    largura, distancia_minima, altura_da_linha = 200, 24, 10
    escala = Decimal(largura) / (DIAS_ANTES + DIAS_DEPOIS)
    fim_das_linhas: List[Decimal] = []
    posicoes = []
    for cliente, dias, saldo, cor, link in sorted(marcos, key=lambda m: m[1]):
        x = (max(-DIAS_ANTES, min(DIAS_DEPOIS, dias)) + DIAS_ANTES) * escala
        linha = next((n for n, fim in enumerate(fim_das_linhas) if x - fim >= distancia_minima), len(fim_das_linhas))
        if linha == len(fim_das_linhas):
            fim_das_linhas.append(x)
        fim_das_linhas[linha] = x
        posicoes.append((x, linha, cliente, saldo, cor, link))
    eixo = len(fim_das_linhas) * altura_da_linha + 8
    pontos = [
        h(
            '<a href="{link}"><title>{c}: {v}</title><line class="haste" x1="{x}" y1="{eixo}" x2="{x}" y2="{y}"/>'
            '<circle class="{cor}" cx="{x}" cy="{y}" r="2.4"/><text class="valor" x="{x}" y="{ty}">{curto}</text></a>',
            link=link, c=cliente, v=formatar(saldo), cor=cor, x=_n(x), eixo=eixo,
            y=eixo - 5 - linha * altura_da_linha, ty=eixo - 9 - linha * altura_da_linha, curto=formatar(saldo),
        )
        for x, linha, cliente, saldo, cor, link in posicoes
    ]
    zero = _n(DIAS_ANTES * escala)
    return h(
        '<svg class="regua" viewBox="-10 -2 220 {altura}" role="img" aria-label="Títulos vencidos e a vencer em torno de hoje">'
        '<line class="eixo" x1="0" y1="{eixo}" x2="{l}" y2="{eixo}"/>'
        '<line class="hoje" x1="{z}" y1="0" x2="{z}" y2="{fim_hoje}"/>'
        '{p}'
        '<text class="rotulo" x="0" y="{ry}">há 30 dias</text>'
        '<text class="rotulo hoje-rotulo" x="{z}" y="{ry}">hoje, {hoje}</text>'
        '<text class="rotulo" x="{l}" y="{ry}">em 15 dias</text></svg>',
        altura=eixo + 10, eixo=eixo, l=largura, z=zero, fim_hoje=eixo + 2, ry=eixo + 7, hoje=hoje, p=juntar(pontos),
    )
