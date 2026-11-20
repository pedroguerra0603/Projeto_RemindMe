"""Leitura do formulário `multipart/form-data`, para o upload da evidência (Spec 010, OPEN-68).

O módulo `cgi` saiu da biblioteca padrão no Python 3.13; os cabeçalhos de cada parte são lidos pelo módulo `email`.
Qualquer corpo mal formado é tratado como formulário vazio, sem exceção: a recusa fica com quem chama.
"""

from dataclasses import dataclass
from email.message import Message
from email.utils import collapse_rfc2231_value
from typing import Dict, Tuple


@dataclass(frozen=True)
class ArquivoEnviado:
    nome: str
    conteudo: bytes


def ler_multipart(corpo: bytes, tipo_de_conteudo: str) -> Tuple[Dict[str, str], Dict[str, ArquivoEnviado]]:
    """Devolve os campos de texto e os arquivos. Parte de arquivo sem nome e sem conteúdo (campo de arquivo deixado
    vazio pelo navegador) não entra em `arquivos` (foco de revisão 2)."""
    cabecalho = Message()
    cabecalho["Content-Type"] = tipo_de_conteudo
    limite = cabecalho.get_param("boundary")
    if not isinstance(limite, str) or not limite:
        return {}, {}
    delimitador = b"--" + limite.encode("latin-1")
    pedacos = corpo.split(delimitador)
    if len(pedacos) < 3 or pedacos[0] not in (b"", b"\r\n") or not pedacos[-1].startswith(b"--"):
        return {}, {}
    campos: Dict[str, str] = {}
    arquivos: Dict[str, ArquivoEnviado] = {}
    for pedaco in pedacos[1:-1]:
        if not (pedaco.startswith(b"\r\n") and pedaco.endswith(b"\r\n")):
            return {}, {}
        cabecalhos, separador, conteudo = pedaco[2:-2].partition(b"\r\n\r\n")
        if not separador:
            return {}, {}
        parte = Message()
        for linha in cabecalhos.decode("utf-8", errors="replace").split("\r\n"):
            nome, dois_pontos, valor = linha.partition(":")
            if dois_pontos:
                parte[nome.strip()] = valor.strip()
        nome = parte.get_param("name", header="content-disposition")
        if not isinstance(nome, str):
            continue
        if parte.get_param("filename", header="content-disposition") is None and parte.get_param(
            "filename*", header="content-disposition"
        ) is None:
            campos[nome] = conteudo.decode("utf-8", errors="replace")
            continue
        nome_do_arquivo = _nome_do_arquivo(parte)
        if nome_do_arquivo or conteudo:
            arquivos[nome] = ArquivoEnviado(nome_do_arquivo, conteudo)
    return campos, arquivos


def _nome_do_arquivo(parte: Message) -> str:
    """`filename*` (RFC 2231, em UTF-8) prevalece sobre `filename`, como manda a RFC 6266."""
    parametros = parte.get_params(header="content-disposition") or []
    codificado = next((v for n, v in parametros if n == "filename" and isinstance(v, tuple)), None)
    if codificado is not None:
        return collapse_rfc2231_value(codificado)
    return parte.get_filename() or ""
