"""Painel de cada perfil e seus gráficos (Specs 017, 018 e 004). Só monta o que os serviços devolvem (INV-1)."""

from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web import graficos as g
from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import Contexto, botao_link, cabecalho, caixa_de_aviso, layout, tabela
from remindme.apresentacao.web.paginas_auditoria import _item_do_historico
from remindme.apresentacao.web.paginas_orcamentos import _cartao_pendentes
from remindme.dominio.conta_pagar import EstadoContaPagar
from remindme.dominio.operacoes import Operacao
from remindme.dominio.orcamento import EstadoOrcamento
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario


def pagina_painel(
    ctx: Contexto,
    visoes: Optional[list],
    nomes_clientes: Dict[str, str],
    registros: Optional[list],
    usuarios: Optional[List[Usuario]],
    aviso: Optional[Tuple[str, str]] = None,
    pendentes: Optional[list] = None,
    pagamentos: Optional[list] = None,
    orcamentos: Optional[list] = None,
    contas: Optional[list] = None,
) -> Html:
    partes: List[Html] = []
    acoes = []
    if ctx.pode(Operacao.CADASTRAR_TITULO):
        acoes.append(botao_link("/titulos/novo", "Novo título"))
    if ctx.pode(Operacao.CONDUZIR_ORCAMENTO):
        acoes.append(botao_link("/orcamentos/novo", "Novo orçamento", "secundario"))
    if ctx.pode(Operacao.MANTER_CLIENTES):
        acoes.append(botao_link("/clientes/novo", "Novo cliente", "secundario"))
    primeiro_nome = ctx.usuario.nome.split()[0] if ctx.usuario.nome else ""
    partes.append(cabecalho(f"Olá, {primeiro_nome}", f.data_por_extenso(ctx.hoje).capitalize(), juntar(acoes)))
    if visoes is not None or contas is not None:
        partes.append(_regua_do_caixa(visoes, nomes_clientes, ctx, contas))

    if pendentes:
        partes.append(_cartao_pendentes(pendentes, nomes_clientes))
    partes.append(_graficos_do_perfil(ctx, visoes or [], registros or [], pagamentos or [], orcamentos or []))
    if visoes is not None:
        partes.append(_resumo_financeiro(visoes, nomes_clientes, ctx))
    if usuarios is not None:
        ativos = [u for u in usuarios if u.ativo]
        partes.append(
            h(
                """<div class="indicadores">
  <div class="indicador"><div class="rotulo">Usuários ativos</div><div class="numero">{ativos}</div><div class="detalhe">{inativos} inativo(s)</div></div>
  <div class="indicador"><div class="rotulo">Administração</div><div class="detalhe margem-topo"><a href="/usuarios">Usuários</a> e <a href="/permissoes">permissões por perfil</a></div></div>
</div>""",
                ativos=len(ativos),
                inativos=len(usuarios) - len(ativos),
            )
        )
    if registros is not None:
        operacoes = [r for r in registros if r.campo != "sessão"]
        itens = [_item_do_historico(r) for r in operacoes[-3:][::-1]]
        partes.append(
            h(
                '<section class="cartao sem-borda-interna"><h2>Últimas operações</h2>{lista}<p class="secundario rodape-cartao"><a href="/auditoria">Ver toda a auditoria</a></p></section>',
                lista=h('<ul class="historico">{i}</ul>', i=juntar(itens)) if itens else h('<p class="vazio">{t}</p>', t="Nenhuma operação registrada ainda."),
            )
        )
    if visoes is None and usuarios is None and registros is None and contas is None:
        partes.append(caixa_de_aviso("info", "O seu perfil ainda não tem funcionalidades nesta versão."))
    return layout("Painel", juntar(partes), ctx, "painel", aviso)


