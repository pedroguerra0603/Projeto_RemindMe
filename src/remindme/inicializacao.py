"""Montagem da aplicação e linha de comando (Spec 017). Uso: `python3 -m remindme --help`.

É o único ponto que conhece todas as camadas: liga os serviços da aplicação ao SQLite, ao relógio do sistema,
ao agendador e à interface web.
"""

import argparse
import getpass
import logging
import secrets
import ssl
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from remindme.aplicacao.acesso import Autorizacao
from remindme.aplicacao.auditoria import RegistroErrosNoLog
from remindme.aplicacao.portas import CifradorDeSenha, RegistroErros, Relogio
from remindme.aplicacao.servico_acesso import ServicoAcesso
from remindme.aplicacao.servico_auditoria import ServicoAuditoria
from remindme.aplicacao.servico_clientes import ServicoClientes
from remindme.aplicacao.servico_titulos import ServicoTitulos
from remindme.apresentacao.web.aplicacao_web import AplicacaoWeb, Servicos
from remindme.dominio.erros import OperacaoRecusada
from remindme.dominio.usuario import Perfil
from remindme.entradas.agendador import AgendadorDeVencimentos
from remindme.infraestrutura.relogio import RelogioDoSistema
from remindme.infraestrutura.sqlite import UnidadeDeTrabalhoSQLite, preparar_banco

BANCO_PADRAO = "remindme.db"
BANCO_DA_DEMONSTRACAO = "remindme-demonstracao.db"
ENDERECOS_LOCAIS = ("127.0.0.1", "localhost", "::1")


class ConfiguracaoInvalida(Exception):
    pass


@dataclass
class Sistema:
    servicos: Servicos
    web: AplicacaoWeb
    agendador: AgendadorDeVencimentos
    uow: UnidadeDeTrabalhoSQLite
    relogio: Relogio


def montar(
    caminho_banco: str,
    relogio: Optional[Relogio] = None,
    cifrador: Optional[CifradorDeSenha] = None,
    erros: Optional[RegistroErros] = None,
) -> Sistema:
    preparar_banco(caminho_banco)
    uow = UnidadeDeTrabalhoSQLite(caminho_banco)
    relogio = relogio or RelogioDoSistema()
    erros = erros or RegistroErrosNoLog()
    autorizacao = Autorizacao(relogio)
    servicos = Servicos(
        acesso=ServicoAcesso(uow, relogio, erros, cifrador, autorizacao),
        clientes=ServicoClientes(uow, relogio, erros, autorizacao),
        titulos=ServicoTitulos(uow, uow.clientes, relogio, erros, autorizacao),
        auditoria=ServicoAuditoria(uow, relogio, erros, autorizacao),
    )
    agendador = AgendadorDeVencimentos(servicos.titulos, relogio)
    return Sistema(servicos, AplicacaoWeb(servicos, relogio, erros), agendador, uow, relogio)


def conferir_endereco(host: str, certificado: Optional[str], chave: Optional[str]) -> None:
    """OPEN-38 (RNF-05, E3): sem certificado, o servidor só atende a própria máquina."""
    if (certificado is None) != (chave is None):
        raise ConfiguracaoInvalida("Informe o certificado e a chave juntos (--certificado e --chave).")
    if certificado is None and host not in ENDERECOS_LOCAIS:
        raise ConfiguracaoInvalida(
            f"Para atender pela rede ({host}), o RemindMe exige HTTPS (RNF-05): informe --certificado e --chave. "
            "Sem certificado, use --host 127.0.0.1, que só atende esta máquina."
        )


class _Registrador(WSGIRequestHandler):
    """Registra cada requisição no log da aplicação, e não direto na saída de erro."""

    def log_message(self, formato, *argumentos):
        logging.getLogger("remindme.web").info("%s %s", self.address_string(), formato % argumentos)


def criar_servidor(
    sistema: Sistema, host: str, porta: int, certificado: Optional[str] = None, chave: Optional[str] = None
) -> WSGIServer:
    conferir_endereco(host, certificado, chave)
    servidor = make_server(host, porta, sistema.web, handler_class=_Registrador)
    if certificado:
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        contexto.load_cert_chain(certificado, chave)
        servidor.socket = contexto.wrap_socket(servidor.socket, server_side=True)
        servidor.base_environ["HTTPS"] = "on"
    return servidor


def endereco(servidor: WSGIServer, https: bool) -> str:
    host, porta = servidor.server_address[:2]
    return f"{'https' if https else 'http'}://{'localhost' if host in ('127.0.0.1', '::1') else host}:{porta}"


