"""Páginas HTML da interface web (Spec 017). Só montam o que os serviços devolvem; nenhuma regra aqui (INV-1)."""

from dataclasses import dataclass
from datetime import date
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html, e, h, juntar
from remindme.dominio.operacoes import Operacao
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Perfil, Usuario

Erros = Dict[str, str]
Valores = Dict[str, str]


@dataclass(frozen=True)
class Contexto:
    """Quem está usando a página: o usuário da sessão, as operações do perfil e a proteção dos formulários."""

    usuario: Usuario
    operacoes: FrozenSet[Operacao]
    protecao: str
    hoje: date

    def pode(self, operacao: Operacao) -> bool:
        return operacao in self.operacoes


MENU = (
    ("painel", "/painel", "Painel", "◧", None),
    ("empresa", "/empresa", "Empresa", "▣", None),
    ("titulos", "/titulos", "Títulos", "▤", Operacao.CONSULTAR_TITULOS),
    ("orcamentos", "/orcamentos", "Orçamentos", "◇", Operacao.CONDUZIR_ORCAMENTO),
    ("mensagens", "/mensagens", "Mensagens enviadas", "✉", Operacao.CONSULTAR_MENSAGENS),
    ("clientes", "/clientes", "Clientes", "◉", Operacao.CONSULTAR_CLIENTES),
    ("contas", "/contas-a-pagar", "Contas a pagar", "▥", Operacao.CONSULTAR_CONTAS_PAGAR),
    ("fornecedores", "/fornecedores", "Fornecedores", "◍", Operacao.CONSULTAR_FORNECEDORES),
    ("auditoria", "/auditoria", "Auditoria", "⌕", Operacao.CONSULTAR_AUDITORIA),
    ("usuarios", "/usuarios", "Usuários", "◎", Operacao.ADMINISTRAR_USUARIOS),
    ("permissoes", "/permissoes", "Permissões", "▦", Operacao.ADMINISTRAR_USUARIOS),
)

CLASSE_DO_ESTADO = {
    EstadoTitulo.ABERTO: "aberto",
    EstadoTitulo.VENCIDO: "vencido",
    EstadoTitulo.BAIXADO: "baixado",
    EstadoTitulo.CANCELADO: "cancelado",
}


PERFIS_DE_USUARIO = list(Perfil)


# Estrutura


DESCRICAO_PADRAO = "RemindMe: gestão de recebíveis, orçamentos e clientes de micro e pequenas empresas."


def _documento_html(titulo: str, corpo: Html, descricao: str = DESCRICAO_PADRAO) -> Html:
    return h(
        """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} | RemindMe</title>
<meta name="description" content="{descricao}">
<meta name="theme-color" content="#0f1e3d">
<link rel="icon" href="/estatico/icone.svg" type="image/svg+xml">
<link rel="stylesheet" href="/estatico/estilo.css">
<script src="/estatico/tema.js"></script>
</head>
<body>
{corpo}
</body>
</html>
""",
        titulo=titulo,
        corpo=corpo,
        descricao=descricao,
    )


def layout(titulo: str, conteudo: Html, ctx: Contexto, secao: str = "", aviso: Optional[Tuple[str, str]] = None) -> Html:
    itens = juntar(
        h(
            '<li><a href="{href}"{atual}><span class="icone" aria-hidden="true">{icone}</span>{rotulo}</a></li>',
            href=href,
            atual=Html(' aria-current="page"') if chave == secao else Html(""),
            icone=icone,
            rotulo=rotulo,
        )
        for chave, href, rotulo, icone, operacao in MENU
        if operacao is None or ctx.pode(operacao)
    )
    corpo = h(
        """<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo">
  <a class="marca" href="/painel"><img src="/estatico/icone.svg" alt="">RemindMe</a>
  <div class="quem">
    <span class="nome-completo"><strong>{nome}</strong></span>
    <span class="perfil">{perfil}</span>
    <button id="trocar-tema" class="discreto botao-tema" type="button" hidden aria-label="Trocar entre tema claro e escuro" title="Tema claro/escuro">Tema</button>
    <a class="botao discreto" href="/trocar-senha">Trocar senha</a>
    <form method="post" action="/sair">{protecao}<button class="discreto" type="submit">Sair</button></form>
  </div>
</header>
<div class="corpo">
  <nav class="menu" aria-label="Principal"><ul>{itens}</ul></nav>
  <main id="conteudo">{aviso}{conteudo}</main>
</div>""",
        nome=ctx.usuario.nome,
        perfil=ctx.usuario.perfil.value,
        protecao=protecao(ctx),
        itens=itens,
        aviso=caixa_de_aviso(*aviso) if aviso else Html(""),
        conteudo=conteudo,
    )
    return _documento_html(titulo, corpo)