# Gráficos do painel: um conjunto por perfil, com os dados que o painel já tem.
MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _regua_do_caixa(visoes: Optional[list], nomes_clientes: Dict[str, str], ctx: Contexto, contas: Optional[list] = None) -> Html:
    """O destaque do painel: vencidos à esquerda do hoje e os próximos 15 dias à direita. Com as contas a pagar
    (Spec 018, RF-94), uma linha do que sai do caixa no mesmo período e o saldo previsto."""
    if visoes is None:
        return h(
            '<section class="regua-do-caixa" aria-labelledby="t-regua"><h2 id="t-regua">Régua do caixa</h2>{p}</section>',
            p=_a_pagar(contas or [], ctx, None),
        )
    marcos = []
    for v in visoes:
        dias = (v.vencimento - ctx.hoje).days
        if v.estado is EstadoTitulo.VENCIDO:
            cor = "vermelho"
        elif v.estado is EstadoTitulo.ABERTO and dias <= g.DIAS_DEPOIS:
            cor = "laranja" if v.proximo_do_vencimento else "azul"
        else:
            continue
        marcos.append((nomes_clientes.get(v.cliente_id, "Cliente"), dias, v.saldo, cor, f"/titulos/{v.id}"))
    vencidos = [m for m in marcos if m[3] == "vermelho"]
    a_vencer = [m for m in marcos if m[3] != "vermelho"]
    resumo = h(
        '<p class="regua-resumo">{rotulo}<span class="vermelho">{nv} vencido(s), {sv}</span><span class="laranja">{na} a vencer em 15 dias, {sa}</span></p>',
        # Com a linha do que há a pagar, cada linha diz de que lado do caixa está.
        rotulo=Html('<a href="/titulos">A receber</a>') if contas is not None else Html(""),
        nv=len(vencidos), sv=f.moeda(sum((m[2] for m in vencidos), Decimal("0.00"))),
        na=len(a_vencer), sa=f.moeda(sum((m[2] for m in a_vencer), Decimal("0.00"))),
    )
    a_receber = sum((m[2] for m in marcos), Decimal("0.00"))
    return h(
        '<section class="regua-do-caixa" aria-labelledby="t-regua"><h2 id="t-regua">Régua do caixa</h2>{r}{g}{p}</section>',
        r=resumo, g=g.regua(marcos, f.moeda_curta, f.data(ctx.hoje)[:5]),
        p=_a_pagar(contas, ctx, a_receber) if contas is not None else Html(""),
    )


def _a_pagar(contas: list, ctx: Contexto, a_receber: Optional[Decimal]) -> Html:
    """RF-94: o que vence para pagar (vencidas e próximos 15 dias) e, com os títulos, o saldo previsto."""
    limite = ctx.hoje + timedelta(days=g.DIAS_DEPOIS)
    vencidas = [c for c in contas if c.estado is EstadoContaPagar.VENCIDA]
    a_vencer = [c for c in contas if c.estado is EstadoContaPagar.ABERTA and c.vencimento <= limite]
    total_vencidas = sum((c.saldo for c in vencidas), Decimal("0.00"))
    total_a_vencer = sum((c.saldo for c in a_vencer), Decimal("0.00"))
    saldo = (
        h(
            '<span class="saldo-previsto {sinal}">Saldo previsto em 15 dias: <strong>{v}</strong></span>',
            sinal="negativo" if a_receber - total_vencidas - total_a_vencer < 0 else "positivo",
            v=f.moeda(a_receber - total_vencidas - total_a_vencer),
        )
        if a_receber is not None
        else Html("")
    )
    return h(
        '<p class="regua-resumo regua-pagar"><a href="/contas-a-pagar">A pagar</a>'
        '<span class="vermelho">{nv} vencida(s), {sv}</span><span class="laranja">{na} a vencer em 15 dias, {sa}</span>{saldo}</p>',
        nv=len(vencidas), sv=f.moeda(total_vencidas), na=len(a_vencer), sa=f.moeda(total_a_vencer), saldo=saldo,
    )


def _cartao_grafico(titulo: str, grafico: Html) -> Html:
    return h('<section class="cartao cartao-grafico"><h2>{t}</h2>{g}</section>', t=titulo, g=grafico)


