"""Páginas da Spec 010: calendário de obrigações, cadastro, detalhe com histórico, cumprimento e evidências."""

from datetime import date, timedelta
from typing import Dict, List

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
    tabela,
)
from remindme.dominio.obrigacao import EstadoObrigacao, Periodicidade, TipoEvento, TipoObrigacao
from remindme.dominio.operacoes import Operacao

CLASSE_DO_ESTADO = {
    EstadoObrigacao.PENDENTE: "aberto",
    EstadoObrigacao.AGUARDANDO_EVIDENCIA: "proximo",
    EstadoObrigacao.ATRASADA: "vencido",
    EstadoObrigacao.CUMPRIDA: "baixado",
}

DIAS_DAS_PROXIMAS = 15


def selo_obrigacao(estado: EstadoObrigacao, grande: bool = False) -> Html:
    return h(
        '<span class="selo {c}{g}">{t}</span>', c=CLASSE_DO_ESTADO[estado], g=" grande" if grande else "", t=estado.value
    )


def _responsavel(visao) -> Html:
    if visao.responsavel_ativo:
        return h("{n}", n=visao.responsavel_nome)
    return h('{n} <span class="selo inativo">responsável inativo</span>', n=visao.responsavel_nome)


def tabela_de_obrigacoes(visoes: list) -> Html:
    linhas = [
        h(
            '<tr class="{classe}"><td><a href="/obrigacoes/{id}">{nome}</a></td><td>{tipo}</td><td>{prazo}</td>'
            "<td>{responsavel}</td><td>{estado}</td></tr>",
            classe="vencido" if v.estado is EstadoObrigacao.ATRASADA else "",
            id=v.id, nome=v.nome, tipo=v.tipo.value, prazo=f.data(v.prazo), responsavel=_responsavel(v),
            estado=selo_obrigacao(v.estado),
        )
        for v in visoes
    ]
    cabecalhos = [("Obrigação", ""), ("Tipo", ""), ("Prazo", ""), ("Responsável", ""), ("Estado", "")]
    return tabela(cabecalhos, linhas, "Nenhuma obrigação encontrada.")


def pagina_calendario(ctx: Contexto, visoes: list, filtro: str, aviso=None) -> Html:
    """RF-43, RB-04: o calendário único da empresa, por prazo. As Cumpridas ficam no filtro."""
    acoes = botao_link("/obrigacoes/nova", "Nova obrigação")
    opcoes = [("", "Em aberto"), ("todas", "Todas")] + [(e.name, e.value) for e in EstadoObrigacao]
    itens = juntar(
        [
            h('<option value="{v}"{s}>{t}</option>', v=valor, s=Html(" selected") if valor == filtro else Html(""), t=texto)
            for valor, texto in opcoes
        ]
    )
    filtros = h(
        """<form class="filtros" method="get" action="/obrigacoes">
<div class="campo"><label for="estado">Estado</label><select id="estado" name="estado">{itens}</select></div>
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/obrigacoes">Limpar</a></div>
</form>""",
        itens=itens,
    )
    atrasadas = sum(1 for v in visoes if v.estado is EstadoObrigacao.ATRASADA)
    subtitulo = f"{len(visoes)} obrigação(ões), por prazo" + (f"; {atrasadas} atrasada(s)" if atrasadas else "")
    conteudo = juntar(
        [
            cabecalho("Obrigações", subtitulo, acoes),
            h('<section class="cartao">{f}</section>', f=filtros),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela_de_obrigacoes(visoes)),
        ]
    )
    return layout("Obrigações", conteudo, ctx, "obrigacoes", aviso)


def _opcoes_de_responsavel(responsaveis: list):
    return [(u.id, f"{u.nome} ({u.perfil.value})") for u in responsaveis]


