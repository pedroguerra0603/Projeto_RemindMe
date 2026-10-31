"""Páginas da Spec 018: fornecedores e contas a pagar. Mesmos componentes das páginas de clientes e títulos."""

from decimal import Decimal
from typing import Dict, Optional

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import (
    Contexto,
    Erros,
    Valores,
    _cartao_historico,
    botao_link,
    cabecalho,
    caixa_de_aviso,
    campo,
    erro_geral,
    layout,
    protecao,
    selecao,
    tabela,
)
from remindme.dominio.conta_pagar import ESTADOS_EM_ABERTO, EstadoContaPagar
from remindme.dominio.operacoes import Operacao

CLASSE_DO_ESTADO = {
    EstadoContaPagar.ABERTA: "aberto",
    EstadoContaPagar.VENCIDA: "vencido",
    EstadoContaPagar.PAGA: "baixado",
    EstadoContaPagar.CANCELADA: "cancelado",
}


def selo_conta(estado: EstadoContaPagar, grande: bool = False) -> Html:
    return h(
        '<span class="selo {c}{g}">{t}</span>', c=CLASSE_DO_ESTADO[estado], g=" grande" if grande else "", t=estado.value
    )


def em_aberto(visoes: list) -> Decimal:
    return sum((v.saldo for v in visoes if v.estado in ESTADOS_EM_ABERTO), Decimal("0.00"))


# Fornecedores


def pagina_fornecedores(ctx: Contexto, fornecedores: list, termo: str, aviso=None) -> Html:
    acoes = botao_link("/fornecedores/novo", "Novo fornecedor") if ctx.pode(Operacao.MANTER_FORNECEDORES) else Html("")
    busca = h(
        """<form class="filtros" method="get" action="/fornecedores" role="search">
  <div class="campo"><label for="q">Pesquisar por nome ou documento</label><input id="q" name="q" type="search" value="{termo}"></div>
  <div><button class="secundario" type="submit">Pesquisar</button></div>
</form>""",
        termo=termo,
    )
    linhas = [
        h(
            '<tr><td><a href="/fornecedores/{id}">{nome}</a></td><td class="mono">{doc}</td><td>{contato}</td></tr>',
            id=x.id, nome=x.nome, doc=f.documento(x.documento), contato=f.contato(x.contato),
        )
        for x in fornecedores
    ]
    vazio = "Nenhum fornecedor encontrado para a pesquisa." if termo else "Nenhum fornecedor cadastrado ainda."
    conteudo = juntar(
        [
            cabecalho("Fornecedores", "De quem a empresa compra e a quem deve contas a pagar.", acoes),
            h('<section class="cartao">{b}</section>', b=busca),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela([("Nome", ""), ("Documento", ""), ("Contato", "")], linhas, vazio)),
        ]
    )
    return layout("Fornecedores", conteudo, ctx, "fornecedores", aviso)


def pagina_fornecedor_formulario(ctx: Contexto, valores: Valores, erros: Erros, fornecedor_id: Optional[str] = None) -> Html:
    novo = fornecedor_id is None
    formulario = h(
        """<form class="formulario" method="post" action="{acao}" novalidate>
{protecao}{geral}
{nome}
<div class="linha-campos">{documento}{contato}</div>
<div class="acoes"><button type="submit">{botao}</button><a class="botao secundario" href="{voltar}">Cancelar</a></div>
</form>""",
        acao="/fornecedores/novo" if novo else f"/fornecedores/{fornecedor_id}/editar",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        nome=campo("nome", "Nome ou razão social", valores, erros),
        documento=campo("documento", "CPF ou CNPJ", valores, erros, ajuda="Com ou sem pontuação."),
        contato=campo("contato", "Contato", valores, erros, ajuda="E-mail ou telefone com DDD."),
        botao="Cadastrar fornecedor" if novo else "Salvar alterações",
        voltar="/fornecedores" if novo else f"/fornecedores/{fornecedor_id}",
    )
    titulo = "Novo fornecedor" if novo else "Alterar fornecedor"
    return layout(titulo, juntar([cabecalho(titulo), h('<section class="cartao">{f}</section>', f=formulario)]), ctx, "fornecedores")