def _graficos_do_perfil(ctx: Contexto, visoes: list, registros: list, pagamentos: list, orcamentos: list) -> Html:
    perfil = ctx.usuario.perfil
    if perfil is Perfil.DONO:
        cartoes = [
            _cartao_grafico("Recebido nos últimos 6 meses", g.colunas(_recebido_por_mes(pagamentos, ctx.hoje), f.moeda_curta, "Recebido por mês")),
            _cartao_grafico("Carteira de títulos", g.anel(_carteira(visoes), f.moeda, "Carteira de títulos por situação")),
        ]
    elif perfil is Perfil.ADMINISTRADOR:
        acoes = _acoes_dos_ultimos_30_dias(registros, ctx.hoje)
        cartoes = [
            _cartao_grafico("Ações por usuário (30 dias)", g.barras(_contar(acoes, lambda r: r.responsavel, "azul"), _vezes, "Ações por usuário")),
            _cartao_grafico("Ações mais comuns (30 dias)", g.barras(_contar(acoes, lambda r: r.operacao, "laranja")[:5], _vezes, "Ações mais comuns")),
        ]
    elif perfil is Perfil.OPERADOR_FINANCEIRO:
        cartoes = [
            _cartao_grafico("Meus orçamentos por estado", g.barras(_orcamentos_por_estado(orcamentos), _vezes, "Orçamentos por estado")),
            _cartao_grafico("A receber nos próximos 7 dias", g.colunas(_proximos_7_dias(visoes, ctx.hoje), f.moeda_curta, "A receber por dia")),
        ]
    elif perfil is Perfil.CONTADOR:
        cartoes = [_cartao_grafico("Carteira por atraso", g.barras(_faixas_de_atraso(visoes, ctx.hoje), f.moeda, "Saldo por faixa de atraso"))]
    else:
        return Html("")
    return h('<div class="grade-2">{c}</div>', c=juntar(cartoes))


def _vezes(quantidade: Decimal) -> str:
    return f"{quantidade:.0f}"


def _recebido_por_mes(pagamentos: list, hoje: date) -> list:
    """Os 6 meses até o atual, do mais antigo ao mais recente."""
    meses = []
    ano, mes = hoje.year, hoje.month
    for _ in range(6):
        meses.insert(0, (ano, mes))
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return [
        (MESES[m - 1], sum((p.valor for p in pagamentos if (p.data.year, p.data.month) == (a, m)), Decimal("0.00")), "azul")
        for a, m in meses
    ]


def _carteira(visoes: list) -> list:
    def soma(estado, campo):
        return sum((getattr(v, campo) for v in visoes if v.estado is estado), Decimal("0.00"))

    return [
        ("A receber em dia", soma(EstadoTitulo.ABERTO, "saldo"), "azul"),
        ("Vencido", soma(EstadoTitulo.VENCIDO, "saldo"), "vermelho"),
        ("Recebido (baixado)", soma(EstadoTitulo.BAIXADO, "valor"), "verde"),
    ]


def _acoes_dos_ultimos_30_dias(registros: list, hoje: date) -> list:
    """Ações de pessoas (sem entradas e saídas do sistema e sem rotinas automáticas)."""
    inicio = hoje - timedelta(days=30)
    return [r for r in registros if not r.automatica and r.campo != "sessão" and r.data_hora.date() >= inicio]


def _contar(registros: list, chave, cor: str) -> list:
    return [(nome, Decimal(total), cor) for nome, total in Counter(chave(r) for r in registros).most_common()]


def _orcamentos_por_estado(orcamentos: list) -> list:
    cores = {
        EstadoOrcamento.RASCUNHO: "azul",
        EstadoOrcamento.PENDENTE_DE_ALCADA: "laranja",
        EstadoOrcamento.CANCELADO: "cinza",
    }
    return [(estado.value, Decimal(sum(1 for o in orcamentos if o.estado is estado)), cor) for estado, cor in cores.items()]


def _proximos_7_dias(visoes: list, hoje: date) -> list:
    dias = [hoje + timedelta(days=n) for n in range(7)]
    return [
        (dia.strftime("%d/%m"), sum((v.saldo for v in visoes if v.estado is EstadoTitulo.ABERTO and v.vencimento == dia), Decimal("0.00")), "azul")
        for dia in dias
    ]