def pagina_obrigacao_formulario(ctx: Contexto, responsaveis: list, valores: Valores, erros: Erros) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="/obrigacoes/nova" novalidate>
{protecao}{geral}
{nome}
<div class="linha-campos">{tipo}{periodicidade}</div>
<div class="linha-campos">{prazo}{responsavel}</div>
{exige}
<div class="acoes"><button type="submit">Cadastrar obrigação</button><a class="botao secundario" href="/obrigacoes">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        nome=campo("nome", "Nome", valores, erros, ajuda="Por exemplo, DAS, FGTS ou Aluguel da loja."),
        tipo=selecao("tipo", "Tipo", [(t.value, t.value) for t in TipoObrigacao], valores, erros, vazio="Escolha o tipo"),
        periodicidade=selecao(
            "periodicidade", "Periodicidade", [(p.value, p.value) for p in Periodicidade], valores, erros, vazio="Escolha a periodicidade"
        ),
        prazo=campo("prazo", "Prazo", valores, erros, tipo="date"),
        responsavel=selecao(
            "responsavel", "Responsável", _opcoes_de_responsavel(responsaveis), valores, erros, vazio="Escolha o responsável"
        ),
        exige=selecao("exige_evidencia", "Exige evidência?", [("nao", "Não"), ("sim", "Sim")], valores, erros),
    )
    conteudo = juntar(
        [
            cabecalho("Nova obrigação", "A obrigação nasce Pendente; o responsável é avisado 7 dias antes do prazo."),
            h('<section class="cartao">{f}</section>', f=formulario),
        ]
    )
    return layout("Nova obrigação", conteudo, ctx, "obrigacoes")


def _detalhe_do_evento(evento, nomes: Dict[str, str]) -> str:
    if evento.tipo is TipoEvento.RESPONSAVEL_ALTERADO:
        anterior, _, novo = evento.detalhe.partition(" → ")
        return f"{nomes.get(anterior, anterior)} → {nomes.get(novo, novo)}"
    if evento.destinatario_id:
        return f"para {nomes.get(evento.destinatario_id, evento.destinatario_id)}, prazo {f.data(evento.prazo)}"
    if evento.tipo is TipoEvento.GERADA:
        return ""
    return evento.detalhe


def _historico(obrigacao, nomes: Dict[str, str]) -> Html:
    itens = [
        h(
            '<li><span class="quando">{quando}</span><span><strong>{quem}</strong>: {tipo}<br><span class="mudanca">{detalhe}</span></span></li>',
            quando=f.data_hora(e.quando),
            quem=nomes.get(e.usuario_id, e.usuario_id) if e.usuario_id else "Sistema",
            tipo=e.tipo.value,
            detalhe=_detalhe_do_evento(e, nomes),
        )
        for e in obrigacao.historico
    ]
    return h(
        '<section class="cartao sem-borda-interna"><h2>Histórico</h2><ul class="historico">{i}</ul></section>', i=juntar(itens)
    )


def _evidencias(obrigacao, nomes: Dict[str, str]) -> Html:
    linhas = [
        h(
            '<tr><td><a href="/obrigacoes/{o}/evidencias/{e}">{arquivo}</a></td><td>{descricao}</td><td>{quando}</td><td>{quem}</td></tr>',
            o=obrigacao.id, e=ev.id, arquivo=ev.nome_arquivo, descricao=ev.descricao, quando=f.data_hora(ev.anexada_em),
            quem=nomes.get(ev.usuario_id, ev.usuario_id),
        )
        for ev in obrigacao.evidencias
    ]
    corpo = tabela([("Arquivo", ""), ("Descrição", ""), ("Anexada em", ""), ("Por", "")], linhas, "Nenhuma evidência anexada.")
    return h('<section class="cartao sem-borda-interna"><h2>Evidências</h2>{t}</section>', t=corpo)


def _serie(obrigacao, serie: list) -> Html:
    if len(serie) < 2:
        return Html("")
    linhas = [
        h(
            "<tr><td>{link}</td><td>{prazo}</td><td>{estado}</td></tr>",
            link=h("{p} (esta)", p="Ocorrência") if o.id == obrigacao.id else h('<a href="/obrigacoes/{i}">Ocorrência</a>', i=o.id),
            prazo=f.data(o.prazo),
            estado=selo_obrigacao(o.estado),
        )
        for o in serie
    ]
    return h(
        '<section class="cartao sem-borda-interna"><h2>Ocorrências da série</h2>{t}</section>',
        t=tabela([("Ocorrência", ""), ("Prazo", ""), ("Estado", "")], linhas, ""),
    )


