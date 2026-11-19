"""Páginas de títulos (Specs 006 e 017). Só montam o que os serviços devolvem (INV-1)."""

from decimal import Decimal
from typing import Dict, Optional

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import (
    Contexto,
    Erros,
    Valores,
    botao_link,
    cabecalho,
    caixa_de_aviso,
    campo,
    erro_geral,
    layout,
    protecao,
    selecao,
    selo_estado,
    selo_proximo,
    tabela,
)
from remindme.apresentacao.web.paginas_auditoria import _cartao_historico
from remindme.apresentacao.web.paginas_orcamentos import _origem_do_titulo
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo


def _tabela_de_titulos(visoes: list, nomes_clientes: Dict[str, str], mostrar_cliente: bool = True) -> Html:
    cabecalhos = ([("Cliente", "")] if mostrar_cliente else []) + [
        ("Vencimento", ""),
        ("Valor", "numero"),
        ("Saldo", "numero"),
        ("Estado", ""),
    ]
    linhas = []
    for v in visoes:
        cliente = h('<td><a href="/titulos/{id}">{n}</a></td>', id=v.id, n=nomes_clientes.get(v.cliente_id, "Cliente")) if mostrar_cliente else Html("")
        vencimento = h('<td><a href="/titulos/{id}">{d}</a></td>', id=v.id, d=f.data(v.vencimento)) if not mostrar_cliente else h("<td>{d}</td>", d=f.data(v.vencimento))
        linhas.append(
            h(
                '<tr class="{classe}">{cliente}{vencimento}<td class="numero">{valor}</td><td class="numero">{saldo}</td><td>{estado} {proximo}</td></tr>',
                classe="vencido" if v.estado is EstadoTitulo.VENCIDO else "",
                cliente=cliente,
                vencimento=vencimento,
                valor=f.moeda(v.valor),
                saldo=f.moeda(v.saldo),
                estado=selo_estado(v.estado),
                proximo=selo_proximo() if v.proximo_do_vencimento else Html(""),
            )
        )
    return tabela(cabecalhos, linhas, "Nenhum título encontrado.")


def pagina_titulos(ctx: Contexto, visoes: list, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros, aviso=None) -> Html:
    acoes = []
    if ctx.pode(Operacao.VERIFICAR_VENCIMENTOS):
        acoes.append(
            h(
                '<form method="post" action="/titulos/verificar-vencimentos">{p}<button class="secundario" type="submit">Verificar vencimentos</button></form>',
                p=protecao(ctx),
            )
        )
    if ctx.pode(Operacao.CADASTRAR_TITULO):
        acoes.append(botao_link("/titulos/novo", "Novo título"))
    opcoes_clientes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    filtros = h(
        """<form class="filtros" method="get" action="/titulos">
{cliente}{estado}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/titulos">Limpar</a></div>
</form>""",
        cliente=selecao("cliente", "Cliente", opcoes_clientes, valores, erros, vazio="Todos", obrigatorio=False),
        estado=selecao("estado", "Estado", [(e_.name, e_.value) for e_ in EstadoTitulo], valores, erros, vazio="Todos", obrigatorio=False),
        de=campo("de", "Vencimento de", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("ate", "Vencimento até", valores, erros, tipo="date", obrigatorio=False),
    )
    total = sum((v.saldo for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)), Decimal("0.00"))
    conteudo = juntar(
        [
            cabecalho("Títulos", f"{len(visoes)} título(s), com {f.moeda(total)} em aberto", juntar(acoes)),
            h('<section class="cartao">{f}</section>', f=filtros),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=_tabela_de_titulos(visoes, nomes_clientes)),
        ]
    )
    return layout("Títulos", conteudo, ctx, "titulos", aviso)