def servir(sistema: Sistema, host: str, porta: int, certificado: Optional[str], chave: Optional[str]) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    servidor = criar_servidor(sistema, host, porta, certificado, chave)
    sistema.agendador.iniciar()
    print(f"\nRemindMe no ar em {endereco(servidor, bool(certificado))}  (Ctrl+C para parar)\n", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nRemindMe encerrado.")
    finally:
        sistema.agendador.parar()
        servidor.server_close()


def _ha_administrador(sistema: Sistema) -> bool:
    with sistema.uow as uow:
        return any(u.ativo and u.perfil is Perfil.ADMINISTRADOR for u in uow.usuarios.listar())


def _criar_administrador(argumentos) -> int:
    sistema = montar(argumentos.banco)
    print("Criação do primeiro Administrador do RemindMe (OPEN-39).")
    nome = input("Nome: ")
    email = input("E-mail: ")
    senha = getpass.getpass("Senha (pelo menos 8 caracteres): ")
    if senha != getpass.getpass("Repita a senha: "):
        print("As senhas não conferem. Nada foi criado.", file=sys.stderr)
        return 1
    try:
        sistema.servicos.acesso.criar_primeiro_administrador(nome, email, senha)
    except OperacaoRecusada as recusa:
        print(f"Não foi possível criar: {recusa.motivo}", file=sys.stderr)
        return 1
    print(f"Administrador criado. Inicie o servidor com: python3 -m remindme --banco {argumentos.banco}")
    return 0


def _servidor(argumentos) -> int:
    try:
        conferir_endereco(argumentos.host, argumentos.certificado, argumentos.chave)
    except ConfiguracaoInvalida as erro:
        print(erro, file=sys.stderr)
        return 2
    sistema = montar(argumentos.banco)
    if not _ha_administrador(sistema):
        print(
            "Aviso: ainda não há Administrador. Crie um com "
            f"`python3 -m remindme criar-administrador --banco {argumentos.banco}`, "
            "ou prepare dados de demonstração com `python3 -m remindme demonstracao`.",
            file=sys.stderr,
        )
    servir(sistema, argumentos.host, argumentos.porta, argumentos.certificado, argumentos.chave)
    return 0


def _demonstracao(argumentos) -> int:
    from remindme.demonstracao import preparar_demonstracao

    caminho = Path(argumentos.banco)
    if caminho.exists():
        if not argumentos.substituir:
            print(
                f"O banco {caminho} já existe. Use --substituir para criar outro do zero, "
                f"ou inicie o servidor com: python3 -m remindme --banco {caminho}",
                file=sys.stderr,
            )
            return 1
        for arquivo in (caminho, Path(f"{caminho}-wal"), Path(f"{caminho}-shm")):
            if arquivo.exists():
                arquivo.unlink()
    senha = argumentos.senha or secrets.token_urlsafe(9)
    if len(senha) < 8:
        print("A senha da demonstração precisa de pelo menos 8 caracteres.", file=sys.stderr)
        return 1
    sistema = montar(str(caminho))
    usuarios = preparar_demonstracao(sistema, senha)
    print("\nDados de demonstração criados em", caminho)
    print("Usuários (a mesma senha para todos):")
    for nome, email, perfil in usuarios:
        print(f"  {perfil:<20} {email:<26} {nome}")
    print(f"  Senha: {senha}\n")
    if argumentos.sem_servidor:
        return 0
    servir(sistema, "127.0.0.1", argumentos.porta, None, None)
    return 0


def _analisador() -> argparse.ArgumentParser:
    analisador = argparse.ArgumentParser(
        prog="python3 -m remindme",
        description="RemindMe: gestão de recebíveis e obrigações de micro e pequenas empresas.",
    )
    comandos = analisador.add_subparsers(dest="comando")

    servidor = comandos.add_parser("servidor", help="inicia o servidor web (padrão)")
    servidor.add_argument("--banco", default=BANCO_PADRAO, help=f"arquivo SQLite (padrão: {BANCO_PADRAO})")
    servidor.add_argument("--host", default="127.0.0.1", help="endereço de escuta (padrão: 127.0.0.1, só esta máquina)")
    servidor.add_argument("--porta", type=int, default=8000, help="porta (padrão: 8000)")
    servidor.add_argument("--certificado", help="certificado TLS, para HTTPS")
    servidor.add_argument("--chave", help="chave privada do certificado TLS")
    servidor.set_defaults(executar=_servidor)

    administrador = comandos.add_parser("criar-administrador", help="cria o primeiro Administrador (OPEN-39)")
    administrador.add_argument("--banco", default=BANCO_PADRAO, help=f"arquivo SQLite (padrão: {BANCO_PADRAO})")
    administrador.set_defaults(executar=_criar_administrador)

    demonstracao = comandos.add_parser("demonstracao", help="cria um banco com dados de demonstração e inicia o servidor")
    demonstracao.add_argument("--banco", default=BANCO_DA_DEMONSTRACAO, help=f"arquivo SQLite (padrão: {BANCO_DA_DEMONSTRACAO})")
    demonstracao.add_argument("--porta", type=int, default=8000, help="porta (padrão: 8000)")
    demonstracao.add_argument("--senha", help="senha dos usuários de demonstração (padrão: gerada agora)")
    demonstracao.add_argument("--substituir", action="store_true", help="apaga o banco de demonstração existente")
    demonstracao.add_argument("--sem-servidor", action="store_true", help="só prepara os dados, sem iniciar o servidor")
    demonstracao.set_defaults(executar=_demonstracao)
    return analisador


def principal(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help"):
        argv.insert(0, "servidor")
    argumentos = _analisador().parse_args(argv)
    return argumentos.executar(argumentos)