def _formulario_de_arquivo(valores: Valores, erros: Erros) -> Html:
    return h(
        """<div class="linha-campos"><div class="campo"><label for="arquivo">Arquivo da evidência</label><span class="ajuda">PDF, PNG ou JPG, até 5 MB.</span>
<input id="arquivo" name="arquivo" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"{atributos}>{mensagem}</div>
{descricao}</div>""",
        atributos=Html(' aria-invalid="true" aria-describedby="erro-arquivo"') if "arquivo" in erros else Html(""),
        mensagem=h('<span class="erro" id="erro-arquivo">{m}</span>', m=erros["arquivo"]) if "arquivo" in erros else Html(""),
        descricao=campo("descricao", "Descrição da evidência", valores, erros, obrigatorio=False, ajuda="Por exemplo, guia paga, protocolo 123."),
    )


def pagina_obrigacao(
    ctx: Contexto,
    obrigacao,
    serie: list,
    nomes: Dict[str, str],
    responsaveis: list,
    responsavel_ativo: bool,
    valores: Valores,
    erros: Erros,
    formulario_com_erro: str = "",
    aviso=None,
) -> Html:
    """RF-50: dados, histórico, evidências, ocorrências da série e os formulários que o estado permite."""
    dados = h(
        """<dl class="dados">
<div><dt>Tipo</dt><dd>{tipo}</dd></div>
<div><dt>Periodicidade</dt><dd>{periodicidade}</dd></div>
<div><dt>Prazo</dt><dd>{prazo}</dd></div>
<div><dt>Responsável</dt><dd>{responsavel}</dd></div>
<div><dt>Exige evidência</dt><dd>{exige}</dd></div>
<div><dt>Cumprimento</dt><dd>{cumprimento}</dd></div>
</dl>""",
        tipo=obrigacao.tipo.value,
        periodicidade=obrigacao.periodicidade.value,
        prazo=f.data(obrigacao.prazo),
        responsavel=h("{n}", n=nomes.get(obrigacao.responsavel_id, "—"))
        if responsavel_ativo
        else h('{n} <span class="selo inativo">responsável inativo</span>', n=nomes.get(obrigacao.responsavel_id, "—")),
        exige="Sim" if obrigacao.exige_evidencia else "Não",
        cumprimento=(
            f"{f.data(obrigacao.cumprimento_em)}, por {nomes.get(obrigacao.cumprimento_por, obrigacao.cumprimento_por)}"
            if obrigacao.cumprimento_em
            else "—"
        ),
    )
    partes: List[Html] = [
        cabecalho(obrigacao.nome, "Obrigação", botao_link("/obrigacoes", "Voltar ao calendário", "secundario")),
        h('<div class="selos-do-titulo">{e}</div>', e=selo_obrigacao(obrigacao.estado, grande=True)),
    ]
    if obrigacao.aguarda_evidencia:
        partes.append(caixa_de_aviso("info", "O cumprimento foi registrado; falta anexar a evidência exigida (RB-29)."))
    if obrigacao.proxima_id:
        partes.append(h('<p>Próxima ocorrência: <a href="/obrigacoes/{i}">abrir</a>.</p>', i=obrigacao.proxima_id))
    partes.append(h('<section class="cartao">{d}</section>', d=dados))

    def erros_de(nome: str) -> Erros:
        return erros if formulario_com_erro == nome else {}

    cumprida = obrigacao.estado is EstadoObrigacao.CUMPRIDA
    if not cumprida and obrigacao.cumprimento_em is None:
        e_ = erros_de("cumprimento")
        partes.append(
            h(
                """<section class="cartao" aria-labelledby="t-cumprimento"><h2 id="t-cumprimento">Registrar cumprimento</h2>
<form class="formulario" method="post" action="/obrigacoes/{id}/cumprimento" enctype="multipart/form-data" novalidate>
{protecao}{geral}
{data}
{arquivo}
<div class="acoes"><button type="submit">Registrar cumprimento</button></div>
</form></section>""",
                id=obrigacao.id, protecao=protecao(ctx), geral=erro_geral(e_),
                data=campo("data", "Data do cumprimento", valores if e_ else {"data": ctx.hoje.isoformat()}, e_, tipo="date"),
                arquivo=_formulario_de_arquivo(valores if e_ else {}, e_),
            )
        )
    elif not cumprida:
        e_ = erros_de("evidencia")
        partes.append(
            h(
                """<section class="cartao destaque-alerta" aria-labelledby="t-evidencia"><h2 id="t-evidencia">Anexar evidência</h2>
<form class="formulario" method="post" action="/obrigacoes/{id}/evidencias" enctype="multipart/form-data" novalidate>
{protecao}{geral}
{arquivo}
<div class="acoes"><button type="submit">Anexar evidência</button></div>
</form></section>""",
                id=obrigacao.id, protecao=protecao(ctx), geral=erro_geral(e_), arquivo=_formulario_de_arquivo(valores if e_ else {}, e_),
            )
        )
    if obrigacao.estado in (EstadoObrigacao.PENDENTE, EstadoObrigacao.AGUARDANDO_EVIDENCIA):
        e_ = erros_de("prazo")
        partes.append(
            h(
                """<section class="cartao"><h2>Alterar prazo</h2>
<form class="formulario" method="post" action="/obrigacoes/{id}/prazo" novalidate>{protecao}{geral}{prazo}
<p class="secundario">A alteração vale só para esta ocorrência; a próxima segue o ritmo da série.</p>
<div class="acoes"><button class="secundario" type="submit">Alterar prazo</button></div></form></section>""",
                id=obrigacao.id, protecao=protecao(ctx), geral=erro_geral(e_),
                prazo=campo("prazo", "Novo prazo", valores if e_ else {"prazo": obrigacao.prazo.isoformat()}, e_, tipo="date"),
            )
        )
    if not cumprida:
        e_ = erros_de("responsavel")
        partes.append(
            h(
                """<section class="cartao"><h2>Alterar responsável</h2>
<form class="formulario" method="post" action="/obrigacoes/{id}/responsavel" novalidate>{protecao}{geral}{responsavel}
<div class="acoes"><button class="secundario" type="submit">Alterar responsável</button></div></form></section>""",
                id=obrigacao.id, protecao=protecao(ctx), geral=erro_geral(e_),
                responsavel=selecao(
                    "responsavel", "Responsável", _opcoes_de_responsavel(responsaveis),
                    valores if e_ else {"responsavel": obrigacao.responsavel_id}, e_,
                ),
            )
        )
    partes += [_evidencias(obrigacao, nomes), _serie(obrigacao, serie), _historico(obrigacao, nomes)]
    return layout(obrigacao.nome, juntar(partes), ctx, "obrigacoes", aviso)


