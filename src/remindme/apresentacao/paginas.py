"""Montagem do HTML. Todo texto vindo de dado passa por `e` (escape)."""

from html import escape
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from remindme.dominio.acesso import Operacao
from remindme.dominio.titulo import EstadoTitulo
from remindme.dominio.usuario import Usuario


def e(texto) -> str:
    return escape("" if texto is None else str(texto), quote=True)


# Itens do menu: (caminho, rótulo, operações que dão acesso). Só aparecem os permitidos (RF-65).
MENU: List[Tuple[str, str, Tuple[Operacao, ...]]] = [
    ("/", "Painel", ()),
    ("/titulos", "Títulos", (Operacao.CONSULTAR_TITULOS,)),
    ("/clientes", "Clientes", (Operacao.MANTER_CLIENTES, Operacao.CONSULTAR_TITULOS)),
    ("/auditoria", "Auditoria", (Operacao.CONSULTAR_AUDITORIA,)),
    ("/usuarios", "Usuários", (Operacao.ADMINISTRAR_USUARIOS,)),
    ("/permissoes", "Permissões", (Operacao.ADMINISTRAR_USUARIOS,)),
]

CLASSE_ESTADO = {
    EstadoTitulo.ABERTO: "aberto",
    EstadoTitulo.VENCIDO: "vencido",
    EstadoTitulo.BAIXADO: "baixado",
    EstadoTitulo.CANCELADO: "cancelado",
}


def documento(titulo: str, corpo: str, cabeca_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)} · RemindMe</title>
<link rel="stylesheet" href="/static/estilo.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%232f5bea'/%3E%3Cpath d='M9 22V10h7a4 4 0 0 1 0 8h-7m7 0 6 4' stroke='white' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
{cabeca_extra}
</head>
<body>
{corpo}
</body>
</html>"""


def layout(
    titulo: str,
    conteudo: str,
    usuario: Usuario,
    operacoes: FrozenSet[Operacao],
    caminho: str,
    csrf: str,
    aviso: Optional[Tuple[str, str]] = None,
) -> str:
    itens = []
    for destino, rotulo, exigidas in MENU:
        if exigidas and not any(op in operacoes for op in exigidas):
            continue
        ativo = destino == caminho or (destino != "/" and caminho.startswith(destino + "/"))
        atual = ' aria-current="page"' if ativo else ""
        itens.append(f'<a href="{destino}"{atual}>{e(rotulo)}</a>')
    bloco_aviso = ""
    if aviso:
        tipo, texto = aviso
        bloco_aviso = f'<div class="aviso aviso-{e(tipo)}" role="status">{e(texto)}</div>'
    corpo = f"""
<header class="topo">
  <a class="marca" href="/"><span class="logo">R</span> RemindMe</a>
  <nav class="menu" aria-label="Principal">{''.join(itens)}</nav>
  <div class="conta">
    <span class="quem"><strong>{e(usuario.nome)}</strong><small>{e(usuario.perfil.value)}</small></span>
    <form method="post" action="/sair">{campo_csrf(csrf)}<button class="botao botao-leve">Sair</button></form>
  </div>
</header>
<main class="conteudo">
  {bloco_aviso}
  {conteudo}
</main>
<footer class="rodape">RemindMe · gestão de recebíveis para micro e pequenas empresas</footer>"""
    return documento(titulo, corpo)


def campo_csrf(token: str) -> str:
    return f'<input type="hidden" name="_csrf" value="{e(token)}">'


def cabecalho(titulo: str, subtitulo: str = "", acoes: str = "") -> str:
    sub = f'<p class="subtitulo">{e(subtitulo)}</p>' if subtitulo else ""
    return f"""<div class="cabecalho"><div><h1>{e(titulo)}</h1>{sub}</div><div class="acoes">{acoes}</div></div>"""


def selo_estado(estado: EstadoTitulo) -> str:
    return f'<span class="selo selo-{CLASSE_ESTADO[estado]}">{e(estado.value)}</span>'


def selo(texto: str, classe: str) -> str:
    return f'<span class="selo selo-{e(classe)}">{e(texto)}</span>'


def tabela(colunas: Sequence[str], linhas: Iterable[Sequence[str]], vazio: str, classes: str = "") -> str:
    """Células já devem vir escapadas."""
    corpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas)
    if not corpo:
        return f'<p class="vazio">{e(vazio)}</p>'
    cab = "".join(f"<th>{e(c)}</th>" for c in colunas)
    return f'<div class="tabela-rolagem"><table class="tabela {classes}"><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table></div>'


def erros_formulario(erros: Dict[str, str], geral: Optional[str] = None) -> str:
    """RNF-14: cada campo e o motivo."""
    if not erros and not geral:
        return ""
    itens = "".join(f"<li><strong>{e(campo)}</strong>: {e(motivo)}</li>" for campo, motivo in erros.items())
    texto = f"<p>{e(geral)}</p>" if geral else "<p>Corrija os campos abaixo.</p>"
    lista = f"<ul>{itens}</ul>" if itens else ""
    return f'<div class="aviso aviso-erro" role="alert">{texto}{lista}</div>'


def entrada(
    nome: str,
    rotulo: str,
    conteudo: str = "",
    tipo: str = "text",
    erro: Optional[str] = None,
    obrigatorio: bool = False,
    extra: str = "",
    ajuda: str = "",
) -> str:
    atributos = ' required' if obrigatorio else ""
    classe = ' class="com-erro"' if erro else ""
    texto_erro = f'<span class="erro-campo">{e(erro)}</span>' if erro else ""
    texto_ajuda = f'<span class="ajuda">{e(ajuda)}</span>' if ajuda else ""
    return f"""<label class="campo"><span>{e(rotulo)}{' *' if obrigatorio else ''}</span>
