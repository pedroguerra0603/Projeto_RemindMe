"""Páginas de usuários, permissões e troca da própria senha (Specs 002, 017 e 019). Só montam o que os serviços devolvem (INV-1)."""

from typing import List

from remindme.apresentacao.web.html import Html, h, juntar
from remindme.apresentacao.web.paginas import (
    Contexto,
    Erros,
    Valores,
    botao_link,
    cabecalho,
    campo,
    erro_geral,
    layout,
    protecao,
    selecao,
    tabela,
)
from remindme.dominio.usuario import Perfil, Usuario


PERFIS_DE_USUARIO = list(Perfil)


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
