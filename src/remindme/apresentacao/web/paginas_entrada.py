"""Telas públicas da interface web: entrar e criar conta (Specs 017 e 002). Nenhuma regra aqui (INV-1)."""

from remindme.apresentacao.web.html import h, Html
from remindme.apresentacao.web.paginas import (
    caixa_de_aviso,
    campo,
    _documento_html,
    erro_geral,
    Erros,
    selecao,
    Valores,
)
from remindme.dominio.usuario import Perfil


# Telas públicas: entrar e criar conta. Painel da marca à esquerda (com a régua do caixa em miniatura,
# só ilustrativa) e o formulário à direita.
_REGUA_ILUSTRATIVA = Html(
    """<svg class="regua-ilustrativa" viewBox="-12 -6 224 50" aria-hidden="true" focusable="false">
<line class="eixo" x1="0" y1="34" x2="200" y2="34"/><line class="hoje" x1="133" y1="0" x2="133" y2="37"/>
<line class="haste" x1="58" y1="34" x2="58" y2="28"/><circle class="vermelho" cx="58" cy="28" r="3.2"/><text x="58" y="21">R$ 680</text>
<line class="haste" x1="102" y1="34" x2="102" y2="14"/><circle class="vermelho" cx="102" cy="14" r="3.2"/><text x="102" y="7">R$ 3,8 mil</text>
<line class="haste" x1="146" y1="34" x2="146" y2="28"/><circle class="laranja" cx="146" cy="28" r="3.2"/><text x="146" y="21">R$ 1,2 mil</text>
<line class="haste" x1="186" y1="34" x2="186" y2="28"/><circle class="azul" cx="186" cy="28" r="3.2"/><text x="186" y="21">R$ 720</text>
<text class="rotulo" x="133" y="44">hoje</text>
</svg>"""
)


def _tela_publica(titulo: str, descricao: str, conteudo: Html) -> Html:
    corpo = h(
        """<div class="publica">
  <aside class="publica-marca">
    <div class="marca marca-clara"><img src="/estatico/icone.svg" alt="">RemindMe</div>
    <p class="publica-frase">Cada cobrança e cada prazo no dia certo.</p>
    <p class="publica-apoio">Títulos, orçamentos e clientes da sua empresa, com o que vence hoje à vista.</p>
    {regua}
  </aside>
  <main class="publica-conteudo" id="conteudo">{conteudo}</main>
</div>""",
        regua=_REGUA_ILUSTRATIVA,
        conteudo=conteudo,
    )
    return _documento_html(titulo, corpo, descricao)


def pagina_entrar(protecao_da_entrada: str, email: str = "", erro: str = "", aviso: str = "", volta: str = "") -> Html:
    conteudo = h(
        """<h1>Entrar</h1>
{aviso}{erro}
<form class="formulario" method="post" action="/entrar">
  <input type="hidden" name="protecao" value="{protecao}">{volta}
  <div class="campo"><label for="email">E-mail</label>
    <input id="email" name="email" type="email" value="{email}" autocomplete="username" required autofocus></div>
  <div class="campo"><label for="senha">Senha</label>
    <input id="senha" name="senha" type="password" autocomplete="current-password" required></div>
  <button type="submit">Entrar</button>
</form>
<p class="publica-troca">Ainda não tem acesso? <a href="/criar-conta">Criar conta</a></p>""",
        aviso=caixa_de_aviso("info", aviso) if aviso else Html(""),
        erro=caixa_de_aviso("erro", erro) if erro else Html(""),
        protecao=protecao_da_entrada,
        volta=h('\n  <input type="hidden" name="volta" value="{v}">', v=volta) if volta else Html(""),
        email=email,
    )
    return _tela_publica(
        "Entrar", "Entre no RemindMe para acompanhar títulos a receber, orçamentos e clientes da sua empresa.", conteudo
    )


PERFIS_DA_CRIACAO_DE_CONTA = [p for p in Perfil if p is not Perfil.ADMINISTRADOR]


def pagina_criar_conta(protecao_da_entrada: str, valores: Valores, erros: Erros, criada: bool = False) -> Html:
    if criada:
        conteudo = h(
            """<h1>Conta criada</h1>
<p class="publica-texto">A conta de {email} aguarda a ativação pelo Administrador da empresa. Assim que ela for ativada, entre com o seu e-mail e a senha que você escolheu.</p>
<p><a class="botao" href="/entrar">Ir para a entrada</a></p>""",
            email=valores.get("email", ""),
        )
    else:
        conteudo = h(
            """<h1>Criar conta</h1>
<p class="publica-texto">A conta fica aguardando a ativação pelo Administrador da empresa.</p>
<form class="formulario" method="post" action="/criar-conta" novalidate>
  <input type="hidden" name="protecao" value="{protecao}">{geral}
  {nome}{email}{perfil}{senha}
  <button type="submit">Criar conta</button>
</form>
<p class="publica-troca">Já tem acesso? <a href="/entrar">Entrar</a></p>""",
            protecao=protecao_da_entrada,
            geral=erro_geral(erros),
            nome=campo("nome", "Nome", valores, erros, extra='autocomplete="name"'),
            email=campo("email", "E-mail", valores, erros, tipo="email", extra='autocomplete="email"'),
            perfil=selecao("perfil", "Perfil", [(p.name, p.value) for p in PERFIS_DA_CRIACAO_DE_CONTA], valores, erros, vazio="Escolha o perfil"),
            senha=campo("senha", "Senha", {}, erros, tipo="password", ajuda="Pelo menos 8 caracteres.", extra='autocomplete="new-password"'),
        )
    return _tela_publica("Criar conta", "Peça acesso ao RemindMe da sua empresa. A conta é ativada pelo Administrador.", conteudo)