<input type="{tipo}" name="{e(nome)}" value="{e(conteudo)}"{atributos}{classe} {extra}>{texto_ajuda}{texto_erro}</label>"""


def selecao(
    nome: str,
    rotulo: str,
    opcoes: Sequence[Tuple[str, str]],
    selecionado: str = "",
    erro: Optional[str] = None,
    obrigatorio: bool = False,
    vazio: Optional[str] = None,
) -> str:
    itens = []
    if vazio is not None:
        itens.append(f'<option value="">{e(vazio)}</option>')
    for valor, texto in opcoes:
        marcado = " selected" if valor == selecionado else ""
        itens.append(f'<option value="{e(valor)}"{marcado}>{e(texto)}</option>')
    classe = ' class="com-erro"' if erro else ""
    texto_erro = f'<span class="erro-campo">{e(erro)}</span>' if erro else ""
    req = " required" if obrigatorio else ""
    return f"""<label class="campo"><span>{e(rotulo)}{' *' if obrigatorio else ''}</span>
<select name="{e(nome)}"{req}{classe}>{''.join(itens)}</select>{texto_erro}</label>"""


def cartao_indicador(rotulo: str, numero: str, destaque: str = "", detalhe: str = "") -> str:
    classe = f" indicador-{destaque}" if destaque else ""
    det = f"<small>{e(detalhe)}</small>" if detalhe else ""
    return f'<div class="indicador{classe}"><span>{e(rotulo)}</span><strong>{e(numero)}</strong>{det}</div>'


def pagina_login(erro: Optional[str] = None, email: str = "", aviso: Optional[str] = None) -> str:
    bloco_erro = f'<div class="aviso aviso-erro" role="alert">{e(erro)}</div>' if erro else ""
    bloco_aviso = f'<div class="aviso aviso-sucesso" role="status">{e(aviso)}</div>' if aviso else ""
    corpo = f"""
<main class="tela-login">
  <section class="cartao login">
    <div class="marca marca-grande"><span class="logo">R</span> RemindMe</div>
    <p class="subtitulo">Cada cobrança e cada obrigação no prazo, com registro de quem fez o quê.</p>
    {bloco_aviso}{bloco_erro}
    <form method="post" action="/login" class="formulario">
      {entrada("email", "E-mail", email, "email", obrigatorio=True, extra='autocomplete="username" autofocus')}
      {entrada("senha", "Senha", "", "password", obrigatorio=True, extra='autocomplete="current-password"')}
      <button class="botao botao-primario botao-largo">Entrar</button>
    </form>
  </section>
</main>"""
    return documento("Entrar", corpo)


def pagina_erro(codigo: int, titulo: str, mensagem: str, logado: bool = True) -> str:
    voltar = '<a class="botao botao-primario" href="/">Voltar ao painel</a>' if logado else '<a class="botao botao-primario" href="/login">Entrar</a>'
    corpo = f"""
<main class="tela-login">
  <section class="cartao login">
    <div class="marca marca-grande"><span class="logo">R</span> RemindMe</div>
    <p class="codigo-erro">{codigo}</p>
    <h1>{e(titulo)}</h1>
    <p>{e(mensagem)}</p>
    {voltar}
  </section>
</main>"""
    return documento(titulo, corpo)