def pagina_fornecedor(ctx: Contexto, fornecedor, visoes: list, historico: Optional[list], aviso=None) -> Html:
    acoes = []
    if ctx.pode(Operacao.CADASTRAR_CONTA_PAGAR):
        acoes.append(botao_link(f"/contas-a-pagar/nova?fornecedor={fornecedor.id}", "Nova conta a pagar"))
    if ctx.pode(Operacao.MANTER_FORNECEDORES):
        acoes.append(botao_link(f"/fornecedores/{fornecedor.id}/editar", "Alterar dados", "secundario"))
    dados = h(
        '<dl class="dados"><div><dt>Documento</dt><dd class="mono">{doc}</dd></div><div><dt>Contato</dt><dd>{contato}</dd></div>'
        '<div><dt>Contas</dt><dd>{n}</dd></div><div><dt>A pagar</dt><dd>{saldo}</dd></div></dl>',
        doc=f.documento(fornecedor.documento), contato=f.contato(fornecedor.contato), n=len(visoes), saldo=f.moeda(em_aberto(visoes)),
    )
    partes = [
        cabecalho(fornecedor.nome, "Fornecedor", juntar(acoes)),
        h('<section class="cartao">{d}</section>', d=dados),
        h('<section class="cartao sem-borda-interna"><h2>Contas a pagar</h2>{t}</section>', t=tabela_de_contas(visoes, {}, mostrar_fornecedor=False)),
    ]
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout(fornecedor.nome, juntar(partes), ctx, "fornecedores", aviso)


# Contas a pagar


def tabela_de_contas(visoes: list, nomes: Dict[str, str], mostrar_fornecedor: bool = True) -> Html:
    cabecalhos = ([("Fornecedor", "")] if mostrar_fornecedor else []) + [
        ("Descrição", ""), ("Vencimento", ""), ("Valor", "numero"), ("Saldo", "numero"), ("Estado", ""),
    ]
    linhas = [
        h(
            '<tr class="{classe}">{fornecedor}<td><a href="/contas-a-pagar/{id}">{descricao}</a></td><td>{venc}</td>'
            '<td class="numero">{valor}</td><td class="numero">{saldo}</td><td>{estado}</td></tr>',
            classe="vencido" if v.estado is EstadoContaPagar.VENCIDA else "",
            fornecedor=h("<td>{n}</td>", n=nomes.get(v.fornecedor_id, "Fornecedor")) if mostrar_fornecedor else Html(""),
            id=v.id, descricao=v.descricao, venc=f.data(v.vencimento), valor=f.moeda(v.valor), saldo=f.moeda(v.saldo),
            estado=selo_conta(v.estado),
        )
        for v in visoes
    ]
    return tabela(cabecalhos, linhas, "Nenhuma conta a pagar encontrada.")


def pagina_contas(ctx: Contexto, visoes: list, nomes: Dict[str, str], valores: Valores, erros: Erros, aviso=None) -> Html:
    acoes = botao_link("/contas-a-pagar/nova", "Nova conta a pagar") if ctx.pode(Operacao.CADASTRAR_CONTA_PAGAR) else Html("")
    opcoes = sorted(nomes.items(), key=lambda par: par[1].casefold())
    filtros = h(
        """<form class="filtros" method="get" action="/contas-a-pagar">
{fornecedor}{estado}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/contas-a-pagar">Limpar</a></div>
</form>""",
        fornecedor=selecao("fornecedor", "Fornecedor", opcoes, valores, erros, vazio="Todos", obrigatorio=False),
        estado=selecao("estado", "Estado", [(e_.name, e_.value) for e_ in EstadoContaPagar], valores, erros, vazio="Todos", obrigatorio=False),
        de=campo("de", "Vencimento de", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("ate", "Vencimento até", valores, erros, tipo="date", obrigatorio=False),
    )
    conteudo = juntar(
        [
            cabecalho("Contas a pagar", f"{len(visoes)} conta(s), com {f.moeda(em_aberto(visoes))} a pagar", acoes),
            h('<section class="cartao">{f}</section>', f=filtros),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela_de_contas(visoes, nomes)),
        ]
    )
    return layout("Contas a pagar", conteudo, ctx, "contas", aviso)