def cabecalho(titulo: str, subtitulo: str = "", acoes: Html = Html("")) -> Html:
    return h(
        '<div class="cabecalho"><div><h1>{titulo}</h1>{subtitulo}</div><div class="acoes">{acoes}</div></div>',
        titulo=titulo,
        subtitulo=h("<p>{t}</p>", t=subtitulo) if subtitulo else Html(""),
        acoes=acoes,
    )


def caixa_de_aviso(tipo: str, texto: str) -> Html:
    papel = "alert" if tipo == "erro" else "status"
    return h('<div class="aviso {tipo}" role="{papel}">{texto}</div>', tipo=tipo, papel=papel, texto=texto)


def protecao(ctx: Contexto) -> Html:
    return h('<input type="hidden" name="protecao" value="{p}">', p=ctx.protecao)


def botao_link(href: str, texto: str, classe: str = "") -> Html:
    return h('<a class="botao {classe}" href="{href}">{texto}</a>', classe=classe, href=href, texto=texto)


def selo_estado(estado: EstadoTitulo, grande: bool = False) -> Html:
    return h(
        '<span class="selo {classe}{grande}">{texto}</span>',
        classe=CLASSE_DO_ESTADO[estado],
        grande=" grande" if grande else "",
        texto=estado.value,
    )


def selo_proximo() -> Html:
    return Html('<span class="selo proximo">Próximo do vencimento</span>')


# Campos


def _erro_do_campo(nome: str, erros: Erros) -> Tuple[Html, Html]:
    if nome not in erros:
        return Html(""), Html("")
    return (
        h(' aria-invalid="true" aria-describedby="erro-{n}"', n=nome),
        h('<span class="erro" id="erro-{n}">{m}</span>', n=nome, m=erros[nome]),
    )


def campo(
    nome: str,
    rotulo: str,
    valores: Valores,
    erros: Erros,
    tipo: str = "text",
    ajuda: str = "",
    obrigatorio: bool = True,
    extra: str = "",
) -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    return h(
        """<div class="campo"><label for="{n}">{rotulo}</label>{ajuda}
<input id="{n}" name="{n}" type="{tipo}" value="{valor}"{obrigatorio}{atributos}{extra}>{mensagem}</div>""",
        n=nome,
        rotulo=rotulo,
        ajuda=h('<span class="ajuda">{a}</span>', a=ajuda) if ajuda else Html(""),
        tipo=tipo,
        valor=valores.get(nome, ""),
        obrigatorio=Html(" required") if obrigatorio else Html(""),
        atributos=atributos,
        extra=Html(" " + extra) if extra else Html(""),
        mensagem=mensagem,
    )


def selecao(
    nome: str,
    rotulo: str,
    opcoes: Iterable[Tuple[str, str]],
    valores: Valores,
    erros: Erros,
    vazio: Optional[str] = None,
    obrigatorio: bool = True,
) -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    escolhido = valores.get(nome, "")
    itens = [h('<option value="">{t}</option>', t=vazio)] if vazio is not None else []
    itens += [
        h('<option value="{v}"{s}>{t}</option>', v=valor, s=Html(" selected") if valor == escolhido else Html(""), t=texto)
        for valor, texto in opcoes
    ]
    return h(
        '<div class="campo"><label for="{n}">{rotulo}</label><select id="{n}" name="{n}"{obrigatorio}{atributos}>{itens}</select>{mensagem}</div>',
        n=nome,
        rotulo=rotulo,
        obrigatorio=Html(" required") if obrigatorio else Html(""),
        atributos=atributos,
        itens=juntar(itens),
        mensagem=mensagem,
    )