def cartoes_do_painel(visoes: list, hoje: date, ctx: Contexto) -> Html:
    """RNF-15: atrasadas em destaque. RF-77: aguardando evidência. E as próximas dos 15 dias seguintes."""
    if not ctx.pode(Operacao.GERENCIAR_OBRIGACOES):
        return Html("")
    atrasadas = [v for v in visoes if v.estado is EstadoObrigacao.ATRASADA]
    aguardando = [v for v in visoes if v.aguarda_evidencia]
    proximas = [
        v for v in visoes
        if v.estado is EstadoObrigacao.PENDENTE and hoje <= v.prazo <= hoje + timedelta(days=DIAS_DAS_PROXIMAS)
    ]
    partes: List[Html] = [
        h(
            """<div class="indicadores">
  <div class="indicador{classe}"><div class="rotulo">Obrigações atrasadas</div><div class="numero">{n}</div><div class="detalhe"><a href="/obrigacoes?estado=ATRASADA">Ver as atrasadas</a></div></div>
  <div class="indicador proximo"><div class="rotulo">Obrigações nos próximos {dias} dias</div><div class="numero">{p}</div><div class="detalhe"><a href="/obrigacoes">Abrir o calendário</a></div></div>
</div>""",
            classe=" atraso" if atrasadas else "", n=len(atrasadas), dias=DIAS_DAS_PROXIMAS, p=len(proximas),
        )
    ]
    if atrasadas:
        partes.append(
            h(
                '<section class="cartao sem-borda-interna destaque-alerta"><h2>Obrigações atrasadas</h2>{t}</section>',
                t=tabela_de_obrigacoes(atrasadas),
            )
        )
    if aguardando:
        partes.append(
            h(
                '<section class="cartao sem-borda-interna destaque-alerta"><h2>Obrigações aguardando evidência</h2>{t}</section>',
                t=tabela_de_obrigacoes(aguardando),
            )
        )
    if proximas:
        partes.append(
            h(
                '<section class="cartao sem-borda-interna"><h2>Próximas obrigações</h2>{t}</section>',
                t=tabela_de_obrigacoes(proximas),
            )
        )
    return juntar(partes)
