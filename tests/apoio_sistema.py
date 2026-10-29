"""Montagem do `Sistema` sobre SQLite em memória, para os testes das Specs 002 e 003 e da interface web."""

from datetime import datetime

from remindme.aplicacao.sistema import Sistema
from remindme.infraestrutura.memoria import RelogioFixo
from remindme.infraestrutura.sqlite import BancoSQLite, UnidadeDeTrabalhoSQLite

AGORA = datetime(2026, 10, 20, 10, 0)
SENHA = "senha-forte-1"
CNPJ = "11.222.333/0001-81"
CPF = "529.982.247-25"


def novo_sistema():
    banco = BancoSQLite(":memory:")
    uow = UnidadeDeTrabalhoSQLite(banco)
    sistema = Sistema(uow, RelogioFixo(AGORA))
    return sistema, uow, banco


def com_usuarios(sistema):
    """Administrador, Dono, Operador Financeiro e Contador; devolve os tokens de sessão."""
    sistema.acesso.instalar_administrador("Admin", "admin@exemplo.com", SENHA)
    admin = sistema.acesso.entrar("admin@exemplo.com", SENHA).token
    for nome, email, perfil in (
        ("Dona", "dona@exemplo.com", "Dono"),
        ("Diego", "diego@exemplo.com", "Operador Financeiro"),
        ("Carla", "carla@exemplo.com", "Contador"),
    ):
        sistema.acesso.cadastrar_usuario(admin, nome, email, SENHA, perfil)
    return {
        "admin": admin,
        "dono": sistema.acesso.entrar("dona@exemplo.com", SENHA).token,
        "operador": sistema.acesso.entrar("diego@exemplo.com", SENHA).token,
        "contador": sistema.acesso.entrar("carla@exemplo.com", SENHA).token,
    }