def pagina_titulo_formulario(ctx: Contexto, nomes_clientes: Dict[str, str], valores: Valores, erros: Erros) -> Html:
    opcoes = sorted(nomes_clientes.items(), key=lambda par: par[1].casefold())
    if not opcoes:
        aviso = caixa_de_aviso("info", "Cadastre um cliente antes de cadastrar o título.")
        acao = botao_link("/clientes/novo", "Novo cliente") if ctx.pode(Operacao.MANTER_CLIENTES) else Html("")
        return layout("Novo título", juntar([cabecalho("Novo título"), aviso, acao]), ctx, "titulos")
    formulario = h(
        """<form class="formulario" method="post" action="/titulos/novo" novalidate>
{protecao}{geral}
{cliente}
<div class="linha-campos">{valor}{vencimento}</div>
{condicao}
<div class="acoes"><button type="submit">Cadastrar título</button><a class="botao secundario" href="/titulos">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        cliente=selecao("cliente", "Cliente", opcoes, valores, erros, vazio="Escolha o cliente"),
        valor=campo("valor", "Valor (R$)", valores, erros, ajuda="Por exemplo, 1.234,56.", extra='inputmode="decimal"'),
        vencimento=campo("vencimento", "Vencimento", valores, erros, tipo="date"),
        condicao=campo("condicao", "Condição de pagamento", valores, erros, obrigatorio=False, ajuda="Opcional. Por exemplo, à vista no Pix."),
    )
    conteudo = juntar([cabecalho("Novo título", "O título nasce Aberto, com origem manual e saldo igual ao valor."), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Novo título", conteudo, ctx, "titulos")


def pagina_titulo(
    ctx: Contexto,
    titulo,
    cliente_nome: str,
    proximo: bool,
    pedido: str,
    valores: Valores,
    erros: Erros,
    historico: Optional[list],
    aviso=None,
) -> Html:
    aceita_pagamento = titulo.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)
    acoes = []
    if aceita_pagamento and ctx.pode(Operacao.CANCELAR_TITULO):
        acoes.append(botao_link(f"/titulos/{titulo.id}/cancelamento", "Cancelar título", "secundario"))
    dados = h(
        """<dl class="dados">
<div><dt>Valor</dt><dd>{valor}</dd></div>
<div><dt>Saldo</dt><dd>{saldo}</dd></div>
<div><dt>Vencimento</dt><dd>{venc}</dd></div>
<div><dt>Condição de pagamento</dt><dd>{condicao}</dd></div>
<div><dt>Origem</dt><dd>{origem}</dd></div>
</dl>""",
        valor=f.moeda(titulo.valor),
        saldo=f.moeda(titulo.saldo),
        venc=f.data(titulo.vencimento),
        condicao=titulo.condicao_pagamento or "—",
        origem=_origem_do_titulo(ctx, titulo),
    )
    linhas = []
    for pagamento in titulo.pagamentos:
        if pagamento.estornado:
            situacao = h('<span class="selo cancelado">Estornado</span> <span class="secundario">{m}</span>', m=pagamento.motivo_estorno or "")
            acao = Html("")
        else:
            situacao = Html('<span class="selo baixado">Registrado</span>')
            acao = (
                h('<a class="botao pequeno secundario" href="/titulos/{t}/pagamentos/{p}/estorno">Estornar</a>', t=titulo.id, p=pagamento.id)
                if ctx.pode(Operacao.ESTORNAR_PAGAMENTO) and titulo.estado is not EstadoTitulo.CANCELADO
                else Html("")
            )
        linhas.append(
            h(
                '<tr><td>{data}</td><td class="numero">{valor}</td><td>{situacao}</td><td class="numero">{acao}</td></tr>',
                data=f.data(pagamento.data),
                valor=f.moeda(pagamento.valor),
                situacao=situacao,
                acao=acao,
            )
        )
    pagamentos = tabela([("Data", ""), ("Valor", "numero"), ("Situação", ""), ("", "numero")], linhas, "Nenhum pagamento registrado.")
    partes = [
        cabecalho(
            cliente_nome,
            "Título",
            juntar(acoes),
        ),
        h('<div class="selos-do-titulo">{estado}{proximo}</div>', estado=selo_estado(titulo.estado, grande=True), proximo=selo_proximo() if proximo else Html("")),
        h('<section class="cartao">{d}</section>', d=dados),
    ]
    if aceita_pagamento and ctx.pode(Operacao.REGISTRAR_PAGAMENTO):
        partes.append(
            h(
                """<section class="cartao" aria-labelledby="t-pagamento"><h2 id="t-pagamento">Registrar pagamento</h2>
<form class="formulario" method="post" action="/titulos/{id}/pagamentos" novalidate>
{protecao}<input type="hidden" name="pedido" value="{pedido}">{geral}
<div class="linha-campos">{valor}{data}</div>
<div class="acoes"><button type="submit">Registrar pagamento</button></div>
</form></section>""",
                id=titulo.id,
                protecao=protecao(ctx),
                pedido=pedido,
                geral=erro_geral(erros),
                valor=campo("valor", "Valor recebido (R$)", valores, erros, ajuda=f"Saldo atual: {f.moeda(titulo.saldo)}.", extra='inputmode="decimal"'),
                data=campo("data", "Data do pagamento", valores, erros, tipo="date"),
            )
        )
    partes.append(h('<section class="cartao sem-borda-interna"><h2>Pagamentos</h2>{p}</section>', p=pagamentos))
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout("Título", juntar(partes), ctx, "titulos", aviso)