def area(nome: str, rotulo: str, valores: Valores, erros: Erros, ajuda: str = "") -> Html:
    atributos, mensagem = _erro_do_campo(nome, erros)
    return h(
        '<div class="campo"><label for="{n}">{rotulo}</label>{ajuda}<textarea id="{n}" name="{n}" required{atributos}>{valor}</textarea>{mensagem}</div>',
        n=nome,
        rotulo=rotulo,
        ajuda=h('<span class="ajuda">{a}</span>', a=ajuda) if ajuda else Html(""),
        atributos=atributos,
        valor=valores.get(nome, ""),
        mensagem=mensagem,
    )


def erro_geral(erros: Erros) -> Html:
    return caixa_de_aviso("erro", erros["_"]) if "_" in erros else Html("")


def tabela(cabecalhos: Sequence[Tuple[str, str]], linhas: List[Html], vazio: str) -> Html:
    if not linhas:
        return h('<p class="vazio">{v}</p>', v=vazio)
    cabeca = juntar(h('<th scope="col" class="{c}">{t}</th>', c=classe, t=texto) for texto, classe in cabecalhos)
    return h('<div class="tabela"><table><thead><tr>{c}</tr></thead><tbody>{l}</tbody></table></div>', c=cabeca, l=juntar(linhas))


