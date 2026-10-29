"""Linha de comando: `servir`, `criar-admin` e `demo`."""

import argparse
import getpass
import logging
import secrets
import sys
from datetime import timedelta
from decimal import Decimal
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from remindme.aplicacao.sistema import Sistema
from remindme.apresentacao.montagem import Agendador, Configuracao, montar, montar_web
from remindme.dominio.erros import OperacaoRecusada

log = logging.getLogger("remindme")


class ServidorComThreads(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class RegistroDeRequisicoes(WSGIRequestHandler):
    def log_message(self, formato, *argumentos):
        logging.getLogger("remindme.http").info("%s %s", self.address_string(), formato % argumentos)


def servir(configuracao: Configuracao) -> None:
    montagem = montar(configuracao)
    sistema = montagem.sistema
    if not _existe_usuario(sistema):
        print(
            "Nenhum usuário cadastrado. Crie o Administrador com\n"
            "  python executar.py criar-admin\n"
            "ou carregue os dados de demonstração com\n"
            "  python executar.py demo\n",
            file=sys.stderr,
        )
    aplicacao = montar_web(montagem, configuracao)
    agendador = Agendador(sistema, configuracao.intervalo_agendador_minutos)
    agendador.iniciar()
    with make_server(
        configuracao.host, configuracao.porta, aplicacao, ServidorComThreads, RegistroDeRequisicoes
    ) as servidor:
        print(f"RemindMe em http://{configuracao.host}:{configuracao.porta}  (Ctrl+C encerra)")
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nEncerrado.")
        finally:
            agendador.parar()


def criar_admin(configuracao: Configuracao, nome: str, email: str) -> int:
    """A senha é digitada (ou lida da entrada padrão, em instalação automatizada), nunca passada na linha."""
    if sys.stdin.isatty():
        senha = getpass.getpass("Senha do Administrador: ")
    else:
        senha = sys.stdin.readline().rstrip("\n")
    sistema = montar(configuracao).sistema
    try:
        sistema.acesso.instalar_administrador(nome, email, senha)
    except OperacaoRecusada as recusa:
        print(f"Não foi possível criar o Administrador: {recusa.motivo}", file=sys.stderr)
        return 1
    print(f"Administrador {email} criado em {configuracao.banco}.")
    return 0


def demo(configuracao: Configuracao, senha: str) -> int:
    """Dados de demonstração para a apresentação. Só roda em banco sem usuários."""
    sistema = montar(configuracao).sistema
    if _existe_usuario(sistema):
        print("O banco já tem usuários. Use outro arquivo com --banco para a demonstração.", file=sys.stderr)
        return 1
    carregar_demo(sistema, senha)
    print(f"Dados de demonstração criados em {configuracao.banco}. Senha de todos os usuários: {senha}")
    for email, perfil in USUARIOS_DEMO:
        print(f"  {perfil:<20} {email}")
    return 0


USUARIOS_DEMO = [
    ("admin@remindme.local", "Administrador"),
    ("dona@remindme.local", "Dono"),
    ("operador@remindme.local", "Operador Financeiro"),
    ("contador@remindme.local", "Contador"),
]


def carregar_demo(sistema: Sistema, senha: str) -> None:
    sistema.acesso.instalar_administrador("Ana Administradora", USUARIOS_DEMO[0][0], senha)
    admin = sistema.acesso.entrar(USUARIOS_DEMO[0][0], senha).token
    sistema.acesso.cadastrar_usuario(admin, "Marta Dona", USUARIOS_DEMO[1][0], senha, "Dono")
    sistema.acesso.cadastrar_usuario(admin, "Diego Operador", USUARIOS_DEMO[2][0], senha, "Operador Financeiro")
    sistema.acesso.cadastrar_usuario(admin, "Carla Contadora", USUARIOS_DEMO[3][0], senha, "Contador")
    operador = sistema.acesso.entrar(USUARIOS_DEMO[2][0], senha).token
    dona = sistema.acesso.entrar(USUARIOS_DEMO[1][0], senha).token
    clientes = [
        ("Padaria Pão Quente Ltda.", "11.222.333/0001-81", "financeiro@paoquente.com.br", "(11) 3456-7890"),
        ("Studio Bella Forma", "45.723.174/0001-10", "contato@bellaforma.com.br", "(11) 98765-4321"),
        ("João Carlos Pereira", "529.982.247-25", "joao.pereira@email.com", "(21) 99876-5432"),
        ("Oficina Mecânica Torque", "04.252.011/0001-10", "torque@oficina.com.br", "(31) 3322-1100"),
    ]
    ids = [
        sistema.cadastrar_cliente(operador, nome=n, documento=d, email=m, telefone=t).id for n, d, m, t in clientes
    ]
    hoje = sistema.hoje()
    titulos = [
        (ids[0], "1850.00", -20, "Boleto 30 dias"),
        (ids[0], "920.50", 2, "PIX"),
        (ids[1], "3200.00", 12, "Transferência"),
        (ids[1], "450.00", -5, "PIX"),
        (ids[2], "780.00", 25, "Cartão"),
        (ids[3], "5400.00", 4, "Boleto 28 dias"),
        (ids[3], "1200.00", -40, "Boleto"),
    ]
    criados = [
        sistema.cadastrar_titulo(operador, c, Decimal(v), hoje + timedelta(days=d), cond) for c, v, d, cond in titulos
    ]
    sistema.registrar_pagamento(operador, criados[0].id, Decimal("850.00"), hoje - timedelta(days=3))
    sistema.registrar_pagamento(operador, criados[6].id, Decimal("1200.00"), hoje - timedelta(days=35))
    sistema.registrar_pagamento(operador, criados[2].id, Decimal("1000.00"), hoje)
    sistema.verificar_vencimentos_automaticamente()
    sistema.cancelar_titulo(dona, criados[3].id, "Serviço não prestado; acordo com o cliente.")


def _existe_usuario(sistema: Sistema) -> bool:
    return sistema.ha_usuarios()


def main(argumentos=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    padrao = Configuracao()
    analisador = argparse.ArgumentParser(prog="remindme", description="RemindMe — gestão de recebíveis.")
    analisador.add_argument("--banco", default=padrao.banco, help=f"arquivo SQLite (padrão: {padrao.banco})")
    comandos = analisador.add_subparsers(dest="comando")
    p_servir = comandos.add_parser("servir", help="inicia o servidor web (padrão)")
    p_servir.add_argument("--host", default=padrao.host, help="use 0.0.0.0 para aceitar conexões externas")
    p_servir.add_argument("--porta", type=int, default=padrao.porta)
    p_servir.add_argument("--https", action="store_true", help="marca os cookies como Secure (atrás de HTTPS)")
    p_servir.add_argument("--antecedencia-dias", type=int, default=padrao.antecedencia_dias,
                          help="dias para sinalizar título próximo do vencimento (RF-23, OPEN-21)")
    p_servir.add_argument("--intervalo-agendador", type=int, default=padrao.intervalo_agendador_minutos,
                          help="minutos entre verificações automáticas de vencimento")
    p_admin = comandos.add_parser("criar-admin", help="cria o primeiro Administrador")
    p_admin.add_argument("--nome", default="Administrador")
    p_admin.add_argument("--email", required=True)
    p_demo = comandos.add_parser("demo", help="cria usuários, clientes e títulos de demonstração")
    p_demo.add_argument("--senha", help="senha dos usuários de demonstração (padrão: gerada)")
    args = analisador.parse_args(argumentos)

    configuracao = Configuracao(
        banco=args.banco,
        host=getattr(args, "host", padrao.host),
        porta=getattr(args, "porta", padrao.porta),
        https=getattr(args, "https", False),
        antecedencia_dias=getattr(args, "antecedencia_dias", padrao.antecedencia_dias),
        intervalo_agendador_minutos=getattr(args, "intervalo_agendador", padrao.intervalo_agendador_minutos),
    )
    if args.comando == "criar-admin":
        return criar_admin(configuracao, args.nome, args.email)
    if args.comando == "demo":
        return demo(configuracao, args.senha or secrets.token_urlsafe(9))
    servir(configuracao)
    return 0