def _faixas_de_atraso(visoes: list, hoje: date) -> list:
    def soma(minimo, maximo):
        return sum(
            (v.saldo for v in visoes if v.estado is EstadoTitulo.VENCIDO and minimo <= (hoje - v.vencimento).days <= maximo),
            Decimal("0.00"),
        )

    em_dia = sum((v.saldo for v in visoes if v.estado is EstadoTitulo.ABERTO), Decimal("0.00"))
    return [
        ("Em dia", em_dia, "azul"),
        ("Até 30 dias", soma(1, 30), "laranja"),
        ("31 a 60 dias", soma(31, 60), "vermelho"),
        ("Mais de 60 dias", soma(61, 100000), "vermelho"),
    ]


def _resumo_financeiro(visoes: list, nomes_clientes: Dict[str, str], ctx: Contexto) -> Html:
    em_aberto = [v for v in visoes if v.estado in (EstadoTitulo.ABERTO, EstadoTitulo.VENCIDO)]
    vencidos = [v for v in visoes if v.estado is EstadoTitulo.VENCIDO]
    proximos = [v for v in visoes if v.proximo_do_vencimento]
    baixados = [v for v in visoes if v.estado is EstadoTitulo.BAIXADO]
    soma = lambda lista: sum((v.saldo for v in lista), Decimal("0.00"))  # noqa: E731
    indicadores = h(
        """<div class="indicadores">
  <div class="indicador"><div class="rotulo">A receber</div><div class="numero">{receber}</div><div class="detalhe">{n_aberto} título(s) Aberto(s) ou Vencido(s)</div></div>
  <div class="indicador atraso"><div class="rotulo">Em atraso</div><div class="numero">{atraso}</div><div class="detalhe">{n_vencido} título(s) Vencido(s)</div></div>
  <div class="indicador proximo"><div class="rotulo">Vencem em breve</div><div class="numero">{n_proximo}</div><div class="detalhe">{proximo} nos próximos dias</div></div>
  <div class="indicador recebido"><div class="rotulo">Baixados</div><div class="numero">{n_baixado}</div><div class="detalhe">títulos pagos por completo</div></div>
</div>""",
        receber=f.moeda(soma(em_aberto)),
        n_aberto=len(em_aberto),
        atraso=f.moeda(soma(vencidos)),
        n_vencido=len(vencidos),
        n_proximo=len(proximos),
        proximo=f.moeda(soma(proximos)),
        n_baixado=len(baixados),
    )
    linhas_vencidos = [
        h(
            '<tr class="vencido"><td><a href="/titulos/{id}">{cliente}</a></td><td>{venc}</td><td class="numero">{dias}</td><td class="numero">{saldo}</td></tr>',
            id=v.id,
            cliente=nomes_clientes.get(v.cliente_id, "Cliente"),
            venc=f.data(v.vencimento),
            dias=(ctx.hoje - v.vencimento).days,
            saldo=f.moeda(v.saldo),
        )
        for v in sorted(vencidos, key=lambda v: v.vencimento)
    ]
    linhas_proximos = [
        h(
            '<tr><td><a href="/titulos/{id}">{cliente}</a></td><td>{venc}</td><td class="numero">{saldo}</td></tr>',
            id=v.id,
            cliente=nomes_clientes.get(v.cliente_id, "Cliente"),
            venc=f.data(v.vencimento),
            saldo=f.moeda(v.saldo),
        )
        for v in sorted(proximos, key=lambda v: v.vencimento)
    ]
    return h(
        """{indicadores}
<div class="grade-2">
  <section class="cartao sem-borda-interna" aria-labelledby="t-vencidos"><h2 id="t-vencidos">Títulos vencidos</h2>{vencidos}</section>
  <section class="cartao sem-borda-interna" aria-labelledby="t-proximos"><h2 id="t-proximos">Próximos do vencimento</h2>{proximos}</section>
</div>""",
        indicadores=indicadores,
        vencidos=tabela([("Cliente", ""), ("Vencimento", ""), ("Dias em atraso", "numero"), ("Saldo", "numero")], linhas_vencidos, "Nenhum título vencido."),
        proximos=tabela([("Cliente", ""), ("Vencimento", ""), ("Saldo", "numero")], linhas_proximos, "Nenhum título vence nos próximos dias."),
    )
