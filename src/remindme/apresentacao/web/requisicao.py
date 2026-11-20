"""Requisição, resposta e auxiliares de formulário da interface web (Spec 017, ADR-006).

Usados pela aplicação WSGI e pelos manipuladores de cada módulo (`rotas_<módulo>.py`). Nenhuma regra aqui (INV-1).
"""

import hmac
import re
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode

from remindme.apresentacao.web import formatos as f
from remindme.apresentacao.web.html import Html
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil


COOKIE_SESSAO = "remindme_sessao"
COOKIE_ENTRADA = "remindme_entrada"
LIMITE_DO_CORPO = 64 * 1024
ESTATICO = Path(__file__).resolve().parent.joinpath("estatico")
ARQUIVOS_ESTATICOS = {
    "estilo.css": "text/css; charset=utf-8",
    "icone.svg": "image/svg+xml",
    "tema.js": "text/javascript; charset=utf-8",
    "plex-sans-400.woff2": "font/woff2",
    "plex-sans-600.woff2": "font/woff2",
}
ID = "[0-9a-f]{32}"

POLITICA_DE_CONTEUDO = (
    "default-src 'none'; style-src 'self'; img-src 'self'; script-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; "
    "frame-ancestors 'none'; base-uri 'none'"
)

AVISOS = {
    "saiu": ("info", "Você saiu do sistema."),
    "sessao-encerrada": (
        "info",
        "Sua sessão terminou: ela venceu, foi encerrada em outra aba ou o servidor foi reiniciado com um banco novo. "
        "Entre de novo para continuar de onde parou.",
    ),
    "senha": ("sucesso", "Senha alterada. As outras sessões abertas com o seu usuário foram encerradas."),
    "cliente": ("sucesso", "Cliente cadastrado."),
    "cliente-alterado": ("sucesso", "Dados do cliente atualizados."),
    "titulo": ("sucesso", "Título cadastrado em Aberto."),
    "pagamento": ("sucesso", "Pagamento registrado."),
    "estorno": ("sucesso", "Pagamento estornado."),
    "cancelamento": ("sucesso", "Título cancelado."),
    "usuario": ("sucesso", "Usuário cadastrado. Informe a senha provisória a ele."),
    "perfil": ("sucesso", "Perfil alterado. Vale na próxima operação do usuário."),
    "inativacao": ("sucesso", "Usuário inativado. As sessões dele foram encerradas."),
    "permissao": ("sucesso", "Permissão atualizada. Vale na próxima operação dos usuários do perfil."),
    "orcamento": ("sucesso", "Orçamento criado em Rascunho. Inclua os itens."),
    "item": ("sucesso", "Item incluído. Os valores foram recalculados."),
    "item-alterado": ("sucesso", "Item alterado. Os valores foram recalculados."),
    "item-removido": ("sucesso", "Item removido. Os valores foram recalculados."),
    "desconto": ("sucesso", "Desconto aplicado. Os valores foram recalculados."),
    "desconto-pendente": ("info", "O desconto passa da sua alçada: o orçamento aguarda a decisão do Dono."),
    "condicao": ("sucesso", "Prazo e condição de pagamento atualizados."),
    "decisao": ("sucesso", "Decisão registrada. O orçamento voltou a Rascunho."),
    "orcamento-cancelado": ("sucesso", "Orçamento cancelado."),
    "orcamento-enviado": ("sucesso", "Orçamento enviado ao cliente."),
    "orcamento-convertido": ("sucesso", "Aprovação registrada. O título foi gerado."),
    "orcamento-rejeitado": ("sucesso", "Rejeição registrada."),
    "empresa": ("sucesso", "Dados da empresa salvos."),
    "fornecedor": ("sucesso", "Fornecedor cadastrado."),
    "fornecedor-alterado": ("sucesso", "Dados do fornecedor atualizados."),
    "conta": ("sucesso", "Conta a pagar cadastrada em Aberta."),
    "pagamento-conta": ("sucesso", "Pagamento registrado."),
    "estorno-conta": ("sucesso", "Pagamento estornado."),
    "cancelamento-conta": ("sucesso", "Conta a pagar cancelada."),
    "ativacao": ("sucesso", "Usuário ativado. Ele já pode entrar."),
}

_CORRELACAO = re.compile(r"Identificador de correlação: ([0-9a-f]+)")


class CorpoGrandeDemais(Exception):
    pass


class Requisicao:
    def __init__(self, ambiente: dict):
        self.metodo = ambiente.get("REQUEST_METHOD", "GET").upper()
        self.caminho = ambiente.get("PATH_INFO", "") or "/"
        self.consulta_original = ambiente.get("QUERY_STRING", "")
        self.consulta = _primeiros(parse_qs(self.consulta_original, keep_blank_values=True))
        self.https = ambiente.get("wsgi.url_scheme") == "https"
        try:
            self.cookies = {nome: m.value for nome, m in SimpleCookie(ambiente.get("HTTP_COOKIE", "")).items()}
        except CookieError:
            self.cookies = {}
        self.formulario: Dict[str, str] = {}
        if self.metodo == "POST":
            try:
                tamanho = int(ambiente.get("CONTENT_LENGTH") or 0)
            except ValueError:
                tamanho = 0
            if tamanho > LIMITE_DO_CORPO:
                raise CorpoGrandeDemais()
            corpo = ambiente["wsgi.input"].read(tamanho) if tamanho > 0 else b""
            if ambiente.get("CONTENT_TYPE", "").startswith("application/x-www-form-urlencoded"):
                texto = corpo.decode("utf-8", errors="replace")
                self.formulario = _primeiros(parse_qs(texto, keep_blank_values=True))

    def campo(self, nome: str) -> str:
        return self.formulario.get(nome, "").strip()