def pagina_motivo(
    ctx: Contexto, titulo_pagina: str, explicacao: str, acao: str, voltar: str, botao: str, valores: Valores, erros: Erros,
    secao: str = "titulos",
) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="{acao}" novalidate>
{protecao}{geral}
{motivo}
<div class="acoes"><button class="perigo" type="submit">{botao}</button><a class="botao secundario" href="{voltar}">Voltar</a></div>
</form>""",
        acao=acao,
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        motivo=area("motivo", "Motivo", valores, erros, ajuda="Obrigatório. Fica registrado na auditoria."),
        botao=botao,
        voltar=voltar,
    )
    conteudo = juntar([cabecalho(titulo_pagina, explicacao), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout(titulo_pagina, conteudo, ctx, secao)


# Auditoria


def _descrever(registro: str) -> Tuple[str, Optional[str]]:
    partes = registro.split(", ")
    tipo, _, chave = partes[0].partition(" ")
    if tipo == "titulo":
        return ("Pagamento do título " if len(partes) > 1 else "Título ") + chave[:8], f"/titulos/{chave}"
    if tipo == "cliente":
        return "Cliente " + chave[:8], f"/clientes/{chave}"
    if tipo == "empresa":
        return "Dados da empresa", "/empresa"
    if tipo == "orcamento":
        return ("Item do orçamento " if len(partes) > 1 else "Orçamento ") + chave[:8], f"/orcamentos/{chave}"
    if tipo == "fornecedor":
        return "Fornecedor " + chave[:8], f"/fornecedores/{chave}"
    if tipo == "conta_pagar":
        return ("Pagamento da conta " if len(partes) > 1 else "Conta a pagar ") + chave[:8], f"/contas-a-pagar/{chave}"
    if tipo == "usuario":
        return "Usuário " + chave[:8], f"/usuarios/{chave}"
    return registro, "/permissoes" if registro == "permissões" else None


def _valor_exibido(campo_: Optional[str], texto: Optional[str]) -> str:
    if texto is None:
        return "—"
    if campo_ == "valor":
        lido = f.ler_valor(texto)
        return f.moeda(lido) if lido is not None else texto
    if campo_ in ("desconto", "desconto solicitado"):
        lido = f.ler_valor(texto)
        return f.percentual(lido) if lido is not None else texto
    if campo_ == "documento":
        return f.documento(texto)
    if campo_ == "contato":
        return f.contato(texto)
    return texto


def _mudanca(r) -> Html:
    if not r.campo:
        return Html("")
    return h(
        "<strong>{campo}</strong>: {anterior} → {novo}{motivo}",
        campo=r.campo,
        anterior=_valor_exibido(r.campo, r.valor_anterior),
        novo=_valor_exibido(r.campo, r.valor_novo),
        motivo=h(' <span class="secundario">(motivo: {m})</span>', m=r.motivo) if r.motivo else Html(""),
    )


def _item_do_historico(r) -> Html:
    return h(
        '<li><span class="quando">{quando}</span><span><strong>{quem}</strong>: {operacao}<br><span class="mudanca">{mudanca}</span></span></li>',
        quando=f.data_hora(r.data_hora),
        quem=r.responsavel,
        operacao=r.operacao,
        mudanca=_mudanca(r),
    )


def _cartao_historico(historico: list) -> Html:
    itens = [_item_do_historico(r) for r in historico]
    lista = h('<ul class="historico">{i}</ul>', i=juntar(itens)) if itens else h('<p class="vazio">{t}</p>', t="Sem histórico.")
    return h('<section class="cartao sem-borda-interna"><h2>Histórico</h2>{l}</section>', l=lista)


def pagina_auditoria(ctx: Contexto, registros: list, opcoes, valores: Valores, erros: Erros) -> Html:
    filtros = h(
        """<form class="filtros" method="get" action="/auditoria">
{quem}{operacao}{de}{ate}
<div class="acoes"><button class="secundario" type="submit">Filtrar</button><a href="/auditoria">Limpar</a></div>
</form>""",
        quem=selecao("usuario", "Responsável", list(opcoes.responsaveis.items()), valores, erros, vazio="Todos", obrigatorio=False),
        operacao=selecao("operacao", "Operação", [(o, o) for o in opcoes.operacoes], valores, erros, vazio="Todas", obrigatorio=False),
        de=campo("de", "De", valores, erros, tipo="date", obrigatorio=False),
        ate=campo("fim", "Até", valores, erros, tipo="date", obrigatorio=False),
    )
    linhas = []
    for r in registros:
        descricao, link = _descrever(r.registro_afetado)
        afetado = h('<a href="{l}">{d}</a>', l=link, d=descricao) if link else e(descricao)
        linhas.append(
            h(
                "<tr><td class=\"mono\">{quando}</td><td>{quem}</td><td>{operacao}</td><td>{afetado}</td><td>{mudanca}</td></tr>",
                quando=f.data_hora(r.data_hora),
                quem=r.responsavel,
                operacao=r.operacao,
                afetado=afetado,
                mudanca=_mudanca(r),
            )
        )
    filtro_registro = valores.get("registro", "")
    subtitulo = f"{len(registros)} registro(s), em ordem cronológica. Os registros não podem ser alterados nem excluídos."
    partes = [
        cabecalho("Auditoria", subtitulo),
        erro_geral(erros),
        h('<section class="cartao">{f}</section>', f=filtros),
    ]
    if filtro_registro:
        partes.append(caixa_de_aviso("info", "Mostrando só o histórico de um registro."))
    partes.append(
        h(
            '<section class="cartao sem-borda-interna">{t}</section>',
            t=tabela([("Data e hora", ""), ("Responsável", ""), ("Operação", ""), ("Registro", ""), ("Alteração", "")], linhas, "Nenhum registro para os filtros escolhidos."),
        )
    )
    return layout("Auditoria", juntar(partes), ctx, "auditoria")


# Usuários e permissões


def _selo_situacao(usuario: Usuario) -> Html:
    return Html('<span class="selo ativo">Ativo</span>') if usuario.ativo else Html('<span class="selo inativo">Inativo</span>')


def pagina_usuarios(ctx: Contexto, usuarios: List[Usuario], aviso=None) -> Html:
    linhas = [
        h(
            '<tr><td><a href="/usuarios/{id}">{nome}</a></td><td>{email}</td><td>{perfil}</td><td>{situacao}</td></tr>',
            id=u.id,
            nome=u.nome,
            email=u.email,
            perfil=u.perfil.value,
            situacao=_selo_situacao(u),
        )
        for u in usuarios
    ]
    conteudo = juntar(
        [
            cabecalho("Usuários", "Cada usuário tem exatamente um perfil.", botao_link("/usuarios/novo", "Novo usuário")),
            h('<section class="cartao sem-borda-interna">{t}</section>', t=tabela([("Nome", ""), ("E-mail", ""), ("Perfil", ""), ("Situação", "")], linhas, "Nenhum usuário.")),
        ]
    )
    return layout("Usuários", conteudo, ctx, "usuarios", aviso)


def pagina_usuario_formulario(ctx: Contexto, valores: Valores, erros: Erros) -> Html:
    formulario = h(
        """<form class="formulario" method="post" action="/usuarios/novo" novalidate>
{protecao}{geral}
{nome}
<div class="linha-campos">{email}{perfil}</div>
{senha}
<div class="acoes"><button type="submit">Cadastrar usuário</button><a class="botao secundario" href="/usuarios">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        nome=campo("nome", "Nome", valores, erros),
        email=campo("email", "E-mail", valores, erros, tipo="email"),
        perfil=selecao("perfil", "Perfil", [(p.name, p.value) for p in PERFIS_DE_USUARIO], valores, erros, vazio="Escolha o perfil"),
        senha=campo("senha", "Senha provisória", valores, erros, tipo="password", ajuda="Pelo menos 8 caracteres. Informe-a ao usuário.", extra='autocomplete="new-password"'),
    )
    conteudo = juntar([cabecalho("Novo usuário"), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Novo usuário", conteudo, ctx, "usuarios")


def pagina_trocar_senha(ctx: Contexto, erros: Erros) -> Html:
    """RF-95: os campos nunca levam valor, nem depois de um erro."""
    formulario = h(
        """<form class="formulario" method="post" action="/trocar-senha" novalidate>
{protecao}{geral}
{atual}
{nova}
{confirmacao}
<div class="acoes"><button type="submit">Trocar senha</button><a class="botao secundario" href="/painel">Cancelar</a></div>
</form>""",
        protecao=protecao(ctx),
        geral=erro_geral(erros),
        atual=campo("senha_atual", "Senha atual", {}, erros, tipo="password", extra='autocomplete="current-password"'),
        nova=campo("nova_senha", "Nova senha", {}, erros, tipo="password", ajuda="Pelo menos 8 caracteres.", extra='autocomplete="new-password"'),
        confirmacao=campo("confirmacao", "Repita a nova senha", {}, erros, tipo="password", extra='autocomplete="new-password"'),
    )
    conteudo = juntar([cabecalho("Trocar senha"), h('<section class="cartao">{f}</section>', f=formulario)])
    return layout("Trocar senha", conteudo, ctx, "")


def pagina_usuario(ctx: Contexto, usuario: Usuario, valores: Valores, erros: Erros, aviso=None) -> Html:
    dados = h(
        '<dl class="dados"><div><dt>E-mail</dt><dd>{email}</dd></div><div><dt>Perfil</dt><dd>{perfil}</dd></div><div><dt>Situação</dt><dd>{situacao}</dd></div></dl>',
        email=usuario.email,
        perfil=usuario.perfil.value,
        situacao=_selo_situacao(usuario),
    )
    partes = [cabecalho(usuario.nome, "Usuário"), erro_geral(erros), h('<section class="cartao">{d}</section>', d=dados)]
    if usuario.ativo:
        partes.append(
            h(
                """<div class="grade-2">
<section class="cartao"><h2>Alterar perfil</h2>
<form class="formulario" method="post" action="/usuarios/{id}/perfil" novalidate>{protecao}{perfil}
<div class="acoes"><button type="submit">Alterar perfil</button></div></form></section>
<section class="cartao"><h2>Inativar usuário</h2><p class="secundario">O usuário perde o acesso na hora. O histórico dele é preservado.</p>
<form method="post" action="/usuarios/{id}/inativacao">{protecao}<button class="perigo" type="submit">Inativar usuário</button></form></section>
</div>""",
                id=usuario.id,
                protecao=protecao(ctx),
                perfil=selecao("perfil", "Novo perfil", [(p.name, p.value) for p in PERFIS_DE_USUARIO], valores or {"perfil": usuario.perfil.name}, erros),
            )
        )
    else:
        partes.append(
            h(
                """<section class="cartao"><h2>Ativar usuário</h2><p class="secundario">Libera a entrada com o e-mail e a senha que a pessoa escolheu ao criar a conta.</p>
<form method="post" action="/usuarios/{id}/ativacao">{protecao}<button type="submit">Ativar usuário</button></form></section>""",
                id=usuario.id,
                protecao=protecao(ctx),
            )
        )
    partes.append(h('<p><a href="/auditoria?registro=usuario+{id}">Histórico deste usuário</a></p>', id=usuario.id))
    return layout(usuario.nome, juntar(partes), ctx, "usuarios", aviso)


def pagina_permissoes(ctx: Contexto, linhas_da_matriz: list, aviso=None) -> Html:
    cabecalhos = h("<th scope=\"col\">Operação</th>{p}", p=juntar(h('<th scope="col">{p}</th>', p=perfil.value) for perfil in Perfil))
    linhas = []
    for linha in linhas_da_matriz:
        celulas = []
        for perfil in Perfil:
            celula = linha.celulas[perfil]
            texto = "Permitido" if celula.permitido else "Negado"
            classe = "sim" if celula.permitido else "nao"
            if celula.fixada is not None:
                celulas.append(
                    h('<td><span class="celula {c} fixa" title="{m}">🔒 {t}</span></td>', c=classe, m=celula.fixada.motivo, t=texto)
                )
            else:
                celulas.append(
                    h(
                        """<td><form method="post" action="/permissoes">{protecao}<input type="hidden" name="perfil" value="{perfil}"><input type="hidden" name="operacao" value="{operacao}"><input type="hidden" name="acao" value="{acao}"><button class="{c}" type="submit" title="{dica}">{t}</button></form></td>""",
                        protecao=protecao(ctx),
                        perfil=perfil.name,
                        operacao=linha.operacao.name,
                        acao="retirar" if celula.permitido else "conceder",
                        c=classe,
                        dica=("Retirar" if celula.permitido else "Conceder") + f" a permissão de {perfil.value}",
                        t=texto,
                    )
                )
        linhas.append(h("<tr><th scope=\"row\">{o}</th>{c}</tr>", o=linha.operacao.value, c=juntar(celulas)))
    conteudo = juntar(
        [
            cabecalho("Permissões por perfil", "Clique em uma célula para conceder ou retirar. 🔒 indica permissão fixada por regra de negócio, que não muda por configuração."),
            h('<section class="cartao sem-borda-interna"><div class="tabela"><table class="matriz"><thead><tr>{c}</tr></thead><tbody>{l}</tbody></table></div></section>', c=cabecalhos, l=juntar(linhas)),
        ]
    )
    return layout("Permissões", conteudo, ctx, "permissoes", aviso)


# Erros


def pagina_erro(codigo: int, titulo: str, mensagem: str, correlacao: Optional[str] = None, com_volta: bool = True) -> Html:
    corpo = h(
        """<main class="erro-pagina" id="conteudo">
<div class="codigo">{codigo}</div>
<h1>{titulo}</h1>
<p>{mensagem}</p>
{correlacao}
{volta}
</main>""",
        codigo=codigo,
        titulo=titulo,
        mensagem=mensagem,
        correlacao=h('<p class="secundario">Identificador para o suporte: <span class="mono">{c}</span></p>', c=correlacao) if correlacao else Html(""),
        volta=Html('<p><a class="botao secundario" href="/painel">Voltar ao painel</a></p>') if com_volta else Html(""),
    )
    return _documento_html(titulo, corpo)