def pagina_conta_formulario(ctx: Contexto, nomes: Dict[str, str], valores: Valores, erros: Erros) -> Html:
    opcoes = sorted(nomes.items(), key=lambda par: par[1].casefold())
    if not opcoes:
        acao = botao_link("/fornecedores/novo", "Novo fornecedor") if ctx.pode(Operacao.MANTER_FORNECEDORES) else Html("")
        aviso = caixa_de_aviso("info", "Cadastre um fornecedor antes de cadastrar a conta a pagar.")
        return layout("Nova conta a pagar", juntar([cabecalho("Nova conta a pagar"), aviso, acao]), ctx, "contas")
    formulario = h(
        """<form class="formulario" method="post" action="/contas-a-pagar/nova" novalidate>
{protecao}{geral}
{fornecedor}
{descricao}
<div class="linha-campos">{valor}{vencimento}</div>
{condicao}
<div class="acoes"><button type="submit">Cadastrar conta</button><a class="botao secundario" href="/contas-a-pagar">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        fornecedor=selecao("fornecedor", "Fornecedor", opcoes, valores, erros, vazio="Escolha o fornecedor"),
        descricao=campo("descricao", "Descrição", valores, erros, ajuda="O que foi comprado. Por exemplo, 20 pneus aro 14."),
        valor=campo("valor", "Valor (R$)", valores, erros, ajuda="Por exemplo, 1.234,56.", extra='inputmode="decimal"'),
        vencimento=campo("vencimento", "Vencimento", valores, erros, tipo="date"),
        condicao=campo("condicao", "Forma de pagamento", valores, erros, obrigatorio=False, ajuda="Opcional. Por exemplo, boleto."),
    )
    conteudo = juntar(
        [cabecalho("Nova conta a pagar", "A conta nasce Aberta, com saldo igual ao valor."), h('<section class="cartao">{f}</section>', f=formulario)]
    )
    return layout("Nova conta a pagar", conteudo, ctx, "contas")


def pagina_conta(
    ctx: Contexto, conta, fornecedor_nome: str, pedido: str, valores: Valores, erros: Erros, historico: Optional[list], aviso=None
) -> Html:
    aceita_pagamento = conta.estado in ESTADOS_EM_ABERTO
    acoes = []
    if aceita_pagamento and ctx.pode(Operacao.CANCELAR_CONTA_PAGAR):
        acoes.append(botao_link(f"/contas-a-pagar/{conta.id}/cancelamento", "Cancelar conta", "secundario"))
    dados = h(
        """<dl class="dados">
<div><dt>Fornecedor</dt><dd><a href="/fornecedores/{fid}">{fornecedor}</a></dd></div>
<div><dt>Valor</dt><dd>{valor}</dd></div>
<div><dt>Saldo</dt><dd>{saldo}</dd></div>
<div><dt>Vencimento</dt><dd>{venc}</dd></div>
<div><dt>Forma de pagamento</dt><dd>{condicao}</dd></div>
</dl>""",
        fid=conta.fornecedor_id, fornecedor=fornecedor_nome, valor=f.moeda(conta.valor), saldo=f.moeda(conta.saldo),
        venc=f.data(conta.vencimento), condicao=conta.condicao_pagamento or "—",
    )
    linhas = []
    for pagamento in conta.pagamentos:
        if pagamento.estornado:
            situacao = h('<span class="selo cancelado">Estornado</span> <span class="secundario">{m}</span>', m=pagamento.motivo_estorno or "")
            acao = Html("")
        else:
            situacao = Html('<span class="selo baixado">Registrado</span>')
            pode = ctx.pode(Operacao.ESTORNAR_PAGAMENTO_CONTA) and conta.estado is not EstadoContaPagar.CANCELADA
            acao = (
                h('<a class="botao pequeno secundario" href="/contas-a-pagar/{c}/pagamentos/{p}/estorno">Estornar</a>', c=conta.id, p=pagamento.id)
                if pode
                else Html("")
            )
        linhas.append(
            h(
                '<tr><td>{data}</td><td class="numero">{valor}</td><td>{situacao}</td><td class="numero">{acao}</td></tr>',
                data=f.data(pagamento.data), valor=f.moeda(pagamento.valor), situacao=situacao, acao=acao,
            )
        )
    partes = [
        cabecalho(conta.descricao, "Conta a pagar", juntar(acoes)),
        h('<div class="selos-do-titulo">{e}</div>', e=selo_conta(conta.estado, grande=True)),
        h('<section class="cartao">{d}</section>', d=dados),
    ]
    if aceita_pagamento and ctx.pode(Operacao.PAGAR_CONTA):
        partes.append(
            h(
                """<section class="cartao" aria-labelledby="t-pagamento"><h2 id="t-pagamento">Registrar pagamento</h2>
<form class="formulario" method="post" action="/contas-a-pagar/{id}/pagamentos" novalidate>
{protecao}<input type="hidden" name="pedido" value="{pedido}">{geral}
<div class="linha-campos">{valor}{data}</div>
<div class="acoes"><button type="submit">Registrar pagamento</button></div>
</form></section>""",
                id=conta.id, protecao=protecao(ctx), pedido=pedido, geral=erro_geral(erros),
                valor=campo("valor", "Valor pago (R$)", valores, erros, ajuda=f"Saldo atual: {f.moeda(conta.saldo)}.", extra='inputmode="decimal"'),
                data=campo("data", "Data do pagamento", valores, erros, tipo="date"),
            )
        )
    pagamentos = tabela([("Data", ""), ("Valor", "numero"), ("Situação", ""), ("", "numero")], linhas, "Nenhum pagamento registrado.")
    partes.append(h('<section class="cartao sem-borda-interna"><h2>Pagamentos</h2>{p}</section>', p=pagamentos))
    if historico is not None:
        partes.append(_cartao_historico(historico))
    return layout("Conta a pagar", juntar(partes), ctx, "contas", aviso)
