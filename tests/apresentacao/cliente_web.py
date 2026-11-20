"""Cliente de teste da aplicação WSGI, no próprio processo, sem servidor e sem dependência (OPEN-29)."""

import io
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

_PROTECAO = re.compile(r'name="protecao" value="([^"]+)"')
_PEDIDO = re.compile(r'name="pedido" value="([^"]+)"')


@dataclass
class RespostaDeTeste:
    status: int
    cabecalhos: List[Tuple[str, str]]
    texto: str
    bruto: bytes = b""

    def cabecalho(self, nome: str) -> Optional[str]:
        return next((v for n, v in self.cabecalhos if n.lower() == nome.lower()), None)

    def cookies_definidos(self) -> List[str]:
        return [v for n, v in self.cabecalhos if n.lower() == "set-cookie"]

    @property
    def destino(self) -> Optional[str]:
        return self.cabecalho("Location")

    @property
    def protecao(self) -> str:
        return _PROTECAO.search(self.texto).group(1)

    @property
    def pedido(self) -> str:
        return _PEDIDO.search(self.texto).group(1)


@dataclass
class ClienteWeb:
    aplicacao: object
    https: bool = False
    cookies: Dict[str, str] = field(default_factory=dict)

    def pedir(
        self,
        metodo: str,
        caminho: str,
        dados: Optional[Dict[str, str]] = None,
        corpo: Optional[bytes] = None,
        tipo: str = "application/x-www-form-urlencoded",
    ) -> RespostaDeTeste:
        caminho, _, consulta = caminho.partition("?")
        conteudo = corpo if corpo is not None else urlencode(dados or {}).encode("utf-8")
        ambiente = {
            "REQUEST_METHOD": metodo,
            "PATH_INFO": caminho,
            "QUERY_STRING": consulta,
            "CONTENT_TYPE": tipo,
            "CONTENT_LENGTH": str(len(conteudo)),
            "wsgi.input": io.BytesIO(conteudo),
            "wsgi.url_scheme": "https" if self.https else "http",
            "HTTP_COOKIE": "; ".join(f"{nome}={valor}" for nome, valor in self.cookies.items()),
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
        }
        recebido = {}

        def iniciar(status, cabecalhos):
            recebido["status"], recebido["cabecalhos"] = status, cabecalhos

        bruto = b"".join(self.aplicacao(ambiente, iniciar))
        texto = bruto.decode("utf-8", errors="replace")
        resposta = RespostaDeTeste(int(recebido["status"].split()[0]), recebido["cabecalhos"], texto, bruto)
        for cookie in resposta.cookies_definidos():
            nome, _, resto = cookie.partition("=")
            valor = resto.split(";")[0]
            if "Max-Age=0" in cookie:
                self.cookies.pop(nome, None)
            else:
                self.cookies[nome] = valor
        return resposta

    def get(self, caminho: str) -> RespostaDeTeste:
        return self.pedir("GET", caminho)

    def post(self, caminho: str, dados: Optional[Dict[str, str]] = None) -> RespostaDeTeste:
        return self.pedir("POST", caminho, dados)

    def enviar(self, pagina: str, acao: str, dados: Dict[str, str]) -> RespostaDeTeste:
        """Abre a página do formulário e o envia com a proteção da sessão, como o navegador faria."""
        return self.post(acao, {"protecao": self.get(pagina).protecao, **dados})

    def postar_multipart(
        self, caminho: str, campos: Dict[str, str], arquivos: Optional[Dict[str, Tuple[str, bytes]]] = None
    ) -> RespostaDeTeste:
        """Spec 010: formulário com arquivo, como o navegador o envia (`multipart/form-data`)."""
        limite = "----RemindMeTeste7d1f"
        partes = []
        for nome, valor in campos.items():
            partes.append(f'Content-Disposition: form-data; name="{nome}"\r\n\r\n'.encode("utf-8") + valor.encode("utf-8"))
        for nome, (nome_do_arquivo, conteudo) in (arquivos or {}).items():
            partes.append(
                f'Content-Disposition: form-data; name="{nome}"; filename="{nome_do_arquivo}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n".encode("utf-8") + conteudo
            )
        delimitador = b"--" + limite.encode()
        corpo = b"".join(delimitador + b"\r\n" + parte + b"\r\n" for parte in partes) + delimitador + b"--\r\n"
        return self.pedir("POST", caminho, corpo=corpo, tipo=f"multipart/form-data; boundary={limite}")

    def entrar(self, email: str, senha: str) -> RespostaDeTeste:
        protecao = self.get("/entrar").protecao
        return self.post("/entrar", {"protecao": protecao, "email": email, "senha": senha})