class Resposta:
    def __init__(self, status: int = 200, corpo: bytes = b"", tipo: str = "text/html; charset=utf-8"):
        self.status = status
        self.corpo = corpo
        self.cabecalhos: List[Tuple[str, str]] = [("Content-Type", tipo)]
        self.cache = "no-store"

    @classmethod
    def pagina(cls, html: Html, status: int = 200) -> "Resposta":
        return cls(status, html.encode("utf-8"))

    @classmethod
    def redirecionar(cls, destino: str) -> "Resposta":
        resposta = cls(303)
        resposta.cabecalhos.append(("Location", destino))
        return resposta

    def cookie(self, nome: str, conteudo: str, https: bool, apagar: bool = False) -> "Resposta":
        partes = [f"{nome}={'' if apagar else conteudo}", "Path=/", "HttpOnly", "SameSite=Lax"]
        if apagar:
            partes.append("Max-Age=0")
        if https:
            partes.append("Secure")
        self.cabecalhos.append(("Set-Cookie", "; ".join(partes)))
        return self


Manipulador = Callable[..., Resposta]


def _primeiros(valores: Dict[str, List[str]]) -> Dict[str, str]:
    return {chave: lista[0] for chave, lista in valores.items() if lista}


def _sessao_encerrada(req: Requisicao) -> Resposta:
    """RNF-01: sem sessão válida, volta à entrada. Se havia uma sessão (venceu, foi encerrada ou o banco é outro),
    explica o motivo e guarda a página pedida, para voltar a ela depois de entrar."""
    if not req.cookies.get(COOKIE_SESSAO):
        return Resposta.redirecionar("/entrar")
    destino = "/entrar?aviso=sessao-encerrada"
    if req.metodo == "GET":
        pedida = req.caminho + (f"?{req.consulta_original}" if req.consulta_original else "")
        destino += "&" + urlencode({"volta": pedida})
    return Resposta.redirecionar(destino).cookie(COOKIE_SESSAO, "", req.https, apagar=True)


def _volta(endereco: str) -> str:
    """Só aceita voltar para uma página do próprio RemindMe, para a entrada não servir de redirecionamento a outro site."""
    if not re.fullmatch(r"/[A-Za-z0-9][A-Za-z0-9/_.=&%?-]*", endereco or "") or endereco.startswith("/sair"):
        return ""
    return endereco


def _confere(enviado: str, esperado: str) -> bool:
    return bool(enviado) and bool(esperado) and hmac.compare_digest(enviado.encode(), esperado.encode())


def _valores(req: Requisicao, *nomes: str) -> Dict[str, str]:
    return {nome: req.campo(nome) for nome in nomes}


def _erros(recusa: OperacaoRecusada) -> Dict[str, str]:
    """RNF-14: os campos da recusa; sem campo, a mensagem vai para o topo do formulário."""
    return dict(recusa.campos) if recusa.campos else {"_": recusa.motivo}


def _valor_do_formulario(valores: Dict[str, str], erros: Dict[str, str]):
    if not valores["valor"]:
        erros["valor"] = "Informe o valor."
        return None
    valor = f.ler_valor(valores["valor"])
    if valor is None:
        erros["valor"] = "Informe um valor em reais, por exemplo 1.234,56."
    return valor


def _numero_do_formulario(valores: Dict[str, str], chave: str, mensagem: str, erros: Dict[str, str]):
    """Quantidade, valor unitário ou percentual no formato brasileiro (1.234,56). A regra fica no domínio."""
    if not valores[chave]:
        return None
    numero = f.ler_valor(valores[chave].replace("%", ""))
    if numero is None:
        erros[chave] = mensagem
    return numero


def _data_do_filtro(valores: Dict[str, str], chave: str, erros: Dict[str, str]):
    if not valores[chave]:
        return None
    lida = f.ler_data(valores[chave])
    if lida is None:
        erros[chave] = "Informe uma data válida."
    return lida


def _perfil(nome: str) -> Optional[Perfil]:
    return Perfil[nome] if nome in Perfil.__members__ else None


def _aviso(req: Requisicao) -> Optional[Tuple[str, str]]:
    codigo = req.consulta.get("aviso", "")
    if codigo == "vencimentos":
        quantidade = req.consulta.get("quantidade", "0")
        n = int(quantidade) if quantidade.isdigit() else 0
        return ("sucesso", f"Verificação concluída: {n} título(s) passaram a Vencido.")
    return AVISOS.get(codigo)
