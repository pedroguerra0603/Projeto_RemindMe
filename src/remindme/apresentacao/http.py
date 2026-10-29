"""Requisição, resposta e rotas sobre WSGI (PEP 3333), somente com a biblioteca padrão (OPEN-01)."""

import re
from dataclasses import dataclass, field
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs

TAMANHO_MAXIMO_CORPO = 1024 * 1024


class Requisicao:
    def __init__(self, ambiente: dict):
        self.ambiente = ambiente
        self.metodo = ambiente.get("REQUEST_METHOD", "GET").upper()
        self.caminho = ambiente.get("PATH_INFO", "/") or "/"
        self.consulta = _achatar(parse_qs(ambiente.get("QUERY_STRING", ""), keep_blank_values=True))
        self.cookies = _cookies(ambiente.get("HTTP_COOKIE", ""))
        self.parametros: Dict[str, str] = {}
        self._formulario: Optional[Dict[str, List[str]]] = None

    @property
    def formulario(self) -> Dict[str, List[str]]:
        if self._formulario is None:
            try:
                tamanho = int(self.ambiente.get("CONTENT_LENGTH") or 0)
            except ValueError:
                tamanho = 0
            tamanho = max(0, min(tamanho, TAMANHO_MAXIMO_CORPO))
            corpo = self.ambiente["wsgi.input"].read(tamanho) if tamanho else b""
            self._formulario = parse_qs(corpo.decode("utf-8", "replace"), keep_blank_values=True)
        return self._formulario

    def campo(self, nome: str, padrao: str = "") -> str:
        valores = self.formulario.get(nome)
        return valores[0] if valores else padrao

    def campos(self, nome: str) -> List[str]:
        return self.formulario.get(nome, [])


@dataclass
class Resposta:
    corpo: bytes = b""
    status: int = 200
    tipo: str = "text/html; charset=utf-8"
    cabecalhos: List[Tuple[str, str]] = field(default_factory=list)

    @classmethod
    def html(cls, texto: str, status: int = 200) -> "Resposta":
        return cls(texto.encode("utf-8"), status)

    @classmethod
    def redirecionar(cls, destino: str) -> "Resposta":
        return cls(b"", 303, cabecalhos=[("Location", destino)])

    def definir_cookie(self, nome: str, conteudo: str, seguro: bool, max_age: Optional[int] = None) -> None:
        partes = [f"{nome}={conteudo}", "Path=/", "HttpOnly", "SameSite=Lax"]
        if seguro:
            partes.append("Secure")
        if max_age is not None:
            partes.append(f"Max-Age={max_age}")
        self.cabecalhos.append(("Set-Cookie", "; ".join(partes)))

    def apagar_cookie(self, nome: str, seguro: bool) -> None:
        self.definir_cookie(nome, "", seguro, max_age=0)

    def linha_de_status(self) -> str:
        return f"{self.status} {HTTPStatus(self.status).phrase}"


Manipulador = Callable[[Requisicao], Resposta]


class Rotas:
    def __init__(self):
        self._rotas: List[Tuple[str, re.Pattern, Manipulador]] = []

    def adicionar(self, metodo: str, padrao: str, manipulador: Manipulador) -> None:
        """`padrao` aceita segmentos `{nome}`, que casam com letras, dígitos, `-` e `_`."""
        regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[\\w-]+)", padrao)
        self._rotas.append((metodo, re.compile(f"^{regex}$"), manipulador))

    def encontrar(self, metodo: str, caminho: str) -> Tuple[Optional[Manipulador], Dict[str, str], bool]:
        """Devolve o manipulador, os parâmetros e se o caminho existe com outro método."""
        caminho_existe = False
        for metodo_rota, regex, manipulador in self._rotas:
            casamento = regex.match(caminho)
            if casamento:
                if metodo_rota == metodo:
                    return manipulador, casamento.groupdict(), True
                caminho_existe = True
        return None, {}, caminho_existe


def _achatar(dados: Dict[str, List[str]]) -> Dict[str, str]:
    return {chave: valores[0] for chave, valores in dados.items() if valores}


def _cookies(texto: str) -> Dict[str, str]:
    cookie = SimpleCookie()
    try:
        cookie.load(texto)
    except CookieError:
        return {}
    return {nome: morsel.value for nome, morsel in cookie.items()}
